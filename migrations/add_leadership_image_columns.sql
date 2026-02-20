-- Add missing image columns to leadership table
ALTER TABLE leadership ADD COLUMN IF NOT EXISTS image VARCHAR;
ALTER TABLE leadership ADD COLUMN IF NOT EXISTS image_public_id VARCHAR;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_leadership_image ON leadership(image);
CREATE INDEX IF NOT EXISTS idx_leadership_image_public_id ON leadership(image_public_id);