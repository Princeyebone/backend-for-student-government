-- Step 1: Disconnect all users from the database
-- Run as postgres superuser: psql -U postgres

-- Terminate all connections to cms_db
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'cms_db'
  AND pid <> pg_backend_pid();

-- Step 2: Drop the database
DROP DATABASE IF EXISTS cms_db;

-- Step 3: Drop and recreate the user (optional, for clean slate)
DROP USER IF EXISTS cms_user;
CREATE USER cms_user WITH PASSWORD '0264442031Qq.';

-- Step 4: Create the database with cms_user as owner
CREATE DATABASE cms_db OWNER cms_user;

-- Step 5: Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE cms_db TO cms_user;

-- Step 6: Connect to the new database
\c cms_db

-- Step 7: Grant schema permissions (run after connecting to cms_db)
GRANT ALL ON SCHEMA public TO cms_user;
ALTER SCHEMA public OWNER TO cms_user;

-- Verify
\l cms_db
\du cms_user
