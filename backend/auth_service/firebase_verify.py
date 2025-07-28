"""
Firebase token verification for Google OAuth authentication.
"""

import firebase_admin
from firebase_admin import credentials, auth
from typing import Optional, Dict, Any
import json
import os
from config.settings import get_firebase_credentials


class FirebaseAuth:
    """Firebase authentication service"""
    
    _app = None
    
    @classmethod
    def initialize_firebase(cls):
        """Initialize Firebase Admin SDK"""
        if cls._app is None:
            try:
                # Get Firebase credentials from settings
                firebase_creds = get_firebase_credentials()
                
                # Check if credentials are properly configured
                if not firebase_creds.get('project_id') or firebase_creds.get('project_id') == 'your-firebase-project-id':
                    print("⚠️ Firebase credentials not properly configured - Firebase authentication disabled")
                    cls._app = None
                    return False
                
                # Check if private key is available
                if not firebase_creds.get('private_key'):
                    print("⚠️ Firebase private key not configured - Firebase authentication disabled")
                    cls._app = None
                    return False
                
                # Initialize Firebase Admin SDK
                cred = credentials.Certificate(firebase_creds)
                cls._app = firebase_admin.initialize_app(cred)
                
                print("✅ Firebase Admin SDK initialized successfully")
                return True
                
            except Exception as e:
                print(f"❌ Failed to initialize Firebase Admin SDK: {e}")
                cls._app = None
                return False
    
    @classmethod
    def verify_id_token(cls, id_token: str) -> Optional[Dict[str, Any]]:
        """Verify Firebase ID token and return user info"""
        try:
            if cls._app is None:
                if not cls.initialize_firebase():
                    print("❌ Firebase not available - cannot verify token")
                    return None
            
            # Verify the ID token
            decoded_token = auth.verify_id_token(id_token)
            
            # Extract user information
            user_info = {
                'uid': decoded_token.get('uid'),
                'email': decoded_token.get('email'),
                'email_verified': decoded_token.get('email_verified', False),
                'name': decoded_token.get('name'),
                'picture': decoded_token.get('picture'),
                'provider_id': decoded_token.get('firebase', {}).get('sign_in_provider'),
                'issuer': decoded_token.get('iss'),
                'audience': decoded_token.get('aud'),
                'issued_at': decoded_token.get('iat'),
                'expires_at': decoded_token.get('exp')
            }
            
            return user_info
            
        except auth.ExpiredIdTokenError:
            print("❌ Firebase ID token has expired")
            return None
        except auth.RevokedIdTokenError:
            print("❌ Firebase ID token has been revoked")
            return None
        except auth.InvalidIdTokenError:
            print("❌ Firebase ID token is invalid")
            return None
        except Exception as e:
            print(f"❌ Error verifying Firebase ID token: {e}")
            return None
    
    @classmethod
    def verify_custom_token(cls, custom_token: str) -> Optional[Dict[str, Any]]:
        """Verify Firebase custom token"""
        try:
            if cls._app is None:
                if not cls.initialize_firebase():
                    print("❌ Firebase not available - cannot verify custom token")
                    return None
            
            # Verify the custom token
            decoded_token = auth.verify_id_token(custom_token)
            return decoded_token
            
        except Exception as e:
            print(f"❌ Error verifying Firebase custom token: {e}")
            return None
    
    @classmethod
    def get_user_by_uid(cls, uid: str) -> Optional[Dict[str, Any]]:
        """Get Firebase user by UID"""
        try:
            if cls._app is None:
                if not cls.initialize_firebase():
                    print("❌ Firebase not available - cannot get user")
                    return None
            
            # Get user record from Firebase
            user_record = auth.get_user(uid)
            
            user_info = {
                'uid': user_record.uid,
                'email': user_record.email,
                'email_verified': user_record.email_verified,
                'display_name': user_record.display_name,
                'photo_url': user_record.photo_url,
                'phone_number': user_record.phone_number,
                'disabled': user_record.disabled,
                'provider_data': [
                    {
                        'uid': provider.uid,
                        'display_name': provider.display_name,
                        'email': provider.email,
                        'photo_url': provider.photo_url,
                        'provider_id': provider.provider_id
                    }
                    for provider in user_record.provider_data
                ],
                'custom_claims': user_record.custom_claims,
                'created_at': user_record.user_metadata.creation_timestamp,
                'last_sign_in': user_record.user_metadata.last_sign_in_timestamp
            }
            
            return user_info
            
        except auth.UserNotFoundError:
            print(f"❌ Firebase user not found: {uid}")
            return None
        except Exception as e:
            print(f"❌ Error getting Firebase user: {e}")
            return None
    
    @classmethod
    def create_custom_token(cls, uid: str, additional_claims: Dict[str, Any] = None) -> Optional[str]:
        """Create a custom Firebase token"""
        try:
            if cls._app is None:
                if not cls.initialize_firebase():
                    print("❌ Firebase not available - cannot create custom token")
                    return None
            
            # Create custom token
            custom_token = auth.create_custom_token(uid, additional_claims)
            return custom_token.decode('utf-8')
            
        except Exception as e:
            print(f"❌ Error creating Firebase custom token: {e}")
            return None
    
    @classmethod
    def set_custom_user_claims(cls, uid: str, claims: Dict[str, Any]) -> bool:
        """Set custom claims for a Firebase user"""
        try:
            if cls._app is None:
                if not cls.initialize_firebase():
                    print("❌ Firebase not available - cannot set custom claims")
                    return False
            
            # Set custom claims
            auth.set_custom_user_claims(uid, claims)
            return True
            
        except Exception as e:
            print(f"❌ Error setting Firebase custom claims: {e}")
            return False
    
    @classmethod
    def delete_user(cls, uid: str) -> bool:
        """Delete a Firebase user"""
        try:
            if cls._app is None:
                if not cls.initialize_firebase():
                    print("❌ Firebase not available - cannot delete user")
                    return False
            
            # Delete user
            auth.delete_user(uid)
            return True
            
        except Exception as e:
            print(f"❌ Error deleting Firebase user: {e}")
            return False


def verify_google_token(id_token: str) -> Optional[Dict[str, Any]]:
    """Verify Google OAuth token using Firebase"""
    return FirebaseAuth.verify_id_token(id_token)


def get_firebase_user_info(uid: str) -> Optional[Dict[str, Any]]:
    """Get Firebase user information by UID"""
    return FirebaseAuth.get_user_by_uid(uid)


def create_firebase_token(uid: str, claims: Dict[str, Any] = None) -> Optional[str]:
    """Create a Firebase custom token"""
    return FirebaseAuth.create_custom_token(uid, claims)


def set_user_claims(uid: str, claims: Dict[str, Any]) -> bool:
    """Set custom claims for a Firebase user"""
    return FirebaseAuth.set_custom_user_claims(uid, claims)


def delete_firebase_user(uid: str) -> bool:
    """Delete a Firebase user"""
    return FirebaseAuth.delete_user(uid) 