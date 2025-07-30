import firebase_admin
from firebase_admin import credentials, auth
from config.settings import settings
from common.exceptions import AuthenticationError
import logging

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
try:
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
    logger.info("Firebase Admin SDK initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firebase Admin SDK: {e}")

async def verify_firebase_token(token: str) -> dict:
    """
    Verify Firebase ID token and return user data
    """
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
            
        decoded_token = auth.verify_id_token(token)
        return {
            'uid': decoded_token['uid'],
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name', ''),
            'email_verified': decoded_token.get('email_verified', False)
        }
    except auth.InvalidIdTokenError:
        raise AuthenticationError("Invalid Firebase token")
    except auth.ExpiredIdTokenError:
        raise AuthenticationError("Expired Firebase token")
    except Exception as e:
        logger.error(f"Firebase token verification failed: {e}")
        raise AuthenticationError("Token verification failed")
