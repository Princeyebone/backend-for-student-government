"""Audit logging utilities"""
from sqlmodel import Session
from fastapi import Request
from typing import Optional
import uuid
from datetime import datetime

from .model import AuditLog, User


def create_audit_log(
    session: Session,
    user: User,
    action: str,
    resource: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[str] = None,
    request: Optional[Request] = None
):
    """
    Create an audit log entry
    
    Args:
        session: Database session
        user: User performing the action
        action: Action being performed (e.g., "login", "create_news", "delete_user")
        resource: Resource being affected (e.g., "news", "user", "leadership")
        resource_id: ID of the affected resource
        details: Additional details about the action
        request: FastAPI request object to extract IP address
    """
    ip_address = None
    if request:
        # Try to get real IP from headers (if behind proxy)
        ip_address = request.headers.get("X-Forwarded-For")
        if not ip_address:
            ip_address = request.headers.get("X-Real-IP")
        if not ip_address and request.client:
            ip_address = request.client.host
    
    log_entry = AuditLog(
        user_id=user.id,
        user_email=user.email,
        user_role=user.role.value,
        action=action,
        resource=resource,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        timestamp=datetime.utcnow()
    )
    
    session.add(log_entry)
    session.commit()
    
    return log_entry
