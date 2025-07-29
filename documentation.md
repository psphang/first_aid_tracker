## Documentation for First Aid Tracker Application

This document outlines the functionality and workflow of the `main.py` web application and the `pinger_scheduled.py` data synchronization script.

### 1. `main.py` - Web Application (FastAPI)

The `main.py` script implements a FastAPI web server for managing first aid kit inventory. It provides API endpoints for interacting with first aid kit data and serves static web content.

**Purpose:**
To provide a backend API for a web-based First Aid Tracker, allowing users to view, add, update, and delete items within various first aid kits, and to manage a master list of first aid items.

**Data Files:**
*   `first_aid_kit.json`: Stores the inventory data for each first aid kit. Each kit is a key in the main JSON object, containing a list of items and a `last_edited` timestamp.
*   `firstIAiditem.json`: Stores a master list of all possible first aid items, including their item numbers, categories, and whether they are expiring.

**Data Models (Pydantic):**
*   `Item`: Represents an item within a first aid kit.
    *   `id` (str): Unique identifier for the item.
    *   `name` (str): Name of the item.
    *   `item_no` (Optional[str]): Item number.
    *   `expiry_date` (Optional[str]): Expiry date in ISO format (YYYY-MM-DD).
    *   `qty` (int): Quantity of the item.
*   `QuantityUpdate`: Used for updating the quantity of an item.
    *   `qty` (int): The new quantity.

**Helper Functions:**
*   `read_data(file_path)`: Reads JSON data from the specified `file_path`. Handles `FileNotFoundError` and `json.JSONDecodeError`. Specifically for `firstIAiditem.json`, it can convert an old list-based format to the new dictionary format (with "items" and "last_edited").
*   `write_data(file_path, data)`: Writes Python dictionary data to the specified `file_path` as JSON, with an indent of 2 for readability.
*   `get_item_status(item)`: Determines the status of an item based on its quantity and expiry date (e.g., "Empty", "Expired", "Expires Soon", "OK", "Invalid Date").
*   `sort_key(item)`: A utility function used for sorting items, prioritizing expiring items and then by expiry date or name.

**API Endpoints:**

*   **`GET /api/firstaiditems`**
    *   **Purpose:** Retrieves the master list of all first aid items.
    *   **Returns:** A dictionary containing the master list of items, sorted by item name.

*   **`GET /api/kits/{kit_id}`**
    *   **Purpose:** Retrieves the details of a specific first aid kit.
    *   **Parameters:** `kit_id` (str) - The identifier of the kit.
    *   **Returns:** A dictionary containing the kit's items, grouped by category, with added status, item number, and expiring information.

*   **`POST /api/kits/{kit_id}`**
    *   **Purpose:** Adds a new item to a specific first aid kit.
    *   **Parameters:** `kit_id` (str), `item` (Item model) - The item to add.
    *   **Actions:** Appends the item to the kit's item list and updates the kit's `last_edited` timestamp.
    *   **Returns:** The added item.

*   **`PUT /api/kits/{kit_id}/{item_id}`**
    *   **Purpose:** Updates the quantity of an item within a specific kit.
    *   **Parameters:** `kit_id` (str), `item_id` (str), `quantity_update` (QuantityUpdate model) - The new quantity.
    *   **Actions:** Finds the item by `item_id` and updates its `qty`. Updates the kit's `last_edited` timestamp.
    *   **Returns:** A success message.
    *   **Raises:** `HTTPException` (404) if kit or item not found.

*   **`DELETE /api/kits/{kit_id}/{item_id}`**
    *   **Purpose:** Removes an item from a specific kit.
    *   **Parameters:** `kit_id` (str), `item_id` (str).
    *   **Actions:** Removes the item by `item_id` from the kit's item list. Updates the kit's `last_edited` timestamp.
    *   **Returns:** A success message.
    *   **Raises:** `HTTPException` (404) if kit or item not found.

*   **`GET /api/all_items`**
    *   **Purpose:** Aggregates and retrieves all items from all first aid kits.
    *   **Returns:** A dictionary of all items, grouped by category, with kit ID and status information.

*   **`POST /api/firstaiditems`**
    *   **Purpose:** Adds a new item to the master `firstIAiditem.json` list.
    *   **Parameters:** `item` (Dict) - The item details.
    *   **Actions:** Assigns a running "No" number, formats the item, appends it to the master list, and updates the `last_edited` timestamp of `firstIAiditem.json`.
    *   **Returns:** A success message.

