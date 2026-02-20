-- Add updated_at column to news table
ALTER TABLE news 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;

-- Add updated_at column to gallary table  
ALTER TABLE gallary 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;

-- Add updated_at column to leadership table
ALTER TABLE leadership 
ADD COLUMN IF NOT EXISTS update_at TIMESTAMP;

-- Note: The model uses 'update_at' for leadership but 'updated_at' for others
-- This maintains consistency with existing model definitions