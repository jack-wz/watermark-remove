import uuid
from sqlalchemy import Column, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from db.session import Base # Assuming python_components is in sys.path

class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Using "event_timestamp" to avoid potential conflict with SQLAlchemy's own 'timestamp' attribute handling if any
    # However, the schema uses "timestamp". If using direct column name, ensure it's quoted if it's a keyword.
    # For consistency with schema, let's use "timestamp" and assume SQLAlchemy handles it or it's quoted in DDL.
    # If issues arise, rename to event_timestamp.
    timestamp = Column("timestamp", DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete="SET NULL"), nullable=True)
    username = Column(Text, nullable=True) # Denormalized username
    
    action = Column(Text, nullable=False)
    details = Column(JSONB, nullable=True)
    ip_address = Column(Text, nullable=True)
    success = Column(Boolean, nullable=True) # True for success, False for failure, Null for not applicable

    # No explicit relationships needed from AuditLog side typically, but can be added if required.
    # user = relationship("User") # If you need to access User object from AuditLog instance

    def __repr__(self):
        return f"<AuditLog(log_id='{self.log_id}', action='{self.action}', user_id='{self.user_id}', timestamp='{self.timestamp}')>"
