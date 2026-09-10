"""
FloodWatch AI — FastAPI Backend Application
SIH26085 — AI-Powered Urban Flood Susceptibility and Safe Mobility System (Greater Chennai Corporation)
"""

import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.core.config import settings
from backend.app.api.api_router import api_router
from backend.app.services.flood_service import FloodService
from backend.app.db.session import SessionLocal
from backend.app.db.init_db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database tables and development seed accounts
    print("[STARTUP] Initializing Database tables and RBAC seeds...")
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()

    # Warm up model and preload grid forecasts
    print("[STARTUP] Initializing FloodWatch AI Nowcasting and Safe Routing Engine...")
    FloodService.get_instance()
    print("[READY] All Chennai GIS spatial features, XGBoost model, and RBAC auth ready for requests.")
    yield
    print("[SHUTDOWN] FloodWatch AI service stopping.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="High-resolution AI-powered urban flood susceptibility and risk-aware safe routing engine for Greater Chennai.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "challenge_code": settings.SIH_PROJECT_CODE,
        "study_area": settings.STUDY_AREA,
        "version": "2.0.0 (Phase 2)",
        "model_version": settings.MODEL_VERSION,
        "api_docs": "/docs",
        "api_v1": settings.API_V1_STR,
        "status": "ONLINE"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
