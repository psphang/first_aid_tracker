-- First Aid Tracker Database Schema
-- PostgreSQL with Neon

-- Create tables
CREATE TABLE IF NOT EXISTS kits (
    kit_id VARCHAR(255) PRIMARY KEY,
    last_edited TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kit_items (
    id VARCHAR(255) PRIMARY KEY,
    kit_id VARCHAR(255) NOT NULL REFERENCES kits(kit_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    item_no VARCHAR(50),
    expiry_date DATE,
    qty INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (kit_id) REFERENCES kits(kit_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS first_aid_items (
    id SERIAL PRIMARY KEY,
    item_no INTEGER NOT NULL,
    item_name VARCHAR(255) NOT NULL UNIQUE,
    item_code VARCHAR(50),
    category VARCHAR(100) DEFAULT 'Uncategorized',
    expiring VARCHAR(10) DEFAULT 'No',
    last_edited TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_kit_items_kit_id ON kit_items(kit_id);
CREATE INDEX IF NOT EXISTS idx_kit_items_name ON kit_items(name);
CREATE INDEX IF NOT EXISTS idx_first_aid_items_name ON first_aid_items(item_name);
CREATE INDEX IF NOT EXISTS idx_first_aid_items_category ON first_aid_items(category);
CREATE INDEX IF NOT EXISTS idx_kits_last_edited ON kits(last_edited);

-- Add comments for documentation
COMMENT ON TABLE kits IS 'Stores first aid kit boxes with metadata';
COMMENT ON TABLE kit_items IS 'Stores items within each kit';
COMMENT ON TABLE first_aid_items IS 'Master list of all first aid items with categories and properties';
COMMENT ON COLUMN first_aid_items.expiring IS 'Flag indicating if item tracks expiry dates (Yes/No)';
