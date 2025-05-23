import uuid
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Schema for displaying a single audit log entry
class AuditLogDisplay(BaseModel):
    log_id: uuid.UUID
    timestamp: datetime # Ensuring this is datetime for proper serialization
    user_id: Optional[uuid.UUID] = None
    username: Optional[str] = None
    action: str
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    success: Optional[bool] = None

    class Config:
        orm_mode = True

# Schema for the paginated list of audit logs
class AuditLogResponse(BaseModel):
    items: List[AuditLogDisplay]
    total: int
    page: int
    size: int
    # Optional: total_pages: int # Can be calculated on the client or added here
    # pages: int = Field(..., description="Total number of pages") # Example if adding total_pages
