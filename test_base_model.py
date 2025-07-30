#!/usr/bin/env python3
"""
Test script to verify base model functionality
"""

import sys
import os

# Add backend to path
sys.path.append('backend')

try:
    from db.base import Base, BaseModel
    from config.database import engine
    
    print("✅ Base model loaded successfully!")
    print(f"Base: {Base}")
    print(f"BaseModel: {BaseModel}")
    
    # Test that BaseModel is abstract
    print(f"BaseModel is abstract: {BaseModel.__abstract__}")
    
    # Test creating tables
    try:
        # This will create tables for all models that inherit from Base
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # Check what tables were created
        inspector = engine.dialect.inspector(engine)
        tables = inspector.get_table_names()
        print(f"Tables in database: {tables}")
        
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}") 