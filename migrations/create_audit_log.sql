-- Create audit_log table
CREATE TABLE IF NOT EXISTS auditlog (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES "user"(id),
    user_email VARCHAR NOT NULL,
    user_role VARCHAR NOT NULL,
    action VARCHAR NOT NULL,
    resource VARCHAR,
    resource_id VARCHAR,
    details TEXT,
    ip_address VARCHAR,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_auditlog_user_id ON auditlog(user_id);
CREATE INDEX IF NOT EXISTS idx_auditlog_user_email ON auditlog(user_email);
CREATE INDEX IF NOT EXISTS idx_auditlog_user_role ON auditlog(user_role);
CREATE INDEX IF NOT EXISTS idx_auditlog_action ON auditlog(action);
CREATE INDEX IF NOT EXISTS idx_auditlog_timestamp ON auditlog(timestamp);
