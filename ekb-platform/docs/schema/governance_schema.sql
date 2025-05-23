-- Governance Schema for EKB Platform (PostgreSQL)

-- Ensure UUID generation is enabled (if not already from user_management_schema.sql or data_storage_schema.sql)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Audit Logs Table: Records significant actions performed within the system for audit and governance purposes.
CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    "timestamp" TIMESTAMPTZ DEFAULT NOW() NOT NULL, -- Using quotes for "timestamp" as it's a keyword
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL, -- Nullable for system actions
    username TEXT, -- Denormalized username for easier log review, even if user is deleted/changed
    action TEXT NOT NULL, -- e.g., 'USER_LOGIN', 'DOCUMENT_INGEST', 'SEARCH_PERFORMED'
    details JSONB, -- Context-specific details, e.g., {'doc_id': '...', 'query': '...'}
    ip_address TEXT, -- IP address of the client performing the action
    success BOOLEAN -- Whether the action was successful or not (e.g., successful login vs. failed login attempt)
);

COMMENT ON TABLE audit_logs IS 'Records significant actions performed within the system for audit and governance.';
COMMENT ON COLUMN audit_logs.log_id IS 'Primary Key, auto-generated UUID for the log entry.';
COMMENT ON COLUMN audit_logs."timestamp" IS 'Timestamp of when the action occurred (auto-generated).';
COMMENT ON COLUMN audit_logs.user_id IS 'Foreign Key referencing the Users table, if action is user-initiated.';
COMMENT ON COLUMN audit_logs.username IS 'Username at the time of the action (denormalized).';
COMMENT ON COLUMN audit_logs.action IS 'Identifier for the type of action performed (e.g., USER_LOGIN, DOCUMENT_VIEW).';
COMMENT ON COLUMN audit_logs.details IS 'JSONB field for storing context-specific information about the event.';
COMMENT ON COLUMN audit_logs.ip_address IS 'IP address from which the action originated, if available.';
COMMENT ON COLUMN audit_logs.success IS 'Flag indicating if the action was successful (true), failed (false), or not applicable (NULL).';

-- Indexes for faster querying of audit logs
CREATE INDEX idx_audit_logs_timestamp ON audit_logs("timestamp");
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);

-- Note: The `updated_at` column is generally not needed for audit logs as they are typically immutable.
-- If specific log entries need to be "updated" (e.g., to add more details discovered later, though not standard practice),
-- then an `updated_at` column with a trigger could be considered. For now, omitted for immutability.

-- End of Governance Schema
