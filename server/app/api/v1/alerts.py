"""
Alerts API Endpoints
Security alerts and notifications
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
import structlog

from app.core.security import get_current_user
from app.core.database import get_mongodb

logger = structlog.get_logger()
router = APIRouter()


class Alert(BaseModel):
    id: str
    timestamp: datetime
    title: str
    description: str
    severity: str
    status: str
    event_id: str
    agent_id: Optional[str] = None
    created_at: Optional[datetime] = None


class AlertsResponse(BaseModel):
    alerts: List[Alert]
    counts: Dict[str, int]


@router.get("/", response_model=AlertsResponse)
async def get_alerts(
    current_user: dict = Depends(get_current_user),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
):
    """
    Get all active alerts
    Generates alerts from critical/high severity events if no alerts exist in database
    Returns alerts list (limited to 100) and total counts for accurate statistics
    """
    db = get_mongodb()
    
    # Check if alerts collection exists and has alerts
    alerts_collection = db.get_collection("alerts")
    alert_count = await alerts_collection.count_documents({})
    
    alerts = []
    counts = {"new": 0, "acknowledged": 0, "resolved": 0, "total": 0}
    
    if alert_count > 0:
        # Query alerts from database
        query_filter = {}
        if severity:
            query_filter["severity"] = severity
        if status:
            query_filter["status"] = status
        
        # Get total counts before limiting
        counts["total"] = await alerts_collection.count_documents(query_filter)
        counts["new"] = await alerts_collection.count_documents({**query_filter, "status": "new"})
        counts["acknowledged"] = await alerts_collection.count_documents({**query_filter, "status": "acknowledged"})
        counts["resolved"] = await alerts_collection.count_documents({**query_filter, "status": "resolved"})
        
        # Get limited list for display
        cursor = alerts_collection.find(query_filter).sort("timestamp", -1).limit(100)
        async for alert_doc in cursor:
            # Remove MongoDB _id field
            alert_dict = {k: v for k, v in alert_doc.items() if k != "_id"}
            alerts.append(Alert(**alert_dict))
    else:
        # Generate alerts from critical/high severity events
        events_collection = db.dlp_events
        
        # Query critical and high severity events
        query_filter = {"severity": {"$in": ["critical", "high"]}}
        if severity:
            query_filter["severity"] = severity
        
        # Get total counts before limiting
        counts["total"] = await events_collection.count_documents(query_filter)
        # For events, we'll count all as "new" since they're being converted to alerts
        counts["new"] = counts["total"]
        counts["acknowledged"] = 0
        counts["resolved"] = 0
        
        # Get limited list for display
        cursor = events_collection.find(query_filter).sort("timestamp", -1).limit(100)
        
        async for event_doc in cursor:
            # Create alert from event
            alert_id = event_doc.get("id") or event_doc.get("event_id", "")
            severity_level = event_doc.get("severity", "medium")
            
            # Generate alert title and description
            event_type = event_doc.get("event_type", "unknown")
            file_path = event_doc.get("file_path", "")
            description_text = event_doc.get("description", "")
            
            if event_type == "file" and file_path:
                title = f"Sensitive Data Detected in File"
                description = f"File: {file_path}\n{description_text}"
            elif event_type == "clipboard":
                title = f"Sensitive Data Copied to Clipboard"
                description = description_text or "Sensitive data detected in clipboard content"
            elif event_type == "usb":
                title = f"USB Device Connected"
                description = description_text or f"USB device connected: {event_doc.get('details', {}).get('device_name', 'Unknown')}"
            else:
                title = f"DLP Event Detected"
                description = description_text or f"{event_type} event detected"
            
            # Determine alert status based on event
            alert_status = "new"  # All generated alerts start as "new"
            if status:
                alert_status = status
            
            alert = Alert(
                id=alert_id,
                timestamp=event_doc.get("timestamp", datetime.utcnow()),
                title=title,
                description=description,
                severity=severity_level,
                status=alert_status,
                event_id=alert_id,
                agent_id=event_doc.get("agent_id"),
                created_at=event_doc.get("timestamp", datetime.utcnow()),
            )
            alerts.append(alert)
    
    logger.info(
        "Alerts retrieved",
        user=getattr(current_user, "email", "unknown"),
        count=len(alerts),
        total_count=counts["total"],
        filters={"severity": severity, "status": status},
    )
    
    return AlertsResponse(alerts=alerts, counts=counts)


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Acknowledge an alert
    """
    logger.info(
        "Alert acknowledged",
        alert_id=alert_id,
        user=getattr(current_user, "email", "unknown"),
    )

    return {"message": "Alert acknowledged"}
