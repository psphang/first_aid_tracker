"""
Database module for PostgreSQL connectivity and utilities
Handles async database operations with connection pooling
"""

import asyncpg
import os
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timezone

# Get database URL from environment or use default
raw_db_url = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
if raw_db_url:
    # Redact password for logging
    if "@" in raw_db_url:
        parts = raw_db_url.split("@")
        user_info = parts[0].split("://")[1].split(":")[0]
        host_info = parts[1]
        print(f"[DEBUG] Connecting to database: postgresql://{user_info}:****@{host_info}")
    else:
        print("[DEBUG] Connecting to database (URL structure not as expected)")

    if "sslmode" not in raw_db_url:
        # Ensure sslmode=require for Neon PostgreSQL
        if "?" in raw_db_url:
            DATABASE_URL = f"{raw_db_url}&sslmode=require"
        else:
            DATABASE_URL = f"{raw_db_url}?sslmode=require"
    else:
        DATABASE_URL = raw_db_url
else:
    print("[!] No DATABASE_URL or NEON_DATABASE_URL found.")
    DATABASE_URL = None

class DatabasePool:
    """Manages PostgreSQL connection pool for the application."""
    
    _pool: Optional[asyncpg.Pool] = None
    _initialized: bool = False
    
    @classmethod
    async def initialize(cls):
        """Initialize the connection pool."""
        if cls._initialized:
            return
        
        if not DATABASE_URL:
            print("[!] DATABASE_URL not set. Database features disabled.")
            cls._initialized = True
            return

        try:
            # Optimize pool size for serverless environment to prevent Neon connection exhaustion
            cls._pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=1,
                max_size=2,
                command_timeout=60
            )
            cls._initialized = True
            print("[✓] Database pool initialized")
        except Exception as e:
            print(f"[!] Database connection failed: {e}")
            cls._initialized = True # Prevent repeated attempts
    
    @classmethod
    async def close(cls):
        """Close the connection pool."""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            cls._initialized = False
            print("[✓] Database pool closed")
    
    @classmethod
    async def get_connection(cls):
        """Get a connection from the pool."""
        if not cls._initialized:
            await cls.initialize()
            
        if cls._pool is None:
            # Return None to signal connection failure
            return None
        return cls._pool.acquire()


async def get_kit_id_by_name(conn, kit_id: str) -> Optional[str]:
    """Helper to find the canonical kit ID case-insensitively and ignoring whitespace, with exact match fallback."""
    clean_kit_id = kit_id.strip()
    
    # Debug: Log all kit IDs
    all_kits = await conn.fetch("SELECT kit_id FROM kits")
    kit_codes = [row['kit_id'] for row in all_kits]
    print(f"[DEBUG] Search for: '{clean_kit_id}'. Available kit codes in DB: {kit_codes}")

    # 1. Try case-insensitive matching
    row = await conn.fetchrow(
        "SELECT kit_id FROM kits WHERE LOWER(TRIM(kit_id)) = LOWER($1)",
        clean_kit_id
    )
    
    # 2. Fallback to exact raw match
    if not row:
        row = await conn.fetchrow(
            "SELECT kit_id FROM kits WHERE kit_id = $1",
            clean_kit_id
        )
        
    return row['kit_id'] if row else None

