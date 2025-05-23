import uuid
from typing import Optional, Dict, Any, List, Tuple # Import List and Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc # For ordering

from .. import models 
from datetime import datetime 

def create_audit_log(
    db: Session,
    action: str,
    user_id: Optional[uuid.UUID] = None,
    username: Optional[str] = None,
    success: Optional[bool] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> models.AuditLog | None:
    """
    Creates an audit log entry.
    """
    try:
        # The 'timestamp' is handled by server_default in the model/DB.
        db_audit_log = models.AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            details=details,
            ip_address=ip_address,
            success=success
            # timestamp is server_default
        )
        db.add(db_audit_log)
        db.commit()
        db.refresh(db_audit_log)
        return db_audit_log
    except Exception as e:
        # Log the error (e.g., to system logs or a dedicated error tracking service)
        print(f"Error creating audit log: {e}")
        # Optionally rollback the session if the audit log is part of a larger transaction
        # that shouldn't fail because of audit logging. However, create_audit_log
        # commits immediately, so this rollback here is for its own transaction.
        try:
            db.rollback()
        except Exception as rb_e:
            print(f"Error during audit log rollback: {rb_e}")
        return None # Indicate failure to create audit log entry

def get_audit_logs(
    db: Session, 
    page: int = 1, 
    size: int = 20, 
    user_id: Optional[uuid.UUID] = None, 
    action: Optional[str] = None, 
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None
) -> Tuple[List[models.AuditLog], int]:
    """
    Retrieves audit logs with pagination and filtering.
    Returns a tuple of (list of AuditLog objects, total count of matching records).
    """
    query = db.query(models.AuditLog)

    # Apply filters
    if user_id:
        query = query.filter(models.AuditLog.user_id == user_id)
    if action:
        query = query.filter(models.AuditLog.action.ilike(f"%{action}%")) # Case-insensitive partial match for action
    if start_date:
        query = query.filter(models.AuditLog.timestamp >= start_date)
    if end_date:
        # Ensure end_date is inclusive of the whole day if only date is provided
        # For datetime, direct comparison is fine. If it's just a date, adjust to end of day.
        query = query.filter(models.AuditLog.timestamp <= end_date)

    # Get total count before pagination
    total_count = query.count()

    # Apply ordering and pagination
    logs = query.order_by(desc(models.AuditLog.timestamp)).limit(size).offset((page - 1) * size).all()
    
    return logs, total_count
