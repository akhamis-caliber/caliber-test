#!/usr/bin/env python3
"""
Test script to verify Redis configuration
"""

import sys
import os

# Add backend to path
sys.path.append('backend')

try:
    from config.redis import redis_client, get_redis
    from config.settings import settings
    
    print("✅ Redis configuration loaded successfully!")
    print(f"Redis URL: {settings.REDIS_URL}")
    print(f"Redis client: {redis_client}")
    
    # Test Redis connection
    try:
        redis_client.ping()
        print("✅ Redis connection successful!")
        
        # Test basic operations
        redis_client.set("test_key", "test_value")
        value = redis_client.get("test_key")
        print(f"✅ Redis read/write test successful: {value}")
        
        # Clean up test data
        redis_client.delete("test_key")
        print("✅ Redis cleanup successful!")
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}") 