# Database query functions
async def get_kit_items(kit_id: str) -> Dict[str, Any]:
    """Get all items for a specific kit."""
    conn = await DatabasePool.get_connection()
    if not conn:
        print(f"[!] Database connection unavailable for get_kit_items")
        return {"items": {}, "last_edited": None, "canonical_id": kit_id, "warning": "Database offline"}

    async with conn:
        canonical_kit_id = await get_kit_id_by_name(conn, kit_id)
        if not canonical_kit_id:
             return {"items": {}, "last_edited": None, "canonical_id": kit_id}
             
        items = await conn.fetch(
            """
            SELECT 
                id, kit_id, name, item_no, expiry_date, qty,
                created_at, updated_at
            FROM kit_items
            WHERE kit_id = $1
            ORDER BY name
            """,
            canonical_kit_id
        )
        
        kit = await conn.fetchrow(
            "SELECT kit_id, last_edited FROM kits WHERE kit_id = $1",
            canonical_kit_id
        )
        
        # Get first aid item details
        item_details_list = await conn.fetch(
            """
            SELECT item_name, item_code, category, expiring
            FROM first_aid_items
            """
        )
        
        item_details_map = {
            item['item_name']: {
                'item_no': item['item_code'],
                'category': item['category'],
                'expiring': item['expiring']
            }
            for item in item_details_list
        }
        
        # Group items by category
        grouped_items = {}
        for item in items:
            details = item_details_map.get(item['name'], {})
            item_data = {
                'id': item['id'],
                'name': item['name'],
                'item_no': item['item_no'] or details.get('item_no', ''),
                'expiry_date': item['expiry_date'].isoformat() if item['expiry_date'] else None,
                'qty': item['qty'],
                'category': details.get('category', 'Uncategorized'),
                'Expiring': details.get('expiring', 'No'),
                'updated_at': (item['updated_at'] or item['created_at']).isoformat() if (item['updated_at'] or item['created_at']) else None,
            }
            
            category = item_data['category']
            if category not in grouped_items:
                grouped_items[category] = []
            grouped_items[category].append(item_data)
        
        return {
            "items": grouped_items,
            "last_edited": kit['last_edited'].isoformat() if kit['last_edited'] else None,
            "canonical_id": canonical_kit_id
        }


async def add_item_to_kit(kit_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add an item to a kit."""
    conn = await DatabasePool.get_connection()
    if not conn:
        raise Exception("Database offline")
    async with conn:
        async with conn.transaction():
            canonical_kit_id = await get_kit_id_by_name(conn, kit_id)
            if not canonical_kit_id:
                canonical_kit_id = kit_id
                # Ensure kit exists
                await conn.execute(
                    """
                    INSERT INTO kits (kit_id)
                    VALUES ($1)
                    ON CONFLICT (kit_id) DO NOTHING
                    """,
                    canonical_kit_id
                )
            
            # Parse expiry_date string to date object for PostgreSQL
            expiry_date = item_data.get('expiry_date')
            if expiry_date and isinstance(expiry_date, str):
                expiry_date = date.fromisoformat(expiry_date)
            
            # Add item
            await conn.execute(
                """
                INSERT INTO kit_items
                (id, kit_id, name, item_no, expiry_date, qty)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                item_data['id'],
                canonical_kit_id,
                item_data['name'],
                item_data.get('item_no'),
                expiry_date,
                item_data['qty']
            )
            
            # Update kit's last_edited timestamp
            await conn.execute(
                """
                UPDATE kits
                SET last_edited = $1
                WHERE kit_id = $2
                """,
                datetime.now(timezone.utc),
                canonical_kit_id
            )
    
    return item_data


async def update_item_quantity(kit_id: str, item_id: str, qty: int) -> bool:
    """Update an item's quantity."""
    conn = await DatabasePool.get_connection()
    if not conn:
        raise Exception("Database offline")
    async with conn:
        canonical_kit_id = await get_kit_id_by_name(conn, kit_id)
        if not canonical_kit_id:
             raise Exception("Kit not found")
        async with conn.transaction():
            result = await conn.execute(
                """
                UPDATE kit_items
                SET qty = $1, updated_at = $2
                WHERE id = $3 AND kit_id = $4
                """,
                qty,
                datetime.now(timezone.utc),
                item_id,
                canonical_kit_id
            )
            
            # Update kit's last_edited timestamp
            await conn.execute(
                """
                UPDATE kits
                SET last_edited = $1
                WHERE kit_id = $2
                """,
                datetime.now(timezone.utc),
                canonical_kit_id
            )
    
    return True


async def remove_item_from_kit(kit_id: str, item_id: str) -> bool:
    """Remove an item from a kit."""
    conn = await DatabasePool.get_connection()
    if not conn:
        raise Exception("Database offline")
    async with conn:
        canonical_kit_id = await get_kit_id_by_name(conn, kit_id)
        if not canonical_kit_id:
             raise Exception("Kit not found")
        async with conn.transaction():
            await conn.execute(
                """
                DELETE FROM kit_items
                WHERE id = $1 AND kit_id = $2
                """,
                item_id,
                canonical_kit_id
            )
            
            # Update kit's last_edited timestamp
            await conn.execute(
                """
                UPDATE kits
                SET last_edited = $1
                WHERE kit_id = $2
                """,
                datetime.now(timezone.utc),
                canonical_kit_id
            )
    
    return True


