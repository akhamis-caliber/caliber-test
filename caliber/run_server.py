#!/usr/bin/env python3
"""
Startup script for Caliber FastAPI server
"""

import uvicorn
import sys
import os

# Add backend to Python path
sys.path.append('backend')

if __name__ == "__main__":
    print("🚀 Starting Caliber API Server...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Alternative Docs: http://localhost:8000/redoc")
    print("🏥 Health Check: http://localhost:8000/health")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 