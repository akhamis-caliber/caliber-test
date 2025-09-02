#!/usr/bin/env python3
"""
Script to create demo user for Caliber application
This addresses the sign-in bug where demo@caliber.com user doesn't exist in database
"""

import asyncio
import sys
import os
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

# Add the backend directory to Python path so we can import models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from db.models import User, Organization, Membership, UserRole


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


async def create_demo_user():
    """Create demo user in database"""
    print("🚀 Creating demo user for Caliber application...")
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/caliber')
    print(f"📡 Connecting to MongoDB: {mongo_url}")
    
    client = AsyncIOMotorClient(mongo_url)
    database = client.get_database()
    
    # Initialize Beanie with models
    await init_beanie(database=database, document_models=[
        User, Organization, Membership
    ])
    print("✅ MongoDB connection initialized")
    
    # Check if demo user already exists
    demo_email = "demo@caliber.com"
    existing_user = await User.find_one(User.email == demo_email)
    
    if existing_user:
        print(f"⚠️  Demo user {demo_email} already exists!")
        print(f"   User ID: {existing_user.id}")
        print(f"   Name: {existing_user.name}")
        
        # Get their organizations
        memberships = await Membership.find(Membership.user_id == existing_user.id).to_list()
        print(f"   Organizations: {len(memberships)}")
        
        for membership in memberships:
            org = await Organization.get(membership.org_id)
            if org:
                print(f"   - {org.name} ({membership.role})")
        
        return existing_user
    
    # Create demo user
    print(f"👤 Creating demo user: {demo_email}")
    demo_password = "password"
    password_hash = hash_password(demo_password)
    
    demo_user = User(
        name="Demo User",
        email=demo_email,
        password_hash=password_hash
    )
    await demo_user.insert()
    print(f"✅ Demo user created with ID: {demo_user.id}")
    
    # Create demo organization
    print("🏢 Creating demo organization...")
    demo_org = Organization(name="Demo Organization")
    await demo_org.insert()
    print(f"✅ Demo organization created with ID: {demo_org.id}")
    
    # Create membership linking user to organization
    print("🔗 Creating membership...")
    membership = Membership(
        user_id=demo_user.id,
        org_id=demo_org.id,
        role=UserRole.ADMIN
    )
    await membership.insert()
    print(f"✅ Membership created - Demo user is Admin of Demo Organization")
    
    print("\n🎉 Demo user setup completed successfully!")
    print(f"   Email: {demo_email}")
    print(f"   Password: {demo_password}")
    print(f"   Organization: {demo_org.name}")
    print(f"   Role: Admin")
    print("\n✅ You can now sign in to the Caliber application using these credentials!")
    
    return demo_user


async def main():
    """Main function"""
    try:
        await create_demo_user()
    except Exception as e:
        print(f"❌ Error creating demo user: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())