#!/usr/bin/env python3
"""
Migration Script: Convert JSON data to PostgreSQL
This script reads existing JSON files and migrates them to SQL database.
Preserves original JSON files as backup.
"""

import json
import os
import sys
import asyncio
import asyncpg
from datetime import datetime
from pathlib import Path
import shutil

# Database connection string
DATABASE_URL = "postgresql://neondb_owner:npg_p4lbiRzPfCL9@ep-proud-bird-aqn2uuie-pooler.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# JSON files
DATA_FILE = "first_aid_kit.json"
ITEMS_FILE = "firstIAiditem.json"
BACKUP_DIR = "backups"


def create_backup():
    """Create backup of JSON files before migration."""
    print("[*] Creating backups...")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if os.path.exists(DATA_FILE):
        backup_path = os.path.join(BACKUP_DIR, f"{DATA_FILE}.{timestamp}.backup")
        shutil.copy2(DATA_FILE, backup_path)
        print(f"[✓] Backed up {DATA_FILE} to {backup_path}")
    
    if os.path.exists(ITEMS_FILE):
        backup_path = os.path.join(BACKUP_DIR, f"{ITEMS_FILE}.{timestamp}.backup")
        shutil.copy2(ITEMS_FILE, backup_path)
        print(f"[✓] Backed up {ITEMS_FILE} to {backup_path}")


async def get_db_connection():
    """Establish database connection."""
    try:
        # Extract connection parameters from URL
        conn = await asyncpg.connect(DATABASE_URL)
        print("[✓] Connected to PostgreSQL database")
        return conn
    except Exception as e:
        print(f"[✗] Failed to connect to database: {e}")
        sys.exit(1)


async def create_schema(conn):
    """Create database schema."""
    print("[*] Creating database schema...")
    
    schema_sql = """
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
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
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

    CREATE INDEX IF NOT EXISTS idx_kit_items_kit_id ON kit_items(kit_id);
    CREATE INDEX IF NOT EXISTS idx_kit_items_name ON kit_items(name);
    CREATE INDEX IF NOT EXISTS idx_first_aid_items_name ON first_aid_items(item_name);
    CREATE INDEX IF NOT EXISTS idx_first_aid_items_category ON first_aid_items(category);
    """
    
    try:
        await conn.execute(schema_sql)
        print("[✓] Schema created successfully")
    except Exception as e:
        print(f"[✗] Error creating schema: {e}")
        sys.exit(1)


async def migrate_first_aid_items(conn):
    """Migrate first_aid_items from JSON to SQL."""
    print("[*] Migrating first aid items...")
    
    if not os.path.exists(ITEMS_FILE):
        print("[!] No items file found, skipping...")
        return
    
    try:
        with open(ITEMS_FILE, 'r') as f:
            data = json.load(f)
        
        items = data.get('items', [])
        migrated = 0
        
        for item in items:
            try:
                item_no = int(item.get('No', 0))
                item_name = item.get('Item', '')
                item_code = item.get('Item#', '')
                category = item.get('category', 'Uncategorized')
                expiring = item.get('Expiring', 'No')
                
                # Check if item already exists
                existing = await conn.fetchval(
                    "SELECT id FROM first_aid_items WHERE item_name = $1",
                    item_name
                )
                
                if not existing:
                    await conn.execute(
                        """
                        INSERT INTO first_aid_items 
                        (item_no, item_name, item_code, category, expiring)
                        VALUES ($1, $2, $3, $4, $5)
                        """,
                        item_no, item_name, item_code, category, expiring
                    )
                    migrated += 1
            except Exception as e:
                print(f"[!] Error migrating item '{item.get('Item', 'Unknown')}': {e}")
                continue
        
        print(f"[✓] Migrated {migrated} first aid items")
    
    except Exception as e:
        print(f"[✗] Error reading items file: {e}")
        sys.exit(1)


