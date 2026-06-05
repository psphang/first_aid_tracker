import asyncpg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
from datetime import date, timedelta, datetime, timezone
from db import (
    DatabasePool, get_kit_items, add_item_to_kit, update_item_quantity,
    remove_item_from_kit, get_all_first_aid_items, add_first_aid_item,
    update_first_aid_item, delete_first_aid_item, get_all_items_across_kits
)

# --- Configuration ---
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# --- Data Models ---
class Item(BaseModel):
    id: str
    name: str
    item_no: Optional[str] = None
    expiry_date: Optional[str] = None
    qty: int

class QuantityUpdate(BaseModel):
    qty: int

# --- FastAPI App ---
app = FastAPI()

# --- CORS Middleware for Vercel Frontend ---
# Allows frontend on Vercel to make API calls to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://first-aid-tracker.vercel.app",  # Vercel production frontend
        "http://localhost:3000",                   # Local Next.js/React dev
        "http://localhost:8001",                   # Local backend dev
        "http://localhost:5173",                   # Local Vite dev
        "http://127.0.0.1:3000",                  # Alternative localhost
        "http://127.0.0.1:8001"                   # Alternative localhost
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# --- Helper Functions ---
def get_item_status(item):
    if item.get('qty', 0) == 0:
        return "Empty"
    if item.get('expiry_date'):
        try:
            expiry = date.fromisoformat(item['expiry_date'])
            today = date.today()
            if expiry < today:
                return "Expired"
            elif expiry <= today + timedelta(days=30):
                return "Expires Soon"
            else:
                return "OK"
        except (ValueError, TypeError):
            return "Invalid Date"
    return "OK"

def sort_key(item):
    expiring_status = item.get('Expiring', 'No')
    expiring_order = 0 if expiring_status == 'Yes' else 1
    expiry_date_str = item.get('expiry_date')
    if expiry_date_str:
        try:
            return (expiring_order, 0, datetime.fromisoformat(expiry_date_str).date())
        except (ValueError, TypeError):
            return (expiring_order, 1, item.get('name', ''))
    else:
        return (expiring_order, 1, item.get('name', ''))

# --- Startup/Shutdown Events ---
@app.on_event("startup")
async def startup_event():
    """Initialize database pool on startup."""
    await DatabasePool.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database pool on shutdown."""
    await DatabasePool.close()

# --- Health Check Endpoint ---
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok", "service": "first-aid-tracker-api"}

# --- API Endpoints ---
@app.get("/api/firstaiditems")
async def get_first_aid_items():
    """Get all first aid items from master list."""
    try:
        data = await get_all_first_aid_items()
        # Convert grouped data to expected format
        items = []
        for category, category_items in data.items():
            items.extend(category_items)
        items.sort(key=lambda x: x.get('Item', '').lower())
        return {"items": items, "last_edited": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/kits/{kit_id}")
async def get_kit_items_endpoint(kit_id: str):
    """Get items for a specific kit."""
    try:
        kit_data = await get_kit_items(kit_id)
        
        # Add status to each item
        grouped_items = kit_data.get('items', {})
        for category_items in grouped_items.values():
            for item in category_items:
                item['status'] = get_item_status(item)
                item['Expiring'] = item.get('Expiring', 'No')
        
        return kit_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/kits/{kit_id}")
async def add_item_to_kit_endpoint(kit_id: str, item: Item):
    """Add an item to a kit."""
    try:
        item_data = item.dict()
        await add_item_to_kit(kit_id, item_data)
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/kits/{kit_id}/{item_id}")
async def update_item_quantity_endpoint(kit_id: str, item_id: str, quantity_update: QuantityUpdate):
    """Update an item's quantity."""
    try:
        await update_item_quantity(kit_id, item_id, quantity_update.qty)
        return {"message": "Quantity updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/kits/{kit_id}/{item_id}")
async def remove_item_from_kit_endpoint(kit_id: str, item_id: str):
    """Remove an item from a kit."""
    try:
        await remove_item_from_kit(kit_id, item_id)
        return {"message": "Item removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/all_items")
async def get_all_items():
    """Get all items across all kits."""
    try:
        grouped_items = await get_all_items_across_kits()
        
        # Add status to each item
        for category_items in grouped_items.values():
            for item in category_items:
                item['status'] = get_item_status(item)
                item['Expiring'] = item.get('Expiring', 'No')
        
        return grouped_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/firstaiditems")
async def add_first_aid_item_endpoint(item: Dict):
    """Add a new first aid item to master list."""
    try:
        await add_first_aid_item(item)
        return {"message": "Item added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/firstaiditems/{item_name}")
async def update_first_aid_item_endpoint(item_name: str, updated_item: Dict):
    """Update a first aid item."""
    try:
        await update_first_aid_item(item_name, updated_item)
        return {"message": "Item updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/firstaiditems/{item_name}")
async def delete_first_aid_item_endpoint(item_name: str):
    """Delete a first aid item."""
    try:
        await delete_first_aid_item(item_name)
        return {"message": "Item deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Static Files ---
@app.get("/")
async def serve_root_page():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"), media_type="text/html")

@app.get("/kit/{kit_id}")
async def serve_kit_page(kit_id: str):
    return FileResponse(os.path.join(STATIC_DIR, "index.html"), media_type="text/html")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/edit_items")
async def serve_edit_items_page():
    return FileResponse(os.path.join(STATIC_DIR, "edit_items.html"), media_type="text/html")

# --- Main ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
