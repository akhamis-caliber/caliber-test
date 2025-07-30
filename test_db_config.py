#!/usr/bin/env python3
"""
Test script to verify database configuration
"""

import sys
import os

# Add backend to path
sys.path.append('backend')

try:
    from config.database import engine, get_db, Base
    from config.settings import settings
    
    print("✅ Database configuration loaded successfully!")
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Engine: {engine}")
    print(f"Base: {Base}")
    
    # Test database connection
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Database connection successful!")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}") 