import uuid
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime # Though not directly in SearchResultItem, good for consistency

# Schema for the search query request
class SearchQueryRequest(BaseModel):
    query_text: str = Field(..., min_length=1, description="The text to search for.")
    top_k: int = Field(10, gt=0, le=100, description="Number of top results to return.")
    # space_id: Optional[uuid.UUID] = None # Future: filter search by space
    # doc_ids: Optional[List[uuid.UUID]] = None # Future: filter search by specific documents

# Schema for a single search result item
class SearchResultItem(BaseModel):
    doc_id: uuid.UUID
    chunk_id: uuid.UUID
    chunk_text: str
    source_uri: str # From parent IngestedDocument
    doc_metadata: Optional[Dict[str, Any]] = None # From parent IngestedDocument
    similarity_score: float # Calculated distance/similarity score from pgvector

    class Config:
        orm_mode = True # If results are directly from ORM objects with these attributes

# Schema for the search response
class SearchResponse(BaseModel):
    query_text: str
    results: List[SearchResultItem]
