-- Data Storage Schema for EKB Platform (PostgreSQL)

-- Ensure UUID generation is enabled (if not already from user_management_schema.sql)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Ingested Documents Table: Stores information about documents ingested into the system.
CREATE TABLE ingested_documents (
    doc_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_uri TEXT NOT NULL UNIQUE, -- e.g., path to original file, URL, or a unique identifier for the source
    doc_type TEXT NOT NULL, -- e.g., 'markdown', 'pdf', 'txt', 'webpage'
    
    -- Storing raw content might be inefficient for large files.
    -- Consider storing a path to the file in a managed storage (e.g., S3, local filesystem)
    -- or using PostgreSQL's Large Object facility if content must be in DB.
    -- For this example, assuming raw_content might be stored directly for smaller docs or as a reference.
    raw_content_ref TEXT, -- Path/reference to stored raw content, or NULL if not applicable/stored elsewhere
    
    extracted_text TEXT, -- Plain text extracted from the document
    
    doc_metadata JSONB, -- For storing other details like author, title, custom tags, source-specific metadata
    
    -- Link to a space if the document is associated with one
    space_id UUID REFERENCES spaces(space_id) ON DELETE SET NULL,
    
    -- Link to the user who uploaded or initiated the ingestion
    uploaded_by_user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    
    ingested_at TIMESTAMPTZ DEFAULT NOW(), -- Timestamp of when the document was ingested
    content_updated_at TIMESTAMPTZ DEFAULT NOW(), -- Timestamp of when the source content was last known to be updated
                                             -- This might be different from ingested_at if re-ingesting existing content.
    processing_status TEXT DEFAULT 'pending', -- e.g., 'pending', 'processing', 'completed', 'failed'
    last_processed_at TIMESTAMPTZ,
    error_message TEXT -- If processing failed

    -- created_at and updated_at for the record itself (standard audit timestamps)
    -- Using ingested_at for the initial ingestion time.
    -- We'll use a separate trigger for a generic 'updated_at' for this record.
);

COMMENT ON TABLE ingested_documents IS 'Stores metadata and extracted content of ingested documents.';
COMMENT ON COLUMN ingested_documents.doc_id IS 'Primary Key, auto-generated UUID for the document record.';
COMMENT ON COLUMN ingested_documents.source_uri IS 'Unique URI or identifier for the source of the document.';
COMMENT ON COLUMN ingested_documents.doc_type IS 'Type of the document (e.g., markdown, pdf).';
COMMENT ON COLUMN ingested_documents.raw_content_ref IS 'Reference (e.g., path) to the raw content if stored separately.';
COMMENT ON COLUMN ingested_documents.extracted_text IS 'Plain text extracted from the document by processing flows.';
COMMENT ON COLUMN ingested_documents.doc_metadata IS 'Flexible JSONB field for additional document metadata.'; # Renamed
COMMENT ON COLUMN ingested_documents.space_id IS 'Foreign Key referencing the Spaces table, if applicable.';
COMMENT ON COLUMN ingested_documents.uploaded_by_user_id IS 'Foreign Key referencing the User who uploaded/initiated ingestion.';
COMMENT ON COLUMN ingested_documents.ingested_at IS 'Timestamp of when the document was first ingested.';
COMMENT ON COLUMN ingested_documents.content_updated_at IS 'Timestamp of when the source content was last updated (if known).';
COMMENT ON COLUMN ingested_documents.processing_status IS 'Current status of the document in the ingestion pipeline.';
COMMENT ON COLUMN ingested_documents.last_processed_at IS 'Timestamp of when the document was last successfully processed.';
COMMENT ON COLUMN ingested_documents.error_message IS 'Stores error messages if processing failed.';


-- Generic function to update 'updated_at' timestamp on any table that has such a column.
-- This was defined in user_management_schema.sql, ensure it's created once.
-- If it might not exist, define it here, otherwise, this is redundant.
-- CREATE OR REPLACE FUNCTION trigger_set_timestamp()
-- RETURNS TRIGGER AS $$
-- BEGIN
--   NEW.updated_at = NOW();
--   RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql;

