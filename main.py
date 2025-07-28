
import json
from fastapi import FastAPI, HTTPException
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
from datetime import date, timedelta, datetime, timezone

# --- Configuration ---
DATA_FILE = "first_aid_kit.json"
ITEMS_FILE = "firstIAiditem.json"
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

# --- Helper Functions ---
def read_data(file_path):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            if file_path == ITEMS_FILE:
                # If it's the items file, check if it's the old array format
                if isinstance(data, list):
                    # Convert old format (list) to new format (dict with "items" and "last_edited")
                    return {"items": data, "last_edited": None}
                # Otherwise, it's already the new format, return as is
                return data
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        if file_path == DATA_FILE:
            return {}
        elif file_path == ITEMS_FILE:
            # Return the new structure for an empty items file
            return {"items": [], "last_edited": None}
        return {}

def write_data(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

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
            # Valid date: sort by date
            return (expiring_order, 0, datetime.fromisoformat(expiry_date_str).date())
        except (ValueError, TypeError):
            # Invalid date string: treat as having no date, sort by name
            return (expiring_order, 1, item.get('name', ''))
    else:
        # No date: sort by name
        return (expiring_order, 1, item.get('name', ''))

# --- API Endpoints ---
@app.get("/api/firstaiditems")
async def get_first_aid_items():
    data = read_data(ITEMS_FILE)
    # Ensure items are sorted
    data.get('items', []).sort(key=lambda x: x.get('Item', '').lower()) # Sort by item name
    return data

@app.get("/api/kits/{kit_id}")
async def get_kit_items(kit_id: str):
    data = read_data(DATA_FILE)
    kit_data = data.get(kit_id, {"items": [], "last_edited": ""})
    all_items_data = read_data(ITEMS_FILE)
    all_items = all_items_data.get('items', [])
    
    item_details = {item.get('Item'): {'item_no': item.get('Item#'), 'category': item.get('category'), 'Expiring': item.get('Expiring')} for item in all_items}
    
    for item in kit_data["items"]:
        details = item_details.get(item.get('name'), {})
        item['status'] = get_item_status(item)
        item['category'] = details.get('category', 'Uncategorized')
        item['item_no'] = details.get('item_no', '')
        item['Expiring'] = details.get('Expiring', 'No')
        
    kit_data["items"].sort(key=sort_key)
    
    grouped_items = {}
    for item in kit_data["items"]:
        category = item.get('category', 'Uncategorized')
        if category not in grouped_items:
            grouped_items[category] = []
        grouped_items[category].append(item)
        
    kit_data['items'] = grouped_items
    return kit_data

@app.post("/api/kits/{kit_id}")
async def add_item_to_kit(kit_id: str, item: Item):
    data = read_data(DATA_FILE)
    if kit_id not in data:
        data[kit_id] = {"items": [], "last_edited": ""}
    data[kit_id]["items"].append(item.dict())
    data[kit_id]["last_edited"] = datetime.now(timezone.utc).isoformat()
    write_data(DATA_FILE, data)
    return item

@app.put("/api/kits/{kit_id}/{item_id}")
async def update_item_quantity(kit_id: str, item_id: str, quantity_update: QuantityUpdate):
    data = read_data(DATA_FILE)
    if kit_id not in data:
        raise HTTPException(status_code=404, detail="Kit not found")

    kit_data = data.get(kit_id)
    if not kit_data or "items" not in kit_data:
        raise HTTPException(status_code=404, detail="Kit not found or malformed")

    items = kit_data["items"]
    item_to_update = next((item for item in items if item['id'] == item_id), None)

    if not item_to_update:
        raise HTTPException(status_code=404, detail="Item not found")

    item_to_update['qty'] = quantity_update.qty
    data[kit_id]["last_edited"] = datetime.now(timezone.utc).isoformat()
    write_data(DATA_FILE, data)
    return {"message": "Quantity updated successfully"}

@app.delete("/api/kits/{kit_id}/{item_id}")
async def remove_item_from_kit(kit_id: str, item_id: str):
    data = read_data(DATA_FILE)
    if kit_id not in data:
        raise HTTPException(status_code=404, detail="Kit not found")
    
    kit_data = data.get(kit_id)
    if not kit_data or "items" not in kit_data:
        raise HTTPException(status_code=404, detail="Kit not found or malformed")
    
    items = kit_data["items"]
    item_to_remove = next((item for item in items if item['id'] == item_id), None)

    if not item_to_remove:
        raise HTTPException(status_code=404, detail="Item not found")

    items.remove(item_to_remove)
    data[kit_id]["last_edited"] = datetime.now(timezone.utc).isoformat()
    write_data(DATA_FILE, data)
    return {"message": "Item removed successfully"}

@app.get("/api/all_items")
async def get_all_items():
    all_data = read_data(DATA_FILE)
    all_items_info_data = read_data(ITEMS_FILE)
    all_items_info = all_items_info_data.get('items', [])
    item_details = {item.get('Item'): {'item_no': item.get('Item#'), 'category': item.get('category'), 'Expiring': item.get('Expiring')} for item in all_items_info}
    
    all_items_list = []
    for kit_id, kit_content in all_data.items():
        if isinstance(kit_content, dict) and "items" in kit_content and isinstance(kit_content["items"], list):
            for item in kit_content["items"]:
                details = item_details.get(item.get('name'), {})
                item_with_kit_id = item.copy()
                item_with_kit_id["kit_id"] = kit_id
                item_with_kit_id['status'] = get_item_status(item)
                item_with_kit_id['item_no'] = details.get('item_no', '')
                item_with_kit_id['category'] = item_details.get(item.get('name'), {}).get('category', 'Uncategorized')
                item_with_kit_id['Expiring'] = details.get('Expiring', 'No')
                all_items_list.append(item_with_kit_id)
    all_items_list.sort(key=sort_key)
    
    grouped_items = {}
    for item in all_items_list:
        category = item.get('category', 'Uncategorized')
        if category not in grouped_items:
            grouped_items[category] = []
        grouped_items[category].append(item)
        
    return grouped_items

@app.post("/api/firstaiditems")
async def add_first_aid_item(item: Dict):
    # Ensure 'Item#' is present, even if empty
    item['Item#'] = item.get('Item#', '')
    items_data = read_data(ITEMS_FILE)
    items = items_data.get('items', [])
    print(f"Current items in firstIAiditem.json: {items}")

    # Determine the next running number for 'No'
    next_no = "1"
    if items:
        max_no = 0
        for existing_item in items:
            try:
                max_no = max(max_no, int(existing_item.get('No', 0)))
            except ValueError:
                pass
        next_no = str(max_no + 1)

    # Create a new dictionary for the item with the desired key order
    formatted_item = {
        "No": next_no,
        "Item#": item.get('Item#', ''),
        "Item": item.get('Item', ''),
        "category": item.get('category', 'Uncategorized'), # Ensure category is always present
        "Expiring": item.get('Expiring', 'No') # Ensure Expiring is always present
    }

    items.append(formatted_item)
    items_data['items'] = items
    items_data['last_edited'] = datetime.now(timezone.utc).isoformat()
    write_data(ITEMS_FILE, items_data)
    return {"message": "Item added successfully"}

@app.put("/api/firstaiditems/{item_name}")
async def update_first_aid_item(item_name: str, updated_item: Dict):
    items_data = read_data(ITEMS_FILE)
    items = items_data.get('items', [])
    found = False
    for item in items: # Iterate directly over items to modify in place
        if item.get("Item", "").strip().lower() == item_name.strip().lower():
            # Update fields of the existing item with values from updated_item
            item['Item'] = updated_item.get('Item', item.get('Item')) # Update Item name
            item['Item#'] = updated_item.get('Item#', item.get('Item#', '')) # Update Item#
            item['category'] = updated_item.get('category', item.get('category', 'Uncategorized')) # Update category
            item['Expiring'] = updated_item.get('Expiring', item.get('Expiring')) # Update Expiring

            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail="Item not found")
    items_data['items'] = items
    items_data['last_edited'] = datetime.now(timezone.utc).isoformat()
    write_data(ITEMS_FILE, items_data)
    return {"message": "Item updated successfully"}

@app.delete("/api/firstaiditems/{item_name}")
async def delete_first_aid_item(item_name: str):
    items_data = read_data(ITEMS_FILE)
    items = items_data.get('items', [])
    initial_len = len(items)
    items = [item for item in items if item.get("Item") != item_name]
    if len(items) == initial_len:
        raise HTTPException(status_code=404, detail="Item not found")
    items_data['items'] = items
    items_data['last_edited'] = datetime.now(timezone.utc).isoformat()
    write_data(ITEMS_FILE, items_data)
    return {"message": "Item deleted successfully"}

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

@app.get("/download/first_aid_kit.json")
async def download_first_aid_kit():
    return FileResponse(DATA_FILE, media_type="application/json", filename="first_aid_kit.json")

@app.get("/download/firstIAiditem.json")
async def download_first_aid_item_file():
    return FileResponse(ITEMS_FILE, media_type="application/json", filename="firstIAiditem.json")

# --- Main ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
