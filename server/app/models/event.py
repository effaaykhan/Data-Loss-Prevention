"""
Event Database Model (PostgreSQL)
Represents DLP events detected by agents or collectors
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(String(64), unique=True, nullable=False, index=True)

    # Event classification
    event_type = Column(String(50), nullable=False, index=True)  # file, clipboard, usb, network, cloud
    event_subtype = Column(String(50), nullable=True)  # file_copy, file_delete, clipboard_copy, etc.

    # Source information
    agent_id = Column(String(64), nullable=True, index=True)
    source_type = Column(String(50), nullable=False)  # agent, collector, connector
    source_id = Column(String(64), nullable=True)

    # User information
    user_email = Column(String(255), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    username = Column(String(255), nullable=True)

    # Event details
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    action = Column(String(50), nullable=False)  # allowed, blocked, alerted, quarantined, logged

    # File/data information
    file_path = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_hash = Column(String(64), nullable=True)

    # Classification results
    classification = Column(JSON, nullable=True)  # {"labels": ["PAN", "SSN"], "score": 0.95, "method": "regex"}
    confidence_score = Column(Float, nullable=True)

    # Policy information
    policy_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    policy_name = Column(String(255), nullable=True)
    policy_violated = Column(String(255), nullable=True)

    # Destination information
    destination = Column(String(255), nullable=True)  # usb, cloud, email, etc.
    destination_details = Column(JSON, nullable=True)

    # Network information (for network events)
    source_ip = Column(String(45), nullable=True)
    destination_ip = Column(String(45), nullable=True)
    protocol = Column(String(20), nullable=True)

    # Additional metadata
    details = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)  # ["pci-dss", "gdpr", "hipaa"]

    # Status and processing
    status = Column(String(20), nullable=False, default="new")  # new, processed, archived
    reviewed = Column(String(20), nullable=False, default="no")  # yes, no
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    # Timestamps
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for common queries
    __table_args__ = (
        Index('idx_event_severity_timestamp', 'severity', 'timestamp'),
        Index('idx_event_user_timestamp', 'user_email', 'timestamp'),
        Index('idx_event_type_timestamp', 'event_type', 'timestamp'),
        Index('idx_event_agent_timestamp', 'agent_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<Event {self.event_id} - {self.event_type}>"

    def to_dict(self):
        """Convert event to dictionary"""
        return {
            "id": str(self.id),
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_subtype": self.event_subtype,
            "agent_id": self.agent_id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "user_email": self.user_email,
            "user_id": str(self.user_id) if self.user_id else None,
            "username": self.username,
            "description": self.description,
            "severity": self.severity,
            "action": self.action,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_hash": self.file_hash,
            "classification": self.classification,
            "confidence_score": self.confidence_score,
            "policy_id": str(self.policy_id) if self.policy_id else None,
            "policy_name": self.policy_name,
            "policy_violated": self.policy_violated,
            "destination": self.destination,
            "destination_details": self.destination_details,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "protocol": self.protocol,
            "details": self.details,
            "tags": self.tags,
            "status": self.status,
            "reviewed": self.reviewed,
            "reviewed_by": str(self.reviewed_by) if self.reviewed_by else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "timestamp": self.timestamp.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
