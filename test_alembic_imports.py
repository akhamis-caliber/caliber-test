#!/usr/bin/env python3
"""
Test script to verify Alembic imports work correctly
"""

import sys
import os

# Add the backend directory to the path
sys.path.append('backend')

try:
    from config.settings import settings
    print("✅ Successfully imported settings")
    print(f"Database URL: {settings.DATABASE_URL}")
except ImportError as e:
    print(f"❌ Failed to import settings: {e}")

try:
    from db.base import Base
    print("✅ Successfully imported Base")
except ImportError as e:
    print(f"❌ Failed to import Base: {e}")

try:
    from db.models import Organization, User, CampaignTemplate, Campaign, ScoringResult, AIInsight
    print("✅ Successfully imported all models")
except ImportError as e:
    print(f"❌ Failed to import models: {e}")

print(f"Python path: {sys.path}") 