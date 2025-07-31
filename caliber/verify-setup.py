#!/usr/bin/env python3
"""
Caliber Backend Setup Verification Script
This script verifies that all components are properly configured and working.
"""

import requests
import subprocess
import sys
import time
from pathlib import Path

def print_status(message, status="INFO"):
    """Print a formatted status message."""
    emoji = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARNING": "⚠️",
        "CHECKING": "🔍"
    }
    print(f"{emoji.get(status, 'ℹ️')} {message}")

def check_docker():
    """Check if Docker is running."""
    print_status("Checking Docker...", "CHECKING")
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, text=True)
        if result.returncode == 0:
            print_status("Docker is running", "SUCCESS")
            return True
        else:
            print_status("Docker is not running", "ERROR")
            return False
    except FileNotFoundError:
        print_status("Docker is not installed", "ERROR")
        return False

def check_docker_compose():
    """Check if Docker Compose is available."""
    print_status("Checking Docker Compose...", "CHECKING")
    try:
        result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_status("Docker Compose is available", "SUCCESS")
            return True
        else:
            print_status("Docker Compose is not available", "ERROR")
            return False
    except FileNotFoundError:
        print_status("Docker Compose is not installed", "ERROR")
        return False

def check_services():
    """Check if Docker services are running."""
    print_status("Checking Docker services...", "CHECKING")
    try:
        result = subprocess.run(["docker-compose", "ps"], capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout
            if "caliber-backend-1" in output and "Up" in output:
                print_status("Backend service is running", "SUCCESS")
            else:
                print_status("Backend service is not running", "WARNING")
            
            if "caliber-postgres-1" in output and "Up" in output:
                print_status("PostgreSQL service is running", "SUCCESS")
            else:
                print_status("PostgreSQL service is not running", "WARNING")
            
            if "caliber-redis-1" in output and "Up" in output:
                print_status("Redis service is running", "SUCCESS")
            else:
                print_status("Redis service is not running", "WARNING")
            
            return True
        else:
            print_status("Failed to check Docker services", "ERROR")
            return False
    except Exception as e:
        print_status(f"Error checking services: {e}", "ERROR")
        return False

def check_api():
    """Check if the API is responding."""
    print_status("Checking API health...", "CHECKING")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print_status("API is healthy", "SUCCESS")
                return True
            else:
                print_status("API is not healthy", "WARNING")
                return False
        else:
            print_status(f"API returned status code: {response.status_code}", "ERROR")
            return False
    except requests.exceptions.ConnectionError:
        print_status("Cannot connect to API", "ERROR")
        return False
    except requests.exceptions.Timeout:
        print_status("API request timed out", "ERROR")
        return False
    except Exception as e:
        print_status(f"Error checking API: {e}", "ERROR")
        return False

def check_api_docs():
    """Check if API documentation is accessible."""
    print_status("Checking API documentation...", "CHECKING")
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print_status("API documentation is accessible", "SUCCESS")
            return True
        else:
            print_status(f"API docs returned status code: {response.status_code}", "WARNING")
            return False
    except requests.exceptions.ConnectionError:
        print_status("Cannot connect to API documentation", "WARNING")
        return False
    except Exception as e:
        print_status(f"Error checking API docs: {e}", "WARNING")
        return False

def check_file_structure():
    """Check if required files and directories exist."""
    print_status("Checking file structure...", "CHECKING")
    
    required_files = [
        "docker-compose.yml",
        "backend/main.py",
        "backend/requirements.txt",
        "backend/config/settings.py",
        "backend/auth_service/firebase_verify.py",
        "backend/scoring_service/schemas.py",
        "backend/ai_service/schemas.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print_status(f"Missing files: {', '.join(missing_files)}", "WARNING")
        return False
    else:
        print_status("All required files exist", "SUCCESS")
        return True

def main():
    """Main verification function."""
    print("🚀 Caliber Backend Setup Verification")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("docker-compose.yml").exists():
        print_status("Please run this script from the caliber directory", "ERROR")
        sys.exit(1)
    
    checks = [
        ("Docker", check_docker),
        ("Docker Compose", check_docker_compose),
        ("File Structure", check_file_structure),
        ("Docker Services", check_services),
        ("API Health", check_api),
        ("API Documentation", check_api_docs)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n--- {name} Check ---")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_status(f"Check failed with error: {e}", "ERROR")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Verification Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print_status("🎉 All checks passed! Your development environment is ready.", "SUCCESS")
        print("\n📚 Next Steps:")
        print("1. Visit http://localhost:8000/docs to explore the API")
        print("2. Use the dev-setup scripts for common tasks:")
        print("   - Linux/Mac: ./dev-setup.sh status")
        print("   - Windows: dev-setup.bat status")
        print("3. Check DEVELOPMENT_STATE.md for detailed information")
    else:
        print_status("⚠️ Some checks failed. Please review the issues above.", "WARNING")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure Docker Desktop is running")
        print("2. Run 'docker-compose up -d' to start services")
        print("3. Check logs with 'docker-compose logs backend'")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 