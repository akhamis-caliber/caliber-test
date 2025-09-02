"""
Database configuration for MongoDB using Beanie
"""

import motor.motor_asyncio
from beanie import init_beanie
from config.settings import settings
import logging

# Configure logging
logger = logging.getLogger(__name__)

# MongoDB client
client = None

async def init_database():
    """Initialize MongoDB database and collections"""
    global client
    
    try:
        # Create motor client
        client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URL)
        
        # Get database
        database = client.get_database()
        
        # Import models for registration
        from db.models import User, Organization, Membership, Campaign, CampaignTemplate, Report, ScoreRow
        
        # Initialize beanie with models
        await init_beanie(
            database=database,
            document_models=[
                User,
                Organization, 
                Membership,
                Campaign,
                CampaignTemplate,
                Report,
                ScoreRow
            ]
        )
        
        logger.info("MongoDB connection initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {e}")
        raise

async def get_database():
    """Get database instance"""
    if client is None:
        await init_database()
    return client.get_database()

async def close_database():
    """Close database connection"""
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")