async def migrate_kits_and_items(conn):
    """Migrate kits and kit items from JSON to SQL."""
    print("[*] Migrating kits and items...")
    
    if not os.path.exists(DATA_FILE):
        print("[!] No kits file found, skipping...")
        return
    
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        
        kits_migrated = 0
        items_migrated = 0
        
        for kit_id, kit_data in data.items():
            try:
                # Skip if not a kit structure
                if not isinstance(kit_data, dict) or 'items' not in kit_data:
                    continue
                
                last_edited_str = kit_data.get('last_edited')
                last_edited = None
                if last_edited_str:
                    try:
                        last_edited = datetime.fromisoformat(last_edited_str)
                    except ValueError:
                        pass
                
                # Insert or update kit
                await conn.execute(
                    """
                    INSERT INTO kits (kit_id, last_edited)
                    VALUES ($1, $2)
                    ON CONFLICT (kit_id) DO UPDATE SET last_edited = $2
                    """,
                    kit_id, last_edited
                )
                kits_migrated += 1
                
                # Migrate items in the kit
                for item in kit_data.get('items', []):
                    try:
                        item_id = item.get('id', f'item-{datetime.now().timestamp()}')
                        name = item.get('name', '')
                        item_no = item.get('item_no', '')
                        expiry_date_str = item.get('expiry_date')
                        qty = item.get('qty', 0)
                        
                        expiry_date = None
                        if expiry_date_str and expiry_date_str != '':
                            try:
                                expiry_date = datetime.fromisoformat(expiry_date_str).date()
                            except ValueError:
                                try:
                                    from datetime import date
                                    expiry_date = date.fromisoformat(expiry_date_str)
                                except ValueError:
                                    expiry_date = None
                        
                        await conn.execute(
                            """
                            INSERT INTO kit_items 
                            (id, kit_id, name, item_no, expiry_date, qty)
                            VALUES ($1, $2, $3, $4, $5, $6)
                            ON CONFLICT (id) DO UPDATE SET 
                                qty = $6, updated_at = CURRENT_TIMESTAMP
                            """,
                            item_id, kit_id, name, item_no, expiry_date, qty
                        )
                        items_migrated += 1
                    except Exception as e:
                        print(f"[!] Error migrating item in kit '{kit_id}': {e}")
                        continue
            
            except Exception as e:
                print(f"[!] Error migrating kit '{kit_id}': {e}")
                continue
        
        print(f"[✓] Migrated {kits_migrated} kits and {items_migrated} items")
    
    except Exception as e:
        print(f"[✗] Error reading kits file: {e}")
        sys.exit(1)


async def verify_migration(conn):
    """Verify migration by counting records in database."""
    print("[*] Verifying migration...")
    
    try:
        kits_count = await conn.fetchval("SELECT COUNT(*) FROM kits")
        items_count = await conn.fetchval("SELECT COUNT(*) FROM kit_items")
        first_aid_count = await conn.fetchval("SELECT COUNT(*) FROM first_aid_items")
        
        print(f"[✓] Database contains:")
        print(f"    - {kits_count} kits")
        print(f"    - {items_count} kit items")
        print(f"    - {first_aid_count} first aid items")
        
        if kits_count > 0 and items_count > 0 and first_aid_count > 0:
            print("[✓] Migration verified successfully!")
            return True
        else:
            print("[!] Warning: Some tables are empty")
            return False
    
    except Exception as e:
        print(f"[✗] Error verifying migration: {e}")
        return False


async def main():
    """Main migration function."""
    print("=" * 60)
    print("First Aid Tracker: JSON to PostgreSQL Migration")
    print("=" * 60)
    print()
    
    # Create backups
    create_backup()
    print()
    
    # Connect to database
    conn = await get_db_connection()
    
    try:
        # Create schema
        await create_schema(conn)
        print()
        
        # Migrate data
        await migrate_first_aid_items(conn)
        await migrate_kits_and_items(conn)
        print()
        
        # Verify
        success = await verify_migration(conn)
        print()
        
        if success:
            print("[✓] Migration completed successfully!")
            print("[*] JSON files have been backed up in the 'backups' directory")
            print("[*] You can now deploy the updated code to production")
        else:
            print("[!] Migration completed with warnings. Please review.")
        
    finally:
        await conn.close()
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
