-- Fix PostgreSQL permissions for cms_user
-- Run as postgres superuser: psql -U postgres -d cms_db -f fix_permissions.sql

-- Grant database connection and creation privileges
GRANT ALL PRIVILEGES ON DATABASE cms_db TO cms_user;

-- Grant schema usage and creation
GRANT ALL ON SCHEMA public TO cms_user;
GRANT CREATE ON SCHEMA public TO cms_user;
GRANT USAGE ON SCHEMA public TO cms_user;

-- Grant privileges on all existing tables and sequences
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cms_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cms_user;

-- Set cms_user as owner of the public schema (this is the key fix!)
ALTER SCHEMA public OWNER TO cms_user;

-- Alternative: Set default privileges for postgres user creating objects
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO cms_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO cms_user;

-- Verify
\du cms_user
\dn+ public
