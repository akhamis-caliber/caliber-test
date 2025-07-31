from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from common.logging import setup_logging
from auth_service.routes import router as auth_router
from campaign_service.routes import router as campaign_router
from scoring_service.routes import router as scoring_router
from report_service.routes import router as report_router
from ai_service.routes import router as ai_router

# Setup logging
setup_logging()

app = FastAPI(
    title="Caliber API",
    description="AI-Powered Inventory Scoring Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.caliber.ai"]
)

# Include routers
app.include_router(auth_router)
app.include_router(campaign_router)
app.include_router(scoring_router)
app.include_router(report_router)
app.include_router(ai_router)

@app.get("/")
async def root():
    return {"message": "Caliber API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

