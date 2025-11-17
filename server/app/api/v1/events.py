"""
DLP Events API Endpoints
Query, filter, and manage DLP events
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field
import structlog

from app.core.security import get_current_user
from app.core.database import get_mongodb

logger = structlog.get_logger()
router = APIRouter()


class EventCreate(BaseModel):
    """Event creation model for agents"""
    event_id: str = Field(..., description="Unique event ID")
    event_type: str = Field(..., description="Event type")
    severity: str = Field(..., description="Event severity")
    agent_id: str = Field(..., description="Agent ID that detected the event")
    source_type: str = Field(default="endpoint", description="Source type")
    file_path: Optional[str] = Field(None, description="File path if applicable")
    classification: Optional[Dict[str, Any]] = Field(None, description="Classification data")
    action: Optional[str] = Field(None, description="Action taken (logged, blocked, alerted, etc.)")
    destination: Optional[str] = Field(None, description="Destination path for transfers")
    blocked: Optional[bool] = Field(None, description="Whether action was blocked")
    event_subtype: Optional[str] = Field(None, description="Event subtype")
    description: Optional[str] = Field(None, description="Event description")
    user_email: Optional[str] = Field(None, description="User email")


class DLPEvent(BaseModel):
    id: str
    timestamp: datetime
    event_type: str
    source: str
    agent_id: str  # Agent ID that generated the event
    user_email: str
    classification_score: float
    classification_labels: List[str]
    policy_id: Optional[str]
    action_taken: str
    severity: str
    file_path: Optional[str]
    destination: Optional[str]
    blocked: bool


class EventsResponse(BaseModel):
    events: List[DLPEvent]
    total: int
    skip: int
    limit: int


class EventQueryParams(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    severity: Optional[List[str]] = None
    source: Optional[List[str]] = None
    user_email: Optional[str] = None
    blocked_only: bool = False


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventCreate,
) -> Dict[str, Any]:
    """
    Create a new DLP event (public endpoint - no auth required for agents)
    """
    db = get_mongodb()
    events_collection = db["dlp_events"]

    # Create event document
    event_doc = {
        "id": event.event_id,
        "timestamp": datetime.utcnow(),
        "event_type": event.event_type,
        "severity": event.severity,
        "agent_id": event.agent_id,
        "source": event.source_type,
        "source_type": event.source_type,
        "user_email": event.user_email or "agent@system",  # Use agent-provided email or default
        "classification_score": 0.0,
        "classification_labels": [],
        "policy_id": None,
        "action_taken": event.action or "logged",  # Use agent-provided action or default to "logged"
        "file_path": event.file_path,
        "destination": event.destination,  # Use agent-provided destination
        "blocked": event.blocked if event.blocked is not None else False,  # Use agent-provided blocked status
    }
    
    # Add optional fields if provided
    if event.event_subtype:
        event_doc["event_subtype"] = event.event_subtype
    if event.description:
        event_doc["description"] = event.description

    # Add classification data if provided
    if event.classification:
        event_doc["classification"] = event.classification

    # Insert into database
    await events_collection.insert_one(event_doc)

    logger.info(
        "Event created",
        event_id=event.event_id,
        agent_id=event.agent_id,
        event_type=event.event_type,
        action_taken=event_doc.get("action_taken"),
        action_received=event.action,
        blocked=event_doc.get("blocked")
    )
    return {"status": "success", "event_id": event.event_id}


@router.get("/", response_model=EventsResponse)
async def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    severity: Optional[str] = None,
    source: Optional[str] = None,
    start_time: Optional[datetime] = Query(
        None,
        description="Filter events with timestamp >= this ISO datetime (UTC)",
    ),
    end_time: Optional[datetime] = Query(
        None,
        description="Filter events with timestamp <= this ISO datetime (UTC)",
    ),
    current_user=Depends(get_current_user),
):
    """
    Get DLP events with pagination and filtering.

    Supports:
    - severity filter
    - source filter
    - time range via start_time / end_time
    """
    db = get_mongodb()

    # Build query filter
    query_filter: Dict[str, Any] = {}
    if severity:
        query_filter["severity"] = severity
    if source:
        query_filter["source"] = source
    if start_time or end_time:
        time_filter: Dict[str, Any] = {}
        if start_time:
            time_filter["$gte"] = start_time
        if end_time:
            time_filter["$lte"] = end_time
        query_filter["timestamp"] = time_filter

    # Query MongoDB
    cursor = (
        db.dlp_events.find(query_filter)
        .sort("timestamp", -1)
        .skip(skip)
        .limit(limit)
    )
    events_raw = await cursor.to_list(length=limit)

    # Convert MongoDB documents to match DLPEvent model
    events = []
    for event_doc in events_raw:
        # Remove MongoDB _id field and ensure all required fields exist
        event_dict = {k: v for k, v in event_doc.items() if k != "_id"}

        # Ensure required fields have defaults if missing
        if "agent_id" not in event_dict:
            event_dict["agent_id"] = event_dict.get("agent_id") or "unknown"
        if "classification_score" not in event_dict:
            event_dict["classification_score"] = 0.0
        if "classification_labels" not in event_dict:
            event_dict["classification_labels"] = []
        if "policy_id" not in event_dict:
            event_dict["policy_id"] = None
        if "file_path" not in event_dict:
            event_dict["file_path"] = None
        if "destination" not in event_dict:
            event_dict["destination"] = None

        events.append(event_dict)

    # Get total count for pagination
    total = await db.dlp_events.count_documents(query_filter)

    logger.info(
        "Events queried",
        user=getattr(current_user, "email", None),
        count=len(events),
        total=total,
        filters=query_filter,
    )

    return {
        "events": events,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{event_id}", response_model=DLPEvent)
async def get_event(
    event_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get specific DLP event by ID
    """
    db = get_mongodb()
    event = await db.dlp_events.find_one({"id": event_id})

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return event


