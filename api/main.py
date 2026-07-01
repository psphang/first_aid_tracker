import asyncpg
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import date, timedelta, datetime

from db import (
    DatabasePool,
    get_kit_items,
    add_item_to_kit,
    update_item_quantity,
    remove_item_from_kit,
    get_all_first_aid_items,
    add_first_aid_item,
    update_first_aid_item,
    delete_first_aid_item,
    get_all_items_across_kits,
)

class Item(BaseModel):
    id: str
    name: str
    item_no: Optional[str] = None
    expiry_date: Optional[str] = None
    qty: int

class QuantityUpdate(BaseModel):
    qty: int

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

def find_public_dir():
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public"),
        os.path.join(os.getcwd(), "public"),
        "public",
    ]
    for p in candidates:
        if os.path.isdir(p):
            return p
    return None

PUBLIC_DIR = None

def read_file(filename):
    global PUBLIC_DIR
    if PUBLIC_DIR is None:
        PUBLIC_DIR = find_public_dir()
    if PUBLIC_DIR:
        fpath = os.path.join(PUBLIC_DIR, filename)
        if os.path.isfile(fpath):
            return open(fpath, encoding="utf-8").read()
    return None

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

@app.on_event("startup")
async def startup_event():
    await DatabasePool.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    await DatabasePool.close()

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "first-aid-tracker-api"}

@app.get("/api/debug-paths")
async def debug_paths():
    results = {}
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public"),
        os.path.join(os.getcwd(), "public"),
        "public",
        "/var/task/public",
        "/var/runtime/public",
    ]
    for p in candidates:
        results[p] = os.path.isdir(p)
    results["cwd"] = os.getcwd()
    results["file_dir"] = os.path.dirname(os.path.abspath(__file__))
    results["ls_file_dir"] = os.listdir(os.path.dirname(os.path.abspath(__file__)))
    if os.path.isdir(os.path.join(os.getcwd())):
        try:
            results["ls_cwd"] = os.listdir(os.getcwd())
        except:
            pass
    return results

@app.get("/api/firstaiditems")
async def get_first_aid_items():
    data = await get_all_first_aid_items()
    items = []
    for category, category_items in data.items():
        items.extend(category_items)
    items.sort(key=lambda x: x.get('Item', '').lower())
    return {"items": items, "last_edited": None}

@app.get("/api/kits/{kit_id}")
async def get_kit_items_endpoint(kit_id: str):
    kit_data = await get_kit_items(kit_id)
    grouped_items = kit_data.get('items', {})
    for category_items in grouped_items.values():
        for item in category_items:
            item['status'] = get_item_status(item)
            item['Expiring'] = item.get('Expiring', 'No')
    return kit_data

@app.post("/api/kits/{kit_id}")
async def add_item_to_kit_endpoint(kit_id: str, item: Item):
    await add_item_to_kit(kit_id, item.dict())
    return item

@app.put("/api/kits/{kit_id}/{item_id}")
async def update_item_quantity_endpoint(kit_id: str, item_id: str, quantity_update: QuantityUpdate):
    await update_item_quantity(kit_id, item_id, quantity_update.qty)
    return {"message": "Quantity updated successfully"}

@app.delete("/api/kits/{kit_id}/{item_id}")
async def remove_item_from_kit_endpoint(kit_id: str, item_id: str):
    await remove_item_from_kit(kit_id, item_id)
    return {"message": "Item removed successfully"}

@app.get("/api/all_items")
async def get_all_items():
    grouped_items = await get_all_items_across_kits()
    for category_items in grouped_items.values():
        for item in category_items:
            item['status'] = get_item_status(item)
            item['Expiring'] = item.get('Expiring', 'No')
    return grouped_items

@app.post("/api/firstaiditems")
async def add_first_aid_item_endpoint(item: Dict):
    await add_first_aid_item(item)
    return {"message": "Item added successfully"}

@app.put("/api/firstaiditems/{item_name}")
async def update_first_aid_item_endpoint(item_name: str, updated_item: Dict):
    await update_first_aid_item(item_name, updated_item)
    return {"message": "Item updated successfully"}

@app.delete("/api/firstaiditems/{item_name}")
async def delete_first_aid_item_endpoint(item_name: str):
    await delete_first_aid_item(item_name)
    return {"message": "Item deleted successfully"}

@app.get("/styles.css")
async def serve_css():
    content = read_file("styles.css")
    if content:
        return HTMLResponse(content=content, media_type="text/css")
    return HTMLResponse(content="not found", status_code=404)

@app.get("/app.js")
async def serve_app_js():
    content = read_file("app.js")
    if content:
        return HTMLResponse(content=content, media_type="application/javascript")
    return HTMLResponse(content="not found", status_code=404)

@app.get("/edit_items.js")
async def serve_edit_js():
    content = read_file("edit_items.js")
    if content:
        return HTMLResponse(content=content, media_type="application/javascript")
    return HTMLResponse(content="not found", status_code=404)

@app.get("/edit_items")
async def serve_edit_page():
    content = read_file("edit_items.html")
    if content:
        return HTMLResponse(content=content, media_type="text/html")
    return HTMLResponse(content="not found", status_code=404)

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    content = read_file("index.html")
    if content:
        return HTMLResponse(content=content, media_type="text/html")
    return HTMLResponse(content="not found", status_code=404)
