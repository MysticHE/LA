"""Audit logging service for security-critical operations.

This module provides structured audit logging for key operations like
API key connect/disconnect, and unauthorized access attempts. All logs
are guaranteed to never contain actual API keys.
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from src.utils.logging import get_secure_logger, redact_api_keys, redact_dict_values


class AuditEventType(str, Enum):
    """Types of auditable events."""
    KEY_CONNECT = "key_connect"
    KEY_DISCONNECT = "key_disconnect"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


class AuditStatus(str, Enum):
    """Status of an audited operation."""
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"


@dataclass
class AuditEntry:
    """Represents a single audit log entry."""
    event_type: AuditEventType
    session_id: str
    timestamp: str
    status: AuditStatus
    provider: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {}
        for key, value in asdict(self).items():
            if value is not None:
                if isinstance(value, Enum):
                    result[key] = value.value
                else:
                    result[key] = value
        return result

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class AuditLogger:
    """Audit logger for security-critical operations.

    All logged data is automatically redacted to ensure API keys
    never appear in audit logs.

    Attributes:
        _entries: In-memory storage of audit entries for querying.
                  In production, this should be persisted to a database.
    """

    def __init__(self, logger_name: str = "audit"):
        """Initialize the audit logger.

        Args:
            logger_name: Name for the logger instance.
        """
        self._logger = get_secure_logger(f"audit.{logger_name}")
        self._entries: List[AuditEntry] = []

    def _get_timestamp(self) -> str:
        """Get current ISO format timestamp."""
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _redact_details(self, details: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Redact sensitive information from details dictionary.

        Args:
            details: Dictionary that may contain sensitive data.

        Returns:
            Redacted dictionary or None if input was None.
        """
        if details is None:
            return None
        return redact_dict_values(details)

    def _redact_session_id(self, session_id: str) -> str:
        """Redact any API keys that might be in session_id.

        This is a defensive measure to ensure API keys are never
        exposed even if accidentally included in session IDs.

        Args:
            session_id: The session identifier.

        Returns:
            Session ID with any API keys redacted.
        """
        return redact_api_keys(session_id)

    def _store_and_log(self, entry: AuditEntry) -> None:
        """Store entry and write to log.

        Args:
            entry: The audit entry to store and log.
        """
        self._entries.append(entry)
        # Log as structured JSON for easier parsing
        self._logger.info("AUDIT: %s", entry.to_json())

    def log_key_connect(
        self,
        session_id: str,
        provider: str,
        status: AuditStatus,
        error_message: Optional[str] = None,
        request_details: Optional[Dict[str, Any]] = None
    ) -> AuditEntry:
        """Log a key connect operation.

        Args:
            session_id: The session identifier.
            provider: The API provider (e.g., "claude", "openai").
            status: The operation status (success/failure).
            error_message: Optional error message if failed.
            request_details: Optional request details (will be redacted).

        Returns:
            The created audit entry.
        """
        entry = AuditEntry(
            event_type=AuditEventType.KEY_CONNECT,
            session_id=self._redact_session_id(session_id),
            timestamp=self._get_timestamp(),
            status=status,
            provider=provider,
            error_message=redact_api_keys(error_message) if error_message else None,
            details=self._redact_details(request_details)
        )
        self._store_and_log(entry)
        return entry

    def log_key_disconnect(
        self,
        session_id: str,
        provider: str,
        status: AuditStatus = AuditStatus.SUCCESS,
        error_message: Optional[str] = None
    ) -> AuditEntry:
        """Log a key disconnect operation.

        Args:
            session_id: The session identifier.
            provider: The API provider (e.g., "claude", "openai").
            status: The operation status.
            error_message: Optional error message if failed.

        Returns:
            The created audit entry.
        """
        entry = AuditEntry(
            event_type=AuditEventType.KEY_DISCONNECT,
            session_id=self._redact_session_id(session_id),
            timestamp=self._get_timestamp(),
            status=status,
            provider=provider,
            error_message=redact_api_keys(error_message) if error_message else None
        )
        self._store_and_log(entry)
        return entry

    def log_unauthorized_access(
        self,
        session_id: str,
        request_path: str,
        request_method: str,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> AuditEntry:
        """Log an unauthorized access attempt.

        Args:
            session_id: The session identifier.
            request_path: The requested URL path.
            request_method: The HTTP method used.
            client_ip: The client's IP address.
            user_agent: The client's User-Agent header.
            details: Additional request details (will be redacted).
            error_message: Optional error description.

        Returns:
            The created audit entry.
        """
        entry = AuditEntry(
            event_type=AuditEventType.UNAUTHORIZED_ACCESS,
            session_id=self._redact_session_id(session_id),
            timestamp=self._get_timestamp(),
            status=AuditStatus.DENIED,
            request_path=redact_api_keys(request_path),
            request_method=request_method,
            client_ip=client_ip,
            user_agent=redact_api_keys(user_agent) if user_agent else None,
            details=self._redact_details(details),
            error_message=redact_api_keys(error_message) if error_message else None
        )
        self._store_and_log(entry)
        return entry

    def query_by_session(self, session_id: str) -> List[AuditEntry]:
        """Query audit entries by session ID.

        Args:
            session_id: The session ID to filter by.

        Returns:
            List of matching audit entries.
        """
        return [e for e in self._entries if e.session_id == session_id]

    def query_by_timestamp_range(
        self,
        start_time: str,
        end_time: str
    ) -> List[AuditEntry]:
        """Query audit entries within a timestamp range.

        Args:
            start_time: ISO format start timestamp.
            end_time: ISO format end timestamp.

        Returns:
            List of audit entries within the time range.
        """
        return [
            e for e in self._entries
            if start_time <= e.timestamp <= end_time
        ]

    def query_by_session_and_timestamp(
        self,
        session_id: str,
        start_time: str,
        end_time: str
    ) -> List[AuditEntry]:
        """Query audit entries by session ID and timestamp range.

        Args:
            session_id: The session ID to filter by.
            start_time: ISO format start timestamp.
            end_time: ISO format end timestamp.

        Returns:
            List of matching audit entries.
        """
        return [
            e for e in self._entries
            if e.session_id == session_id and start_time <= e.timestamp <= end_time
        ]

    def get_all_entries(self) -> List[AuditEntry]:
        """Get all audit entries.

        Returns:
            List of all audit entries.
        """
        return list(self._entries)

    def clear_entries(self) -> None:
        """Clear all stored audit entries.

        Useful for testing. In production, entries should be
        persisted to durable storage before clearing.
        """
        self._entries.clear()


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance.

    Returns:
        The singleton AuditLogger instance.
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def reset_audit_logger() -> None:
    """Reset the global audit logger (for testing).

    Creates a new AuditLogger instance, discarding any
    previously stored entries.
    """
    global _audit_logger
    _audit_logger = AuditLogger()