async def get_all_first_aid_items() -> Dict[str, List[Dict[str, Any]]]:
    """Get all first aid items grouped by category."""
    conn = await DatabasePool.get_connection()
    if not conn:
        return {"Uncategorized": [{"No": "0", "Item#": "", "Item": "Database offline", "category": "Uncategorized", "Expiring": "No"}]}
    
    async with conn:
        items = await conn.fetch(
            """
            SELECT id, item_no, item_name, item_code, category, expiring
            FROM first_aid_items
            ORDER BY category, item_no
            """
        )
        
        grouped = {}
        for item in items:
            category = item['category'] or 'Uncategorized'
            if category not in grouped:
                grouped[category] = []
            
            grouped[category].append({
                'No': str(item['id']),
                'Item#': item['item_code'] or '',
                'Item': item['item_name'],
                'category': category,
                'Expiring': item['expiring'] or 'No'
            })
        
        return grouped


async def add_first_aid_item(item_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new first aid item."""
    conn = await DatabasePool.get_connection()
    if not conn:
        raise Exception("Database offline")
    async with conn:
        # Get next item_no
        max_no = await conn.fetchval(
            "SELECT MAX(item_no) FROM first_aid_items"
        ) or 0
        next_no = max_no + 1
        
        result = await conn.fetchrow(
            """
            INSERT INTO first_aid_items
            (item_no, item_name, item_code, category, expiring, last_edited)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, item_no, item_name, item_code, category, expiring
            """,
            next_no,
            item_data['Item'],
            item_data.get('Item#', ''),
            item_data.get('category', 'Uncategorized'),
            item_data.get('Expiring', 'No'),
            datetime.now(timezone.utc)
        )
        
        return dict(result)


async def update_first_aid_item(item_name: str, item_data: Dict[str, Any]) -> bool:
    """Update a first aid item."""
    conn = await DatabasePool.get_connection()
    if not conn:
        raise Exception("Database offline")
    async with conn:
        result = await conn.execute(
            """
            UPDATE first_aid_items
            SET 
                item_name = $1,
                item_code = $2,
                category = $3,
                expiring = $4,
                last_edited = $5
            WHERE item_name = $6
            """,
            item_data.get('Item', item_name),
            item_data.get('Item#', ''),
            item_data.get('category', 'Uncategorized'),
            item_data.get('Expiring', 'No'),
            datetime.now(timezone.utc),
            item_name
        )
    
    return True


async def delete_first_aid_item(item_name: str) -> bool:
    """Delete a first aid item."""
    conn = await DatabasePool.get_connection()
    if not conn:
        raise Exception("Database offline")
    async with conn:
        await conn.execute(
            "DELETE FROM first_aid_items WHERE item_name = $1",
            item_name
        )
    
    return True


async def get_all_items_across_kits() -> Dict[str, List[Dict[str, Any]]]:
    """Get all items across all kits, grouped by category."""
    conn = await DatabasePool.get_connection()
    if not conn:
        return {"Uncategorized": [{"name": "Database offline"}]}
    
    async with conn:
        items = await conn.fetch(
            """
            SELECT 
                ki.id, ki.kit_id, ki.name, ki.item_no, ki.expiry_date, ki.qty,
                fai.category, fai.expiring
            FROM kit_items ki
            LEFT JOIN first_aid_items fai ON ki.name = fai.item_name
            ORDER BY fai.category, ki.name
            """
        )
        
        grouped = {}
        for item in items:
            category = item['category'] or 'Uncategorized'
            if category not in grouped:
                grouped[category] = []
            
            grouped[category].append({
                'id': item['id'],
                'kit_id': item['kit_id'],
                'name': item['name'],
                'item_no': item['item_no'] or '',
                'expiry_date': item['expiry_date'].isoformat() if item['expiry_date'] else None,
                'qty': item['qty'],
                'category': category,
                'Expiring': item['expiring'] or 'No'
            })
        
        return grouped
