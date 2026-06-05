# JSON to SQL Migration Guide

## Overview
This guide walks you through migrating your First Aid Tracker from JSON file storage to PostgreSQL with Neon.tech.

## Prerequisites
- Python 3.8+
- PostgreSQL connection URL from Neon.tech (provided: `postgresql://neondb_owner:npg_p4lbiRzPfCL9@ep-proud-bird-aqn2uuie-pooler.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require`)
- Git repository with current code

## Migration Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements_sql.txt
```

### Step 2: Run Migration Script
The migration script will:
1. Create backups of your JSON files
2. Connect to PostgreSQL
3. Create database schema
4. Migrate existing data from JSON to SQL
5. Verify the migration

```bash
python migrate_to_sql.py
```

**Expected Output:**
```
============================================================
First Aid Tracker: JSON to SQL Migration
============================================================

[*] Creating backups...
[✓] Backed up first_aid_kit.json to backups/first_aid_kit.json.20260605_143000.backup
[✓] Backed up firstIAiditem.json to backups/firstIAiditem.json.20260605_143000.backup

[*] Creating database connection...
[✓] Connected to PostgreSQL database

[*] Creating database schema...
[✓] Schema created successfully

[*] Migrating first aid items...
[✓] Migrated 15 first aid items

[*] Migrating kits and items...
[✓] Migrated 2 kits and 45 items

[*] Verifying migration...
[✓] Database contains:
    - 2 kits
    - 45 kit items
    - 15 first aid items
[✓] Migration verified successfully!

============================================================
```

### Step 3: Update Environment Variables
Add to your `.env` or Render.com environment variables:
```
DATABASE_URL=postgresql://neondb_owner:npg_p4lbiRzPfCL9@ep-proud-bird-aqn2uuie-pooler.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

### Step 4: Deploy Updated Code
```bash
git add .
git commit -m "Migrate from JSON to PostgreSQL"
git push origin master
```

Render.com will automatically:
1. Pull the latest code
2. Install dependencies from `requirements.txt`
3. Restart the application

## Database Schema

### Tables

#### `kits` table
```sql
CREATE TABLE kits (
    kit_id VARCHAR(255) PRIMARY KEY,
    last_edited TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE
);
```

#### `kit_items` table
```sql
CREATE TABLE kit_items (
    id VARCHAR(255) PRIMARY KEY,
    kit_id VARCHAR(255) REFERENCES kits(kit_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    item_no VARCHAR(50),
    expiry_date DATE,
    qty INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

#### `first_aid_items` table (Master list)
```sql
CREATE TABLE first_aid_items (
    id SERIAL PRIMARY KEY,
    item_no INTEGER NOT NULL,
    item_name VARCHAR(255) NOT NULL UNIQUE,
    item_code VARCHAR(50),
    category VARCHAR(100) DEFAULT 'Uncategorized',
    expiring VARCHAR(10) DEFAULT 'No',
    last_edited TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE
);
```

## Rollback Plan

If issues occur during migration:

1. **Stop the application** on Render.com
2. **Restore from backups** in the `backups/` directory
3. **Revert to previous code** on GitHub
4. **Contact support** for database issues

Backup files are stored with timestamps:
```
backups/
├── first_aid_kit.json.20260605_143000.backup
└── firstIAiditem.json.20260605_143000.backup
```

## Monitoring

After deployment, monitor:
- Render.com deployment logs
- Application error logs
- Database connection status

## API Changes

The API endpoints remain the same for the frontend. The underlying data storage has changed:
- Before: `first_aid_kit.json` and `firstIAiditem.json`
- After: PostgreSQL tables via `db.py` module

## Troubleshooting

### Connection Error
```
postgresql.exceptions.InvalidCatalogNameError
```
**Solution:** Verify DATABASE_URL in environment variables

### Migration Incomplete
```
Warning: Some tables are empty
```
**Solution:** Check backup files in `backups/` directory and verify JSON files were present before migration

### Slow Queries
**Solution:** Wait for connection pooling to stabilize. Initial queries may be slower during pool initialization.

## Next Steps

1. ✅ Test all features on staging
2. ✅ Verify all kits load correctly
3. ✅ Test adding/removing items
4. ✅ Monitor production logs
5. ✅ Keep backups for 30 days

## Support

For issues, check:
- `migrate_to_sql.py` output for migration details
- Application logs on Render.com
- PostgreSQL connection in Neon dashboard
