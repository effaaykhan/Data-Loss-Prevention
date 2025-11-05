"""
Agent Database Model (PostgreSQL)
Represents DLP agents deployed on endpoints
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID, INET
import uuid

from app.core.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hostname = Column(String(255), nullable=False)
    os = Column(String(50), nullable=False)  # windows, linux, macos
    os_version = Column(String(100), nullable=True)
    ip_address = Column(INET, nullable=False)
    version = Column(String(50), nullable=False, default="1.0.0")
    status = Column(String(20), nullable=False, default="offline")  # online, offline, warning, error

    # Agent configuration
    config = Column(JSON, nullable=True)

    # Monitoring capabilities
    capabilities = Column(JSON, nullable=True)  # {"file_monitoring": true, "clipboard": true, "usb": true}

    # Statistics
    total_events = Column(Integer, default=0, nullable=False)
    total_violations = Column(Integer, default=0, nullable=False)

    # Heartbeat and health
    last_seen = Column(DateTime, nullable=True)
    last_heartbeat = Column(DateTime, nullable=True)
    health_status = Column(JSON, nullable=True)  # CPU, memory, disk usage

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    registered_by = Column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<Agent {self.agent_id} - {self.name}>"

    def to_dict(self):
        """Convert agent to dictionary"""
        return {
            "id": str(self.id),
            "agent_id": self.agent_id,
            "name": self.name,
            "hostname": self.hostname,
            "os": self.os,
            "os_version": self.os_version,
            "ip_address": str(self.ip_address),
            "version": self.version,
            "status": self.status,
            "config": self.config,
            "capabilities": self.capabilities,
            "total_events": self.total_events,
            "total_violations": self.total_violations,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "health_status": self.health_status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
