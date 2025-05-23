import uuid
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class IngestionResponse(BaseModel):
    doc_id: uuid.UUID
    source_uri: str
    doc_type: str
    processing_status: str
    message: str = "File processed successfully."
    space_id: Optional[uuid.UUID] = None
    uploaded_by_user_id: uuid.UUID
    doc_metadata: Optional[Dict[str, Any]] = None # To match IngestedDocument.doc_metadata
    created_at: datetime # From IngestedDocument model

    class Config:
        orm_mode = True

class IngestedDocumentDisplay(BaseModel):
    doc_id: uuid.UUID
    source_uri: str
    doc_type: str
    extracted_text: Optional[str] = None
    doc_metadata: Optional[Dict[str, Any]] = None
    space_id: Optional[uuid.UUID] = None
    uploaded_by_user_id: Optional[uuid.UUID] = None # Optional if uploader can be SET NULL
    created_at: datetime # IngestedDocument.created_at is effectively ingested_at
    updated_at: datetime # From IngestedDocument model (record update time)
    processing_status: Optional[str] = None
    last_processed_at: Optional[datetime] = None
    error_message: Optional[str] = None


    class Config:
        orm_mode = True
