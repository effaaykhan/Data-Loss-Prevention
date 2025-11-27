"""
Google Drive cloud connector models.
"""

from __future__ import annotations

import base64
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional, ClassVar

from cryptography.fernet import Fernet
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.config import settings
from app.core.database import Base


def _build_cipher() -> Fernet:
    """
    Create a stable Fernet cipher derived from the application SECRET_KEY.

    Fernet keys must be 32 url-safe base64 encoded bytes. We derive one by
    hashing SECRET_KEY with SHA-256 and base64-encoding the digest.
    """
    secret = settings.SECRET_KEY.encode("utf-8")
    digest = hashlib.sha256(secret).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


class GoogleDriveConnection(Base):
    """
    Represents an authorized Google Drive connection (per user).

    Stores encrypted OAuth tokens plus bookkeeping data so the polling
    service can resume from the correct cursor.
    """

    __tablename__ = "google_drive_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_name = Column(String(255), nullable=True)
    google_user_id = Column(String(255), nullable=False)
    google_user_email = Column(String(255), nullable=True)
    refresh_token = Column(Text, nullable=False)
    access_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    scopes = Column(JSON, nullable=True, default=list)
    last_activity_cursor = Column(String(255), nullable=True)
    last_polled_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="active")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    folders = relationship(
        "GoogleDriveProtectedFolder",
        cascade="all, delete-orphan",
        back_populates="connection",
    )

    __allow_unmapped__ = True

    _cipher: ClassVar[Optional[Fernet]] = None

    @classmethod
    def _get_cipher(cls) -> Fernet:
        if cls._cipher is None:
            cls._cipher = _build_cipher()
        return cls._cipher

    def set_refresh_token(self, token: str) -> None:
        """Encrypt and store the refresh token."""
        if not token:
            raise ValueError("Refresh token cannot be empty")
        cipher = self._get_cipher()
        self.refresh_token = cipher.encrypt(token.encode("utf-8")).decode("utf-8")

    def get_refresh_token(self) -> Optional[str]:
        """Return decrypted refresh token."""
        if not self.refresh_token:
            return None
        cipher = self._get_cipher()
        return cipher.decrypt(self.refresh_token.encode("utf-8")).decode("utf-8")

    def set_access_token(self, token: Optional[str]) -> None:
        """Encrypt and store the short-lived access token (optional)."""
        if not token:
            self.access_token = None
            return
        cipher = self._get_cipher()
        self.access_token = cipher.encrypt(token.encode("utf-8")).decode("utf-8")

    def get_access_token(self) -> Optional[str]:
        """Return decrypted access token if present."""
        if not self.access_token:
            return None
        cipher = self._get_cipher()
        return cipher.decrypt(self.access_token.encode("utf-8")).decode("utf-8")

    def is_token_expired(self) -> bool:
        """True when the cached access token is missing or expired."""
        if not self.token_expiry or not self.access_token:
            return True
        return datetime.utcnow() >= self.token_expiry

    def mark_error(self, message: str) -> None:
        """Record last sync error and flip status."""
        self.status = "error"
        self.error_message = message
        self.updated_at = datetime.utcnow()

    def mark_polled(self, cursor: Optional[str], polled_at: Optional[datetime] = None) -> None:
        """Update cursor/timestamps after a successful poll."""
        self.last_activity_cursor = cursor or self.last_activity_cursor
        self.last_polled_at = polled_at or datetime.utcnow()
        self.status = "active"
        self.error_message = None
        self.updated_at = datetime.utcnow()


class GoogleDriveProtectedFolder(Base):
    """
    Folder metadata tracked per connection. These represent the user-selected
    directories that should be polled by the Drive Activity API.
    """

    __tablename__ = "google_drive_protected_folders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("google_drive_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    folder_id = Column(String(255), nullable=False)
    folder_name = Column(String(512), nullable=True)
    folder_path = Column(Text, nullable=True)
    sensitivity_level = Column(String(20), nullable=False, default="medium")
    last_seen_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    connection = relationship("GoogleDriveConnection", back_populates="folders")

    def touch(self, timestamp: Optional[datetime] = None) -> None:
        """Update the folder's last-seen timestamp."""
        ts = timestamp or datetime.utcnow()
        if ts.tzinfo is not None:
            ts = ts.astimezone(timezone.utc).replace(tzinfo=None)
        self.last_seen_timestamp = ts
        self.updated_at = datetime.utcnow()

