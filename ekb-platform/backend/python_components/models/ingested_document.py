import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship # Import relationship

from db.session import Base # Assuming python_components is in sys.path
# Import User and Space models if relationships are to be explicitly defined here
# from .user import User
# from .space import Space
# from .document_chunk import DocumentChunk # Import for relationship typing - will be done by Alembic later if needed by type checker

class IngestedDocument(Base):
    __tablename__ = "ingested_documents"

    doc_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_uri = Column(Text, nullable=False, unique=True)
    doc_type = Column(String, nullable=False) # e.g., 'markdown', 'pdf'
    
    # Using raw_content_ref as per the schema, assuming it's a path or reference
    raw_content_ref = Column(Text, nullable=True)
    
    extracted_text = Column(Text, nullable=True)
    
    doc_metadata = Column(JSONB, nullable=True) # Renamed from metadata
    
    space_id = Column(UUID(as_uuid=True), ForeignKey('spaces.space_id', ondelete="SET NULL"), nullable=True)
    uploaded_by_user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete="SET NULL"), nullable=True)
    
    # Timestamps from the schema
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    content_updated_at = Column(DateTime(timezone=True), server_default=func.now()) # Or should be nullable if not always known
    
    processing_status = Column(String, default='pending') # e.g., 'pending', 'processing', 'completed', 'failed'
    last_processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    # Standard created_at and updated_at for the record itself
    # The schema used ingested_at for creation, let's add a separate updated_at for record changes
    # For simplicity, I'll rely on ingested_at as creation and add a standard updated_at.
    # The schema comments suggest using a trigger for a generic 'updated_at'.
    # Let's add it here for ORM awareness, assuming the trigger handles the update.
    # If no trigger, use onupdate=func.now().
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # Alias for ingested_at essentially
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships (optional, but good for ORM usage)
    # space = relationship("Space", backref="ingested_documents") # Example, adjust if needed
    # uploader = relationship("User", backref="uploaded_documents") # Example, adjust if needed

    # Relationship to DocumentChunks
    # This assumes DocumentChunk model will have a 'document' relationship back_populating this.
    chunks = relationship(
        "DocumentChunk", 
        back_populates="document", 
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_order" # Keep chunks ordered
    )

    def __repr__(self):
        return f"<IngestedDocument(doc_id='{self.doc_id}', source_uri='{self.source_uri}', doc_type='{self.doc_type}')>"

# Ensure models/user.py has Role.in_space_links and User.space_links if those backrefs were added.
# For IngestedDocument relationships:
# In models/user.py, User class:
#   uploaded_documents = relationship("IngestedDocument", back_populates="uploader")
# In models/space.py, Space class:
#   documents = relationship("IngestedDocument", back_populates="space")
# And then adjust the relationships here to use back_populates.
# For now, keeping them commented out to avoid cross-file modification in one step.