@router.get("/stats/summary")
async def get_event_stats(
    current_user: dict = Depends(get_current_user),
):
    """
    Get event statistics summary
    """
    db = get_mongodb()

    # Aggregate statistics
    total_events = await db.dlp_events.count_documents({})
    blocked_events = await db.dlp_events.count_documents({"blocked": True})

    # Events by severity
    severity_pipeline = [
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
    ]
    severity_stats = await db.dlp_events.aggregate(severity_pipeline).to_list(None)

    # Events by source
    source_pipeline = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}}
    ]
    source_stats = await db.dlp_events.aggregate(source_pipeline).to_list(None)

    return {
        "total_events": total_events,
        "blocked_events": blocked_events,
        "by_severity": {item["_id"]: item["count"] for item in severity_stats},
        "by_source": {item["_id"]: item["count"] for item in source_stats},
    }


@router.get("/stats/by-type")
async def get_events_by_type(
    current_user: dict = Depends(get_current_user),
):
    """
    Get events grouped by type for dashboard charts
    """
    db = get_mongodb()

    # Aggregate events by event_type
    pipeline = [
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    type_stats = await db.dlp_events.aggregate(pipeline).to_list(None)
    
    # Format for chart component
    return [
        {"type": item["_id"] or "unknown", "count": item["count"]}
        for item in type_stats
    ]


@router.get("/stats/by-severity")
async def get_events_by_severity(
    current_user: dict = Depends(get_current_user),
):
    """
    Get events grouped by severity for dashboard charts
    """
    db = get_mongodb()

    # Aggregate events by severity
    pipeline = [
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    severity_stats = await db.dlp_events.aggregate(pipeline).to_list(None)
    
    # Format for chart component
    return [
        {"severity": item["_id"] or "unknown", "count": item["count"]}
        for item in severity_stats
    ]