-- Assuming a generic 'updated_at' column might be added for record modification time,
-- distinct from content_updated_at or ingested_at. If so:
-- ALTER TABLE ingested_documents ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
-- CREATE TRIGGER set_ingested_documents_updated_at_timestamp
-- BEFORE UPDATE ON ingested_documents
-- FOR EACH ROW
-- EXECUTE FUNCTION trigger_set_timestamp(); 
-- For now, this is commented out as the schema focuses on ingestion-specific timestamps.
-- If general record update timestamp is needed, it can be added.

-- Indexes for faster queries
CREATE INDEX idx_ingested_documents_doc_type ON ingested_documents(doc_type);
CREATE INDEX idx_ingested_documents_space_id ON ingested_documents(space_id);
CREATE INDEX idx_ingested_documents_uploaded_by_user_id ON ingested_documents(uploaded_by_user_id);
CREATE INDEX idx_ingested_documents_processing_status ON ingested_documents(processing_status);

-- Consider a GIN index on doc_metadata if you plan to query JSONB fields frequently
CREATE INDEX idx_ingested_documents_doc_metadata_gin ON ingested_documents USING GIN (doc_metadata); # Renamed

-- Consider a full-text search index on extracted_text
-- CREATE INDEX idx_ingested_documents_fts ON ingested_documents USING GIN (to_tsvector('english', extracted_text));


-- Document Chunks Table: Stores chunks of text from ingested documents and their embeddings.
-- Assumes pgvector extension is enabled. Default embedding dimension: 384
CREATE TABLE document_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id UUID NOT NULL REFERENCES ingested_documents(doc_id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(384), -- Example dimension, adjust as needed
    chunk_order INTEGER NOT NULL, -- To maintain the order of chunks within a document
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE document_chunks IS 'Stores text chunks of documents and their vector embeddings.';
COMMENT ON COLUMN document_chunks.chunk_id IS 'Primary Key, auto-generated UUID for the chunk.';
COMMENT ON COLUMN document_chunks.doc_id IS 'Foreign Key referencing the parent ingested document.';
COMMENT ON COLUMN document_chunks.chunk_text IS 'The actual text content of the chunk.';
COMMENT ON COLUMN document_chunks.embedding IS 'Vector embedding of the chunk_text. Dimension depends on the model used (e.g., 384 for all-MiniLM-L6-v2).';
COMMENT ON COLUMN document_chunks.chunk_order IS 'Order of this chunk within the parent document.';
COMMENT ON COLUMN document_chunks.created_at IS 'Timestamp of when the chunk record was created.';
COMMENT ON COLUMN document_chunks.updated_at IS 'Timestamp of when the chunk record was last updated.';

-- Index for faster lookup of chunks by document
CREATE INDEX idx_document_chunks_doc_id ON document_chunks(doc_id);

-- Index for vector similarity search (using HNSW or IVFFlat)
-- Example using HNSW, assuming L2 distance for embeddings.
-- The choice of index and parameters depends on dataset size, query patterns, and performance requirements.
-- CREATE INDEX idx_document_chunks_embedding_hnsw ON document_chunks USING hnsw (embedding vector_l2_ops);
-- Or using IVFFlat:
-- CREATE INDEX idx_document_chunks_embedding_ivfflat ON document_chunks USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
-- For now, commented out as specific indexing strategy might vary. User should add based on needs.


-- Trigger for `updated_at` on `document_chunks`
-- Ensure the trigger function `trigger_set_timestamp()` is defined (likely from user_management_schema.sql or earlier in this file)
CREATE TRIGGER set_document_chunks_updated_at_timestamp
BEFORE UPDATE ON document_chunks
FOR EACH ROW
EXECUTE FUNCTION trigger_set_timestamp(); -- Ensure this function exists

-- End of Data Storage Schema
