-- Migration: create_bills_table
-- Run this manually if the database already exists and auto-migration is not being used.
-- If the app starts fresh, SQLModel.metadata.create_all() handles this automatically.

CREATE TYPE bill_category AS ENUM (
    'Welfare',
    'Academic',
    'Finance',
    'Infrastructure',
    'Events',
    'Constitutional'
);

CREATE TYPE bill_status AS ENUM (
    'Draft',
    'Under Review',
    'Voting',
    'Approved',
    'Rejected'
);

CREATE TABLE IF NOT EXISTS bill (
    id              SERIAL PRIMARY KEY,
    title           TEXT        NOT NULL,
    description     TEXT        NOT NULL,
    category        TEXT        NOT NULL,   -- stored as string; enum enforced at app layer
    status          TEXT        NOT NULL DEFAULT 'Draft',
    sponsor         TEXT        NOT NULL,
    date_proposed   DATE        NOT NULL,

    votes_for       INTEGER,
    votes_against   INTEGER,
    abstain         INTEGER,
    total_senators  INTEGER,

    documents       JSONB,                  -- [{"name": "...", "url": "..."}]
    timeline        JSONB       NOT NULL DEFAULT '[]',  -- [{"label": "...", "date": "..."}]

    created_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    created_by      TEXT        NOT NULL,
    updated_by      TEXT        NOT NULL
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_bill_status   ON bill (status);
CREATE INDEX IF NOT EXISTS idx_bill_category ON bill (category);
CREATE INDEX IF NOT EXISTS idx_bill_sponsor  ON bill (sponsor);
CREATE INDEX IF NOT EXISTS idx_bill_date     ON bill (date_proposed DESC);
