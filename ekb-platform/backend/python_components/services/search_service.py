import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sentence_transformers import SentenceTransformer
import numpy as np # pgvector returns numpy arrays for embeddings if not automatically cast

from .. import models, schemas
from ..models.document_chunk import DocumentChunk # Explicit import
from ..models.ingested_document import IngestedDocument # Explicit import

# Initialize the Sentence Transformer model (e.g., all-MiniLM-L6-v2)
# This model will be loaded once when the module is imported.
MODEL_NAME = 'all-MiniLM-L6-v2'
print(f"Loading sentence transformer model for Search Service: {MODEL_NAME}...")
try:
    embedding_model = SentenceTransformer(MODEL_NAME)
    print(f"Search Service: Model '{MODEL_NAME}' loaded successfully.")
except Exception as e:
    print(f"Search Service: Error loading sentence transformer model '{MODEL_NAME}': {e}")
    embedding_model = None # Set to None if loading fails


def semantic_search(
    db: Session, 
    query_text: str, 
    top_k: int = 10
) -> List[schemas.SearchResultItem]:
    """
    Performs semantic search for document chunks based on query_text.
    """
    if not embedding_model:
        raise RuntimeError("Embedding model is not loaded. Cannot perform semantic search.")

    if not query_text.strip():
        return []

    # 1. Generate embedding for the query_text
    query_embedding = embedding_model.encode(query_text)

    # 2. Construct SQLAlchemy query
    # Using l2_distance as an example. Cosine distance (<=>) or inner product (<#>) might also be suitable.
    # For cosine similarity, you'd typically use 1 - cosine_distance if your vector op gives distance.
    # pgvector's <=> operator gives cosine distance (0 to 2, smaller is more similar for normalized vectors).
    # pgvector's <-> operator gives L2 distance.
    # pgvector's <#> operator gives negative inner product (smaller is more similar for normalized vectors).
    
    # Let's use L2 distance for this example.
    # The type of query_embedding is numpy.ndarray. pgvector expects a list or numpy array.
    
    # Query to find DocumentChunk entities and their similarity score,
    # joining with IngestedDocument to get parent document details.
    results_with_distance = (
        db.query(
            DocumentChunk,
            IngestedDocument.source_uri,
            IngestedDocument.doc_metadata,
            DocumentChunk.embedding.l2_distance(query_embedding).label("distance") 
            # Use .label("distance") to name the calculated distance column
        )
        .join(IngestedDocument, DocumentChunk.doc_id == IngestedDocument.doc_id)
        .order_by(DocumentChunk.embedding.l2_distance(query_embedding)) # Order by distance (ascending)
        .limit(top_k)
        .all()
    )
    
    # 3. Map query results to SearchResultItem Pydantic models
    search_results: List[schemas.SearchResultItem] = []
    for chunk, source_uri, doc_meta, distance in results_with_distance:
        search_results.append(
            schemas.SearchResultItem(
                doc_id=chunk.doc_id,
                chunk_id=chunk.chunk_id,
                chunk_text=chunk.chunk_text,
                source_uri=source_uri,
                doc_metadata=doc_meta,
                similarity_score=float(distance) # Ensure distance is float; L2 distance, smaller is better
                                                 # If using cosine distance (0-2), smaller is better.
                                                 # If using cosine similarity (1 to -1), larger is better.
                                                 # For this example, distance IS similarity_score, so smaller = more similar.
                                                 # If you want a score where higher = better, you might transform it (e.g., 1 / (1 + distance))
            )
        )
        
    return search_results
