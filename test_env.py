#!/usr/bin/env python3
"""
Test script to verify environment variables are loaded correctly
"""

from dotenv import load_dotenv
import os

def test_environment_variables():
    """Test that all environment variables are loaded correctly"""
    
    # Load environment variables
    load_dotenv()
    
    print("=== Environment Variables Test ===")
    print()
    
    # Test database configuration
    print("🗄️ Database Configuration:")
    database_url = os.getenv("DATABASE_URL")
    print(f"  DATABASE_URL: {database_url}")
    if database_url and "caliber_dev" in database_url:
        print("  ✅ Database URL looks correct")
    else:
        print("  ❌ Database URL may need updating")
    print()
    
    # Test Redis configuration
    print("🔴 Redis Configuration:")
    redis_url = os.getenv("REDIS_URL")
    print(f"  REDIS_URL: {redis_url}")
    if redis_url and "localhost:6379" in redis_url:
        print("  ✅ Redis URL looks correct")
    else:
        print("  ❌ Redis URL may need updating")
    print()
    
    # Test environment settings
    print("⚙️ Environment Settings:")
    environment = os.getenv("ENVIRONMENT")
    secret_key = os.getenv("SECRET_KEY")
    print(f"  ENVIRONMENT: {environment}")
    print(f"  SECRET_KEY: {secret_key[:10] if secret_key and len(secret_key) > 10 else 'Not set or too short'}...")
    if environment == "development":
        print("  ✅ Environment set to development")
    else:
        print("  ⚠️ Environment may need updating")
    if secret_key and len(secret_key) > 20:
        print("  ✅ Secret key looks secure")
    else:
        print("  ❌ Secret key may need updating")
    print()
    
    # Test Firebase configuration
    print("🔥 Firebase Configuration:")
    firebase_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    print(f"  FIREBASE_CREDENTIALS_PATH: {firebase_path}")
    if firebase_path:
        print("  ✅ Firebase credentials path set")
    else:
        print("  ❌ Firebase credentials path not set")
    print()
    
    # Test OpenAI configuration
    print("🤖 OpenAI Configuration:")
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print(f"  OPENAI_API_KEY: {openai_key[:10]}...")
        if not openai_key.startswith("your_"):
            print("  ✅ OpenAI API key looks like a real key")
        else:
            print("  ❌ OpenAI API key still has placeholder value")
    else:
        print("  ❌ OpenAI API key not set")
    print()
    
    # Test AWS configuration
    print("☁️ AWS Configuration:")
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_bucket = os.getenv("AWS_BUCKET_NAME")
    print(f"  AWS_ACCESS_KEY_ID: {aws_access_key[:10] if aws_access_key else 'Not set'}...")
    print(f"  AWS_SECRET_ACCESS_KEY: {aws_secret_key[:10] if aws_secret_key else 'Not set'}...")
    print(f"  AWS_BUCKET_NAME: {aws_bucket}")
    if aws_access_key and not aws_access_key.startswith("your_"):
        print("  ✅ AWS credentials look like real keys")
    else:
        print("  ⚠️ AWS credentials may need updating (optional)")
    print()
    
    print("=== Test Complete ===")

if __name__ == "__main__":
    test_environment_variables() 