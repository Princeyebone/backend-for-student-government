-- Add updated_at column to news table
ALTER TABLE news ADD COLUMN updated_at TIMESTAMP;

-- Set existing records to have updated_at = created_at
UPDATE news SET updated_at = created_at WHERE updated_at IS NULL;