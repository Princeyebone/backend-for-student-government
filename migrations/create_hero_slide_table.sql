-- Create hero_slide table for slideshow functionality
CREATE TABLE IF NOT EXISTS heroslide (
    id SERIAL PRIMARY KEY,
    image_url VARCHAR NOT NULL,
    image_public_id VARCHAR NOT NULL,
    caption TEXT,
    order_index INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR NOT NULL,
    updated_at TIMESTAMP,
    updated_by VARCHAR
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_heroslide_order ON heroslide(order_index);
CREATE INDEX IF NOT EXISTS idx_heroslide_active ON heroslide(is_active);
CREATE INDEX IF NOT EXISTS idx_heroslide_created_at ON heroslide(created_at);