*   **`PUT /api/firstaiditems/{item_name}`**
    *   **Purpose:** Updates an existing item in the master `firstIAiditem.json` list.
    *   **Parameters:** `item_name` (str) - The name of the item to update, `updated_item` (Dict) - The new item details.
    *   **Actions:** Finds the item by name and updates its properties. Updates the `last_edited` timestamp of `firstIAiditem.json`.
    *   **Returns:** A success message.
    *   **Raises:** `HTTPException` (404) if item not found.

*   **`DELETE /api/firstaiditems/{item_name}`**
    *   **Purpose:** Deletes an item from the master `firstIAiditem.json` list.
    *   **Parameters:** `item_name` (str) - The name of the item to delete.
    *   **Actions:** Removes the item by name from the master list. Updates the `last_edited` timestamp of `firstIAiditem.json`.
    *   **Returns:** A success message.
    *   **Raises:** `HTTPException` (404) if item not found.

**Static File Serving:**
*   `GET /`: Serves `static/index.html` as the root page.
*   `GET /kit/{kit_id}`: Serves `static/index.html` for specific kit pages (client-side routing).
*   `app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")`: Serves all other static assets (JS, CSS, images) from the `static` directory.
*   `GET /edit_items`: Serves `static/edit_items.html`.
*   `GET /download/first_aid_kit.json`: Allows direct download of `first_aid_kit.json`.
*   `GET /download/firstIAiditem.json`: Allows direct download of `firstIAiditem.json`.

**Running the Application:**
The application can be run using `uvicorn`:
```bash
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
```
This will start the server on `http://0.0.0.0:8001`.

### 2. `pinger_scheduled.py` - Host Active and Data Synchronization

The `pinger_scheduled.py` script is designed to ensure the hosted web service remains active and to synchronize the local JSON data files (`first_aid_kit.json` and `firstIAiditem.json`) with a remote source and a GitHub repository.

**Purpose:**
*   To prevent the hosted web service (e.g., on Render.com's free tier) from going to sleep due to inactivity by periodically sending a request.
*   To maintain data consistency by synchronizing local JSON data files with a remote source.
*   To ensure that any changes to these JSON files (whether from remote updates or local modifications) are automatically pushed to a GitHub repository.

**Core Functionality:**

1.  **Host Ping:**
    *   Sends a `GET` request to the `URL` (`https://first-aid-tracker.onrender.com/`).
    *   Logs the success or failure of the ping, along with the HTTP status code.

2.  **Data Download and Comparison:**
    *   Attempts to download `first_aid_kit.json` and `firstIAiditem.json` from their respective download URLs on the remote server.
    *   For each file, it extracts the `last_edited` timestamp from the remote content and compares it with the `last_edited` timestamp of the local file.

3.  **Handling Remote Updates:**
    *   If a remote file's `last_edited` timestamp is newer than the local file's (or if the local file doesn't exist):
        *   The remote file content is downloaded and used to overwrite the local file.
        *   A historical copy of the downloaded file is saved in the `downloaded_data` directory (e.g., `first_aid_kit_YYYYMMDD_HHMMSS.json`).
        *   The `set_last_download_date` function is called to record the new `last_edited` timestamp.
        *   A Git push is triggered with a commit message indicating an update from remote.

4.  **Handling Local Updates (New Logic):**
    *   If a local file's `last_edited` timestamp is newer than the remote file's (or if the remote file could not be fetched):
        *   The script reads the current content of the local JSON file.
        *   It updates the `last_edited` timestamp within the local JSON data to the current UTC time.
        *   The modified JSON content is then written back to the local file. This crucial step ensures that Git detects a physical change in the file, even if only the timestamp was updated.
        *   A Git push is triggered with a commit message indicating local changes.

**`push_to_github(commit_message, files_to_add)` Function:**
*   This function is responsible for interacting with Git.
*   It accepts a `commit_message` and a list of `files_to_add` (e.g., `[LOCAL_DATA_FILE]`, `[LOCAL_ITEMS_FILE]`).
*   It stages only the specified files using `git add <file_path>`.
*   It checks if there are any staged changes to commit.
*   If changes exist, it commits them with the provided `commit_message`.
*   Finally, it pushes the committed changes to the `master` branch of the `origin` remote.
*   Error handling is included for Git operations.

**Scheduled Task Interaction:**
This script is designed to be run periodically by a system-level scheduled task (e.g., Windows Task Scheduler). The task would execute `pinger_scheduled.py` at regular intervals (e.g., every 14 minutes) to perform its host-pinging and data synchronization duties.
