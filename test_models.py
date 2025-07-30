#!/usr/bin/env python3
"""
Test script to verify all database models
"""

import sys
sys.path.append('backend')

try:
    from db.models import Organization, User, CampaignTemplate, Campaign, ScoringResult, AIInsight
    from config.database import engine
    
    print("✅ All models loaded successfully!")
    print()
    
    # Test each model
    models = [
        ("Organization", Organization),
        ("User", User),
        ("CampaignTemplate", CampaignTemplate),
        ("Campaign", Campaign),
        ("ScoringResult", ScoringResult),
        ("AIInsight", AIInsight)
    ]
    
    for name, model in models:
        print(f"📋 {name}:")
        print(f"  Table: {model.__tablename__}")
        print(f"  Columns: {[col.name for col in model.__table__.columns]}")
        print(f"  Has UUID id: {'id' in [col.name for col in model.__table__.columns]}")
        print(f"  Has timestamps: {'created_at' in [col.name for col in model.__table__.columns] and 'updated_at' in [col.name for col in model.__table__.columns]}")
        print()
    
    # Test creating tables
    try:
        from db.base import Base
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