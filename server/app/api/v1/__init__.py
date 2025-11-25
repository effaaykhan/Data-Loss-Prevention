"""
API v1 Router
Main API router aggregating all endpoints
"""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    events,
    policies,
    users,
    dashboard,
    alerts,
    agents,
    classification,
    analytics,
    export,
    siem,
    google_drive,
)

api_router = APIRouter()

# Health check endpoint (no authentication required)
@api_router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and agent connectivity tests
    """
    return {"status": "healthy", "service": "cybersentinel-dlp"}

# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(events.router, prefix="/events", tags=["Events"])
api_router.include_router(classification.router, prefix="/classification", tags=["Classification"])
api_router.include_router(policies.router, prefix="/policies", tags=["Policies"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(export.router, prefix="/export", tags=["Export"])
api_router.include_router(siem.router, prefix="/siem", tags=["SIEM"])
api_router.include_router(google_drive.router, tags=["Google Drive"])
