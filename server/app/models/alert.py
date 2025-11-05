"""
Alert Database Model (PostgreSQL)
Represents system alerts generated from events or conditions
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(String(64), unique=True, nullable=False, index=True)

    # Alert classification
    alert_type = Column(String(50), nullable=False, index=True)  # policy_violation, system_health, anomaly, threshold
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    priority = Column(Integer, nullable=False, default=100)  # Higher = more important

    # Alert content
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    message = Column(Text, nullable=True)

    # Source information
    source = Column(String(100), nullable=False)  # event, system, policy_engine, ml_classifier
    source_id = Column(String(64), nullable=True)  # Related event_id, agent_id, etc.

    # Related entities
    event_id = Column(String(64), nullable=True, index=True)
    agent_id = Column(String(64), nullable=True, index=True)
    user_email = Column(String(255), nullable=True, index=True)
    policy_id = Column(UUID(as_uuid=True), nullable=True)

    # Alert details
    details = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)  # ["pci-dss", "gdpr", "urgent"]

    # Status and workflow
    status = Column(String(20), nullable=False, default="new", index=True)  # new, acknowledged, investigating, resolved, false_positive
    assigned_to = Column(UUID(as_uuid=True), nullable=True)
    assigned_at = Column(DateTime, nullable=True)

    # Resolution
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_by = Column(UUID(as_uuid=True), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Notification tracking
    notifications_sent = Column(JSON, nullable=True)  # {"email": true, "sms": false, "slack": true}
    notification_history = Column(JSON, nullable=True)

    # Escalation
    escalated = Column(Boolean, default=False, nullable=False)
    escalated_at = Column(DateTime, nullable=True)
    escalation_level = Column(Integer, default=0, nullable=False)

    # Timestamps
    triggered_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for common queries
    __table_args__ = (
        Index('idx_alert_severity_status', 'severity', 'status'),
        Index('idx_alert_type_triggered', 'alert_type', 'triggered_at'),
        Index('idx_alert_user_triggered', 'user_email', 'triggered_at'),
        Index('idx_alert_resolved_triggered', 'resolved', 'triggered_at'),
    )

    def __repr__(self):
        return f"<Alert {self.alert_id} - {self.title}>"

    def to_dict(self):
        """Convert alert to dictionary"""
        return {
            "id": str(self.id),
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "priority": self.priority,
            "title": self.title,
            "description": self.description,
            "message": self.message,
            "source": self.source,
            "source_id": self.source_id,
            "event_id": self.event_id,
            "agent_id": self.agent_id,
            "user_email": self.user_email,
            "policy_id": str(self.policy_id) if self.policy_id else None,
            "details": self.details,
            "metadata": self.metadata,
            "tags": self.tags,
            "status": self.status,
            "assigned_to": str(self.assigned_to) if self.assigned_to else None,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "resolved": self.resolved,
            "resolved_by": str(self.resolved_by) if self.resolved_by else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
            "notifications_sent": self.notifications_sent,
            "notification_history": self.notification_history,
            "escalated": self.escalated,
            "escalated_at": self.escalated_at.isoformat() if self.escalated_at else None,
            "escalation_level": self.escalation_level,
            "triggered_at": self.triggered_at.isoformat(),
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
