#!/usr/bin/env python3
"""
Database initialization script for Caliber
Creates initial database schema and sample data
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

from db.base import Base
from db.models import User, Organization, Membership, Campaign, CampaignType, CampaignGoal, AnalysisLevel
from config.settings import settings

def create_database():
    """Create database tables"""
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    return engine

def create_sample_data(engine):
    """Create sample data for development"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create sample organization
        org = Organization(
            name="Demo Organization"
        )
        db.add(org)
        db.flush()
        
        # Create sample user
        user = User(
            email="demo@caliber.com",
            name="Demo User",
            firebase_uid="demo-user-123"
        )
        db.add(user)
        db.flush()
        
        # Create membership
        membership = Membership(
            user_id=user.id,
            org_id=org.id,
            role="Admin"
        )
        db.add(membership)
        
        # Create sample campaign
        campaign = Campaign(
            org_id=org.id,
            name="Demo Campaign - TradeDesk CTV",
            campaign_type=CampaignType.TRADEDESK,
            goal=CampaignGoal.AWARENESS,
            channel="CTV",
            ctr_sensitivity=True,
            analysis_level=AnalysisLevel.DOMAIN,
            created_by=user.id
        )
        db.add(campaign)
        
        db.commit()
        
        print("✅ Sample data created:")
        print(f"   Organization: {org.name} ({org.id})")
        print(f"   User: {user.name} ({user.email})")
        print(f"   Campaign: {campaign.name}")
        
    except Exception as e:
        print(f"❌ Failed to create sample data: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Main initialization function"""
    print("🚀 Initializing Caliber Database")
    print("=" * 40)
    
    try:
        # Create database tables
        engine = create_database()
        
        # Create sample data
        create_sample_data(engine)
        
        print("\n🎉 Database initialization completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())