from fastapi import APIRouter
from backend.app.api.routes import (
    flood,
    routing,
    alerts,
    analytics,
    health,
    auth,
    otp,
    locations,
    citizen_alerts,
    feedback,
    government,
    admin_users,
    rainfall,
    drainage,
    simulation,
    emergency,
    dno
)

api_router = APIRouter()

# Rainfall & Drainage Telemetry
api_router.include_router(rainfall.router)
api_router.include_router(drainage.router)

# Model Simulation & Emergency Infrastructure
api_router.include_router(simulation.router)
api_router.include_router(emergency.router)

# Authentication & OTP
api_router.include_router(auth.router)
api_router.include_router(otp.router)

# Location & Consent
api_router.include_router(locations.router)

# Targeted Citizen Alerts & General Alerts
api_router.include_router(citizen_alerts.router)
api_router.include_router(alerts.router, tags=["Disaster Alerts"])

# Citizen Feedback & Ground Truth
api_router.include_router(feedback.router)

# Government Authority Operations
api_router.include_router(government.router)

# Administrator & System Governance
api_router.include_router(admin_users.router)

# Core Flood Nowcasting & Safe Mobility
api_router.include_router(flood.router, tags=["Flood Nowcasting & Risk"])
api_router.include_router(routing.router, tags=["Safe Mobility & Routing"])
api_router.include_router(analytics.router, tags=["Flood Analytics"])
api_router.include_router(health.router, tags=["System Health & Admin MLOps"])
api_router.include_router(dno.router)
