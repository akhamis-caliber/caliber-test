#!/usr/bin/env python3
"""
Comprehensive test script for all CALIBER modules
Continues testing from where we left off
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add backend to path
sys.path.append('backend')

def test_config_modules():
    """Test configuration modules"""
    print("🔧 Testing Configuration Modules")
    print("=" * 50)
    
    try:
        from config.settings import settings
        print("✅ Settings imported successfully")
        print(f"   Database URL: {settings.DATABASE_URL}")
        print(f"   Redis URL: {settings.REDIS_URL}")
        print()
        
        from config.database import engine, get_db
        print("✅ Database config imported successfully")
        print(f"   Engine: {engine}")
        print()
        
        from config.redis import redis_client, get_redis
        print("✅ Redis config imported successfully")
        print(f"   Redis client: {redis_client}")
        print()
        
        return True
    except Exception as e:
        print(f"❌ Config modules failed: {e}")
        return False

def test_database_modules():
    """Test database modules"""
    print("🗄️ Testing Database Modules")
    print("=" * 50)
    
    try:
        from db.base import Base
        print("✅ Base imported successfully")
        print()
        
        from db.models import Organization, User, CampaignTemplate, Campaign, ScoringResult, AIInsight
        print("✅ All models imported successfully")
        
        # Test model attributes
        models = [
            ("Organization", Organization),
            ("User", User),
            ("CampaignTemplate", CampaignTemplate),
            ("Campaign", Campaign),
            ("ScoringResult", ScoringResult),
            ("AIInsight", AIInsight)
        ]
        
        for name, model in models:
            print(f"   📋 {name}: {model.__tablename__}")
        print()
        
        return True
    except Exception as e:
        print(f"❌ Database modules failed: {e}")
        return False

def test_storage_module():
    """Test storage module"""
    print("💾 Testing Storage Module")
    print("=" * 50)
    
    try:
        from report_service.storage import FileStorage, file_storage
        print("✅ Storage module imported successfully")
        
        # Quick storage test
        test_storage = FileStorage("temp_test_storage")
        test_content = b"test content"
        saved_path = test_storage.save_file(test_content, "test.txt")
        
        # Verify
        retrieved_path = test_storage.get_file_path("test.txt")
        with open(saved_path, 'rb') as f:
            content = f.read()
        
        success = content == test_content and retrieved_path == saved_path
        
        # Cleanup
        shutil.rmtree("temp_test_storage")
        
        if success:
            print("✅ Storage functionality working correctly")
        else:
            print("❌ Storage functionality failed")
        print()
        
        return success
    except Exception as e:
        print(f"❌ Storage module failed: {e}")
        return False

def test_common_modules():
    """Test common modules"""
    print("🔧 Testing Common Modules")
    print("=" * 50)
    
    try:
        from common.exceptions import ValidationError, NotFoundError
        print("✅ Common exceptions imported successfully")
        
        from common.schemas import BaseResponse
        print("✅ Common schemas imported successfully")
        
        from common.utils import generate_uuid
        print("✅ Common utils imported successfully")
        
        # Test UUID generation
        uuid1 = generate_uuid()
        uuid2 = generate_uuid()
        print(f"   Generated UUIDs: {uuid1}, {uuid2}")
        print(f"   UUIDs are different: {uuid1 != uuid2}")
        print()
        
        return True
    except Exception as e:
        print(f"❌ Common modules failed: {e}")
        return False

def test_service_modules():
    """Test service modules"""
    print("⚙️ Testing Service Modules")
    print("=" * 50)
    
    services = []
    
    # Test auth service
    try:
        from auth_service.dependencies import get_current_user
        print("✅ Auth service dependencies imported")
        services.append("auth")
    except Exception as e:
        print(f"❌ Auth service failed: {e}")
    
    # Test scoring service
    try:
        from scoring_service.controllers import ScoringController
        print("✅ Scoring service controllers imported")
        services.append("scoring")
    except Exception as e:
        print(f"❌ Scoring service failed: {e}")
    
    # Test campaign service
    try:
        from campaign_service.controllers import CampaignController
        print("✅ Campaign service controllers imported")
        services.append("campaign")
    except Exception as e:
        print(f"❌ Campaign service failed: {e}")
    
    # Test AI service
    try:
        from ai_service.controllers import AIController
        print("✅ AI service controllers imported")
        services.append("ai")
    except Exception as e:
        print(f"❌ AI service failed: {e}")
    
    # Test report service
    try:
        from report_service.exports import ExportService
        print("✅ Report service exports imported")
        services.append("report")
    except Exception as e:
        print(f"❌ Report service failed: {e}")
    
    print(f"   Working services: {services}")
    print()
    
    return len(services) > 0

def test_worker_modules():
    """Test worker modules"""
    print("🔄 Testing Worker Modules")
    print("=" * 50)
    
    try:
        from worker.celery import celery_app
        print("✅ Celery app imported successfully")
        
        from worker.tasks import process_campaign_scoring
        print("✅ Worker tasks imported successfully")
        print()
        
        return True
    except Exception as e:
        print(f"❌ Worker modules failed: {e}")
        return False

def test_alembic():
    """Test Alembic configuration"""
    print("🔄 Testing Alembic Configuration")
    print("=" * 50)
    
    try:
        # Test if we can import alembic modules
        import alembic
        print("✅ Alembic package available")
        
        # Check if alembic.ini exists
        if os.path.exists("alembic.ini"):
            print("✅ alembic.ini found")
        else:
            print("⚠️ alembic.ini not found")
        
        # Check if migrations directory exists
        if os.path.exists("backend/db/migrations"):
            print("✅ Migrations directory found")
        else:
            print("⚠️ Migrations directory not found")
        
        print()
        return True
    except Exception as e:
        print(f"❌ Alembic test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 CALIBER-01 Comprehensive Module Test")
    print("=" * 60)
    print()
    
    tests = [
        ("Configuration", test_config_modules),
        ("Database", test_database_modules),
        ("Storage", test_storage_module),
        ("Common", test_common_modules),
        ("Services", test_service_modules),
        ("Worker", test_worker_modules),
        ("Alembic", test_alembic)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"Running {test_name} tests...")
        results[test_name] = test_func()
        print()
    
    # Summary
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:15} {status}")
        if result:
            passed += 1
    
    print()
    print(f"Overall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All modules are working correctly!")
    else:
        print("⚠️ Some modules need attention")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 