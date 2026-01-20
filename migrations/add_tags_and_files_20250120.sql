-- Migration: Add tags, product_line, file paths, and completion tracking
-- Date: 2025-01-20
-- Description: Adds new fields for tagging, grouping, file uploads, and wizard completion tracking

-- Note: For SQLite, we need to handle the migration carefully
-- This script is for reference. SQLAlchemy will auto-create these columns on startup.

-- If you need to apply this manually to an existing database:

ALTER TABLE skus ADD COLUMN tags TEXT;  -- JSON field
ALTER TABLE skus ADD COLUMN product_line VARCHAR(255);
ALTER TABLE skus ADD COLUMN bom_file_path VARCHAR(500);
ALTER TABLE skus ADD COLUMN artwork_file_path VARCHAR(500);
ALTER TABLE skus ADD COLUMN completion_status TEXT;  -- JSON field
ALTER TABLE skus ADD COLUMN completion_percentage INTEGER DEFAULT 0;

-- Note: SQLite doesn't support ALTER TABLE for adding NOT NULL columns with defaults easily
-- The above columns are all nullable or have defaults, so this should work

-- Alternatively, if you encounter issues, the app will auto-migrate on startup
-- since we use Base.metadata.create_all() in init_db()
