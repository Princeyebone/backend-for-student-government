-- Add updated_at column to gallary table
ALTER TABLE gallary ADD COLUMN updated_at TIMESTAMP;

-- Set existing records to have updated_at = created_at
UPDATE gallary SET updated_at = created_at WHERE updated_at IS NULL;