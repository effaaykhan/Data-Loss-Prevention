"""
Dashboard API Endpoints
Real-time statistics and metrics for dashboard
Returns actual data from database (populated by agents)
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
import structlog

from app.core.security import get_current_user
from app.core.database import get_mongodb

logger = structlog.get_logger()
router = APIRouter()


@router.get("/overview")
async def get_dashboard_overview(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get dashboard overview statistics
    Returns real data from database populated by agents
    """
    db = get_mongodb()

    # Query agents from MongoDB
    agents_collection = db["agents"]
    
    # Total agents
    total_agents = await agents_collection.count_documents({})
    
    # Active agents (status = "online")
    active_agents = await agents_collection.count_documents({"status": "online"})

    # Query events from MongoDB (using correct collection name)
    events_collection = db.dlp_events

    # Total events (all time)
    total_events = await events_collection.count_documents({})

    # Critical alerts/events
    critical_alerts = await events_collection.count_documents({"severity": "critical"})

    # Blocked events
    blocked_events = await events_collection.count_documents({"blocked": True})

    return {
        "total_agents": total_agents,
        "active_agents": active_agents,
        "total_events": total_events,
        "critical_alerts": critical_alerts,
        "blocked_events": blocked_events,
    }


@router.get("/timeline")
async def get_event_timeline(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to retrieve"),
    current_user: dict = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """
    Get event timeline data for charts
    Returns actual event counts grouped by hour
    """
    db = get_mongodb()
    events_collection = db.dlp_events

    now = datetime.utcnow()
    start_time = now - timedelta(hours=hours)

    # Aggregate events by hour
    pipeline = [
        {"$match": {"timestamp": {"$gte": start_time}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%dT%H:00:00Z",
                        "date": "$timestamp"
                    }
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}}
    ]

    cursor = events_collection.aggregate(pipeline)
    timeline_data = []

    async for item in cursor:
        timeline_data.append({
            "timestamp": item["_id"],
            "count": item["count"],
        })

    return timeline_data


@router.get("/stats/agents")
async def get_agents_stats(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get agent statistics
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    total = await agents_collection.count_documents({})
    online = await agents_collection.count_documents({"status": "online"})
    offline = await agents_collection.count_documents({"status": "offline"})
    warning = await agents_collection.count_documents({"status": "warning"})

    return {
        "total": total,
        "online": online,
        "offline": offline,
        "warning": warning,
    }


@router.get("/stats/classification")
async def get_classification_stats(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get data classification statistics
    """
    db = get_mongodb()
    files_collection = db["classified_files"]

    total = await files_collection.count_documents({})
    public = await files_collection.count_documents({"classification": "public"})
    internal = await files_collection.count_documents({"classification": "internal"})
    confidential = await files_collection.count_documents({"classification": "confidential"})
    restricted = await files_collection.count_documents({"classification": "restricted"})

    return {
        "total": total,
        "public": public,
        "internal": internal,
        "confidential": confidential,
        "restricted": restricted,
    }
