from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime

# Import settings
from config.settings import settings, validate_settings
from common.schemas import HealthCheck

# Import routers
from auth_service.routes import auth_router
from campaign_service.routes import campaign_router
from scoring_service.routes import scoring_router
from report_service.routes.reports import router as report_router
from ai_service.routes import router as ai_router

# Import dashboard router
from dashboard_service.routes import dashboard_router
from websocket_manager import websocket_endpoint, progress_tracker
from auth_service.middleware import get_current_user_optional

app = FastAPI(
    title="Caliber Scoring System API",
    description="API for campaign scoring and analytics",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Validate settings on startup
@app.on_event("startup")
async def startup_event():
    try:
        validate_settings()
        print(f"✅ {settings.APP_NAME} v{settings.APP_VERSION} starting up...")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        raise

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(campaign_router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(scoring_router, prefix="/api/scoring", tags=["Scoring"])
app.include_router(report_router, prefix="/api", tags=["Reports"])
app.include_router(ai_router, prefix="/api/ai", tags=["AI Services"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])

@app.get("/")
async def root():
    return {"message": "Caliber Scoring System API"}

@app.get("/health", response_model=HealthCheck)
async def health_check():
    return HealthCheck(
        status="healthy",
        service="caliber-api",
        timestamp=datetime.utcnow(),
        version=settings.APP_VERSION
    )

# WebSocket endpoints
@app.websocket("/ws/progress/{connection_id}")
async def websocket_progress(websocket: WebSocket, connection_id: str):
    """WebSocket endpoint for progress updates"""
    await websocket_endpoint(websocket, connection_id)

@app.websocket("/ws/user/{user_id}")
async def websocket_user(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for user-specific updates"""
    await websocket_endpoint(websocket, f"user_{user_id}", user_id)

@app.get("/api/progress/{task_id}")
async def get_progress(task_id: str):
    """Get current progress for a task"""
    progress = progress_tracker.get_progress(task_id)
    if progress:
        return progress
    else:
        return {"error": "Task not found"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 