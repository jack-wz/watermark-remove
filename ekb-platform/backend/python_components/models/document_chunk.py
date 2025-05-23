import uuid
from sqlalchemy import Column, Text, INTEGER, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import VECTOR # Import VECTOR type

from db.session import Base # Assuming python_components is in sys.path
# from .ingested_document import IngestedDocument # Import for relationship typing

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    chunk_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id = Column(UUID(as_uuid=True), ForeignKey('ingested_documents.doc_id', ondelete="CASCADE"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    
    # Define the embedding dimension (e.g., 384 for all-MiniLM-L6-v2)
    # This should match the dimension used when generating embeddings.
    embedding = Column(VECTOR(384), nullable=True) # Nullable if embedding generation can fail or is deferred
    
    chunk_order = Column(INTEGER, nullable=False) # Order of the chunk within the document
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to IngestedDocument
    # The IngestedDocument model will need a corresponding back_populates or backref.
    document = relationship("IngestedDocument", back_populates="chunks")

    def __repr__(self):
        return f"<DocumentChunk(chunk_id='{self.chunk_id}', doc_id='{self.doc_id}', order='{self.chunk_order}')>"


# In models/ingested_document.py, you would add the other side of the relationship:
# from .document_chunk import DocumentChunk # Import at the top
# class IngestedDocument(Base):
#   ...
#   chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan", order_by="DocumentChunk.chunk_order")
#   ...
