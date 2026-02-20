-- Run this file as postgres superuser to grant permissions to cms_user
-- Command: psql -U postgres -h localhost -p 5432 -d cms_db -f grant_permissions.sql

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO cms_user;

-- Grant permissions on existing tables and sequences
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cms_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cms_user;

-- Grant permissions on future tables and sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO cms_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO cms_user;

-- Verify permissions
\du cms_user
