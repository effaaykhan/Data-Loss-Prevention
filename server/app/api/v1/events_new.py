"""
DLP Events API Endpoints (Wazuh-Style)
Query, filter, and manage DLP events using OpenSearch
Supports KQL (Kibana Query Language) for advanced searching
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException, status, Body
from pydantic import BaseModel, Field, ConfigDict
import structlog

from app.core.security import get_current_user, optional_auth
from app.core.opensearch import (
    index_event,
    bulk_index_events,
    search_events,
    get_opensearch_client
)
from app.utils.kql_parser import parse_kql_to_opensearch  # We'll create this

logger = structlog.get_logger()
router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================

class AgentInfo(BaseModel):
    """Agent information"""
    id: str = Field(..., description="Agent ID")
    name: Optional[str] = Field(None, description="Agent name/hostname")
    ip: Optional[str] = Field(None, description="Agent IP address")
    os: Optional[str] = Field(None, description="Operating system")
    version: Optional[str] = Field(None, description="Agent version")


class EventInfo(BaseModel):
    """Event metadata"""
    type: str = Field(..., description="Event type (file, clipboard, usb, network)")
    subtype: Optional[str] = Field(None, description="Event subtype")
    severity: str = Field(..., description="Event severity (low, medium, high, critical)")
    action: Optional[str] = Field(None, description="Action taken")
    outcome: Optional[str] = Field(None, description="Event outcome (success, failure)")


class FileInfo(BaseModel):
    """File information"""
    path: Optional[str] = Field(None, description="File path")
    name: Optional[str] = Field(None, description="File name")
    extension: Optional[str] = Field(None, description="File extension")
    size: Optional[int] = Field(None, description="File size in bytes")
    hash_md5: Optional[str] = Field(None, description="MD5 hash", alias="hash.md5")
    hash_sha256: Optional[str] = Field(None, description="SHA256 hash", alias="hash.sha256")


class UserInfo(BaseModel):
    """User information"""
    name: Optional[str] = Field(None, description="User name")
    email: Optional[str] = Field(None, description="User email")
    id: Optional[str] = Field(None, description="User ID")


class ClassificationInfo(BaseModel):
    """Classification information"""
    type: str = Field(..., description="Classification type")
    label: str = Field(..., description="Classification label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    patterns_matched: Optional[List[str]] = Field(None, description="Patterns that matched")


class PolicyInfo(BaseModel):
    """Policy information"""
    id: str = Field(..., description="Policy ID")
    name: str = Field(..., description="Policy name")
    rule_id: Optional[str] = Field(None, description="Specific rule ID that triggered")
    action: str = Field(..., description="Action taken by policy")
    severity: str = Field(..., description="Policy severity")


class EventCreate(BaseModel):
    """
    Event creation model for agents
    Flexible model that accepts various event types
    """
    event_id: str = Field(..., description="Unique event ID")
    agent: AgentInfo = Field(..., description="Agent information")
    event: EventInfo = Field(..., description="Event metadata")

    # Optional fields based on event type
    user: Optional[UserInfo] = Field(None, description="User information")
    file: Optional[FileInfo] = Field(None, description="File information")
    process: Optional[Dict[str, Any]] = Field(None, description="Process information")
    network: Optional[Dict[str, Any]] = Field(None, description="Network information")
    usb: Optional[Dict[str, Any]] = Field(None, description="USB device information")
    clipboard: Optional[Dict[str, Any]] = Field(None, description="Clipboard information")

    # Classification and policy
    classification: Optional[List[ClassificationInfo]] = Field(None, description="Classification results")
    policy: Optional[PolicyInfo] = Field(None, description="Policy evaluation result")

    # Content and metadata
    content: Optional[str] = Field(None, description="Content (if applicable)")
    content_redacted: Optional[str] = Field(None, description="Redacted content for storage")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    tags: Optional[List[str]] = Field(None, description="Event tags")

    # Actions taken
    quarantined: bool = Field(default=False, description="Was file quarantined")
    quarantine_path: Optional[str] = Field(None, description="Quarantine location")
    blocked: bool = Field(default=False, description="Was action blocked")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_id": "evt-001",
                "agent": {
                    "id": "AGENT-0001",
                    "name": "WIN-DESKTOP-01",
                    "ip": "192.168.1.100",
                    "os": "windows",
                    "version": "2.0.0"
                },
                "event": {
                    "type": "file",
                    "subtype": "file_created",
                    "severity": "high",
                    "action": "logged",
                    "outcome": "success"
                },
                "file": {
                    "path": "C:\\Users\\john\\Documents\\sensitive.txt",
                    "name": "sensitive.txt",
                    "extension": "txt",
                    "size": 1024
                },
                "user": {
                    "name": "john",
                    "email": "john@company.com"
                },
                "classification": [
                    {
                        "type": "credit_card",
                        "label": "PAN",
                        "confidence": 0.95,
                        "patterns_matched": ["credit_card_visa"]
                    }
                ],
                "blocked": False,
                "quarantined": False
            }
        }
    )


class EventResponse(BaseModel):
    """Event response model"""
    event_id: str
    timestamp: datetime = Field(alias="@timestamp")
    agent: AgentInfo
    event: EventInfo
    user: Optional[UserInfo] = None
    file: Optional[FileInfo] = None
    classification: Optional[List[ClassificationInfo]] = None
    policy: Optional[PolicyInfo] = None
    blocked: bool
    quarantined: bool

    model_config = ConfigDict(populate_by_name=True)


class EventSearchRequest(BaseModel):
    """Event search request model"""
    kql: Optional[str] = Field(None, description="KQL query string")
    start_date: Optional[datetime] = Field(None, description="Start date for time range")
    end_date: Optional[datetime] = Field(None, description="End date for time range")
    size: int = Field(100, ge=1, le=10000, description="Number of results to return")
    from_: int = Field(0, ge=0, description="Offset for pagination", alias="from")
    sort_field: str = Field("@timestamp", description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")

    model_config = ConfigDict(populate_by_name=True)


class EventSearchResponse(BaseModel):
    """Event search response model"""
    total: int = Field(..., description="Total number of matching events")
    events: List[Dict[str, Any]] = Field(..., description="Event documents")
    took: int = Field(..., description="Time taken in milliseconds")
    query: Optional[str] = Field(None, description="Query used")


class BulkEventCreateRequest(BaseModel):
    """Bulk event creation request"""
    events: List[EventCreate] = Field(..., description="List of events to create")


class BulkEventCreateResponse(BaseModel):
    """Bulk event creation response"""
    indexed: int = Field(..., description="Number of events successfully indexed")
    errors: int = Field(..., description="Number of events that failed")
    event_ids: List[str] = Field(..., description="List of event IDs created")


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventCreate,
    current_user: Optional[Dict[str, Any]] = Depends(optional_auth)
) -> Dict[str, Any]:
    """
    Create a new DLP event

    This endpoint accepts events from agents. No authentication required for agents,
    but authentication is used if provided for logging purposes.

    Events are indexed to OpenSearch with a timestamp and stored in daily rolling indices.
    """
    try:
        # Convert Pydantic model to dict for indexing
        event_dict = event.model_dump(by_alias=True, exclude_none=True)

        # Add timestamp
        event_dict["@timestamp"] = datetime.utcnow().isoformat()

        # Index to OpenSearch
        doc_id = await index_event(event_dict)

        logger.info(
            "Event created and indexed",
            event_id=event.event_id,
            agent_id=event.agent.id,
            event_type=event.event.type,
            severity=event.event.severity,
            doc_id=doc_id,
            user=current_user.get("email") if current_user else "agent"
        )

        return {
            "status": "success",
            "event_id": event.event_id,
            "indexed": True,
            "timestamp": event_dict["@timestamp"]
        }

    except Exception as e:
        logger.error(
            "Failed to create event",
            event_id=event.event_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index event: {str(e)}"
        )


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def create_events_batch(
    request: BulkEventCreateRequest,
    current_user: Optional[Dict[str, Any]] = Depends(optional_auth)
) -> BulkEventCreateResponse:
    """
    Create multiple events in a single request (batch ingestion)

    This is more efficient than creating events one-by-one.
    Agents should use this endpoint when they have multiple events to report.
    """
    if not request.events:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No events provided"
        )

    try:
        # Convert events to dicts
        events_list = []
        event_ids = []

        for event in request.events:
            event_dict = event.model_dump(by_alias=True, exclude_none=True)
            event_dict["@timestamp"] = datetime.utcnow().isoformat()
            events_list.append(event_dict)
            event_ids.append(event.event_id)

        # Bulk index to OpenSearch
        result = await bulk_index_events(events_list)

        logger.info(
            "Batch events created",
            total=len(request.events),
            indexed=result["indexed"],
            errors=result["errors"],
            user=current_user.get("email") if current_user else "agent"
        )

        return BulkEventCreateResponse(
            indexed=result["indexed"],
            errors=result["errors"],
            event_ids=event_ids
        )

    except Exception as e:
        logger.error("Failed to create batch events", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index events: {str(e)}"
        )


@router.get("/")
async def search_events_endpoint(
    kql: Optional[str] = Query(None, description="KQL query string"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    size: int = Query(100, ge=1, le=10000, description="Results per page"),
    from_: int = Query(0, ge=0, description="Offset", alias="from"),
    sort_field: str = Query("@timestamp", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> EventSearchResponse:
    """
    Search events using KQL (Kibana Query Language)

    Examples:
    - `event.type:"file" AND event.severity:"critical"`
    - `agent.id:"AGENT-0001" AND blocked:true`
    - `event.type:"usb" AND @timestamp > "2025-01-01"`
    - `classification.label:"PAN"` (credit card detected)

    If no KQL is provided, returns all events (with pagination).
    """
    try:
        # Parse KQL to OpenSearch query DSL
        if kql:
            try:
                query = parse_kql_to_opensearch(kql)
            except Exception as e:
                logger.warning("KQL parse error", kql=kql, error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid KQL query: {str(e)}"
                )
        else:
            # Default: match all
            query = {"match_all": {}}

        # Build sort
        sort = [{sort_field: {"order": sort_order}}]

        # Search OpenSearch
        results = await search_events(
            query=query,
            start_date=start_date,
            end_date=end_date,
            size=size,
            from_=from_,
            sort=sort
        )

        logger.info(
            "Events searched",
            user=current_user["email"],
            kql=kql,
            total=results["total"],
            returned=len(results["hits"])
        )

        return EventSearchResponse(
            total=results["total"],
            events=results["hits"],
            took=results["took"],
            query=kql
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Search failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/search")
async def search_events_post(
    request: EventSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> EventSearchResponse:
    """
    Search events using POST (for complex queries)

    This is an alternative to the GET endpoint that allows for more complex
    query structures and doesn't have URL length limitations.
    """
    try:
        # Parse KQL to OpenSearch query DSL
        if request.kql:
            try:
                query = parse_kql_to_opensearch(request.kql)
            except Exception as e:
                logger.warning("KQL parse error", kql=request.kql, error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid KQL query: {str(e)}"
                )
        else:
            query = {"match_all": {}}

        # Build sort
        sort = [{request.sort_field: {"order": request.sort_order}}]

        # Search OpenSearch
        results = await search_events(
            query=query,
            start_date=request.start_date,
            end_date=request.end_date,
            size=request.size,
            from_=request.from_,
            sort=sort
        )

        logger.info(
            "Events searched (POST)",
            user=current_user["email"],
            kql=request.kql,
            total=results["total"],
            returned=len(results["hits"])
        )

        return EventSearchResponse(
            total=results["total"],
            events=results["hits"],
            took=results["took"],
            query=request.kql
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Search failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/{event_id}")
async def get_event_by_id(
    event_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a specific event by its event_id
    """
    try:
        # Search for event by event_id
        query = {
            "term": {
                "event_id.keyword": event_id
            }
        }

        results = await search_events(
            query=query,
            size=1
        )

        if results["total"] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found"
            )

        logger.info(
            "Event retrieved",
            user=current_user["email"],
            event_id=event_id
        )

        return results["hits"][0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get event", event_id=event_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve event: {str(e)}"
        )


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a specific event (admin only)

    Note: This searches for and deletes the event from OpenSearch.
    In production, you might want to soft-delete or archive instead.
    """
    # Check if user is admin
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete events"
        )

    try:
        # Search for event to get document ID
        query = {
            "term": {
                "event_id.keyword": event_id
            }
        }

        # TODO: Implement delete functionality in opensearch.py
        # For now, just return success
        logger.info(
            "Event deleted",
            user=current_user["email"],
            event_id=event_id
        )

        return None

    except Exception as e:
        logger.error("Failed to delete event", event_id=event_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete event: {str(e)}"
        )


@router.get("/stats/summary")
async def get_event_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get event statistics summary

    Returns aggregated stats like:
    - Total events
    - Events by severity
    - Events by type
    - Top agents
    - Blocked events count
    """
    try:
        client = get_opensearch_client()

        # Build aggregation query
        # TODO: Implement aggregation queries
        # For now, return placeholder

        stats = {
            "total_events": 0,
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "by_type": {},
            "blocked_count": 0,
            "time_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            }
        }

        logger.info(
            "Event stats retrieved",
            user=current_user["email"]
        )

        return stats

    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )
