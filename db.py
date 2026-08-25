"""
Database module for PostgreSQL connectivity and utilities
Handles async database operations with connection pooling
"""

import asyncpg
import os
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timezone

# Get database URL from environment or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_p4lbiRzPfCL9@ep-proud-bird-aqn2uuie-pooler.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)

class DatabasePool:
    """Manages PostgreSQL connection pool for the application."""
    
    _pool: Optional[asyncpg.Pool] = None
    
    @classmethod
    async def initialize(cls):
        """Initialize the connection pool."""
        if cls._pool is None:
            # Optimize pool size for serverless environment to prevent Neon connection exhaustion
            cls._pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=1,
                max_size=2,
                command_timeout=60
            )
            print("[✓] Database pool initialized")
    
    @classmethod
    async def close(cls):
        """Close the connection pool."""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            print("[✓] Database pool closed")
    
    @classmethod
    async def get_connection(cls):
        """Get a connection from the pool."""
        if cls._pool is None:
            await cls.initialize()
        return cls._pool.acquire()


# Database query functions
async def get_kit_items(kit_id: str) -> Dict[str, Any]:
    """Get all items for a specific kit."""
    async with await DatabasePool.get_connection() as conn:
        items = await conn.fetch(
            """
            SELECT 
                id, kit_id, name, item_no, expiry_date, qty,
                created_at, updated_at
            FROM kit_items
            WHERE kit_id = $1
            ORDER BY name
            """,
            kit_id
        )
        
        kit = await conn.fetchrow(
            "SELECT kit_id, last_edited FROM kits WHERE kit_id = $1",
            kit_id
        )
        
        if not kit:
            return {"items": [], "last_edited": None}
        
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
            "last_edited": kit['last_edited'].isoformat() if kit['last_edited'] else None
        }


async def add_item_to_kit(kit_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add an item to a kit."""
    async with await DatabasePool.get_connection() as conn:
        async with conn.transaction():
            # Ensure kit exists
            await conn.execute(
                """
                INSERT INTO kits (kit_id)
                VALUES ($1)
                ON CONFLICT (kit_id) DO NOTHING
                """,
                kit_id
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
                kit_id,
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
                kit_id
            )
    
    return item_data


async def update_item_quantity(kit_id: str, item_id: str, qty: int) -> bool:
    """Update an item's quantity."""
    async with await DatabasePool.get_connection() as conn:
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
                kit_id
            )
            
            # Update kit's last_edited timestamp
            await conn.execute(
                """
                UPDATE kits
                SET last_edited = $1
                WHERE kit_id = $2
                """,
                datetime.now(timezone.utc),
                kit_id
            )
    
    return True


async def remove_item_from_kit(kit_id: str, item_id: str) -> bool:
    """Remove an item from a kit."""
    async with await DatabasePool.get_connection() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                DELETE FROM kit_items
                WHERE id = $1 AND kit_id = $2
                """,
                item_id,
                kit_id
            )
            
            # Update kit's last_edited timestamp
            await conn.execute(
                """
                UPDATE kits
                SET last_edited = $1
                WHERE kit_id = $2
                """,
                datetime.now(timezone.utc),
                kit_id
            )
    
    return True


async def get_all_first_aid_items() -> Dict[str, List[Dict[str, Any]]]:
    """Get all first aid items grouped by category."""
    async with await DatabasePool.get_connection() as conn:
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
    async with await DatabasePool.get_connection() as conn:
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
    async with await DatabasePool.get_connection() as conn:
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
    async with await DatabasePool.get_connection() as conn:
        await conn.execute(
            "DELETE FROM first_aid_items WHERE item_name = $1",
            item_name
        )
    
    return True


async def get_all_items_across_kits() -> Dict[str, List[Dict[str, Any]]]:
    """Get all items across all kits, grouped by category."""
    async with await DatabasePool.get_connection() as conn:
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
