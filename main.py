
import json
from fastapi import FastAPI, HTTPException
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict
import uvicorn

# --- Configuration ---
DATA_FILE = "first_aid_kit.json"
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# --- Data Models ---
class Item(BaseModel):
    id: str
    name: str
    expiry_date: str

# --- FastAPI App ---
app = FastAPI()

# --- Helper Functions ---
def read_data() -> Dict[str, List[Item]]:
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def write_data(data: Dict[str, List[Item]]):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# --- API Endpoints ---
@app.get("/api/kits/{kit_id}")
async def get_kit_items(kit_id: str):
    data = read_data()
    return data.get(kit_id, [])

@app.post("/api/kits/{kit_id}")
async def add_item_to_kit(kit_id: str, item: Item):
    data = read_data()
    if kit_id not in data:
        data[kit_id] = []
    data[kit_id].append(item.dict())
    write_data(data)
    return item.dict() # Changed this line

@app.delete("/api/kits/{kit_id}/{item_id}")
async def remove_item_from_kit(kit_id: str, item_id: str):
    data = read_data()
    if kit_id not in data:
        raise HTTPException(status_code=404, detail="Kit not found")
    
    items = data[kit_id]
    item_to_remove = next((item for item in items if item['id'] == item_id), None)

    if not item_to_remove:
        raise HTTPException(status_code=404, detail="Item not found")

    items.remove(item_to_remove)
    write_data(data)
    return {"message": "Item removed successfully"}

@app.get("/api/all_items")
async def get_all_items():
    all_data = read_data()
    all_items_list = []
    for kit_id, items in all_data.items():
        for item in items:
            item_with_kit_id = item.copy()
            item_with_kit_id["kit_id"] = kit_id
            all_items_list.append(item_with_kit_id)
    return all_items_list

# --- Static Files ---
@app.get("/")
async def serve_root_page():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"), media_type="text/html")

@app.get("/kit/{kit_id}")
async def serve_kit_page(kit_id: str):
    return FileResponse(os.path.join(STATIC_DIR, "index.html"), media_type="text/html")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/download/first_aid_kit.json")
async def download_first_aid_kit():
    return FileResponse(DATA_FILE, media_type="application/json", filename="first_aid_kit.json")

# --- Main ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
