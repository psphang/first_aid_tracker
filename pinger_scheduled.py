import requests
import json
import os
from datetime import datetime

# Configuration
BASE_URL = "https://first-aid-tracker.onrender.com/" # Assuming your FastAPI app runs on this URL and port
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloaded_data")

def parse_timestamp(timestamp_str):
    """Parses an ISO format timestamp string into a datetime object."""
    if not timestamp_str: return None
    try:
        return datetime.fromisoformat(timestamp_str)
    except ValueError:
        return None

def download_and_save_first_aid_kit():
    """Downloads first_aid_kit.json and saves it with a timestamp."""
    url = f"{BASE_URL}/download/first_aid_kit.json"
    print(f"Attempting to download first_aid_kit.json from: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        # Use current timestamp for filename as first_aid_kit.json has multiple 'last_edited'
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"first_aid_kit_{timestamp}.json"
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Downloaded and saved {filename}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading first_aid_kit.json: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from first_aid_kit.json: {e}")

def download_and_save_first_aid_item_file():
    """Downloads firstIAiditem.json and saves it, checking its internal last_edited timestamp."""
    url = f"{BASE_URL}/download/firstIAiditem.json"
    print(f"Attempting to download firstIAiditem.json from: {url}")
    try:
        response = requests.get(url)
        print(f"Response status code for firstIAiditem.json: {response.status_code}")
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        downloaded_data = response.json()

        downloaded_last_edited_str = downloaded_data.get("last_edited")
        downloaded_last_edited = parse_timestamp(downloaded_last_edited_str)

        # Find existing firstIAiditem.json files in the directory
        existing_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.startswith("firstIAiditem_") and f.endswith(".json")]
        
        should_save = True
        if existing_files:
            # Assuming we only care about the most recent existing file for comparison
            # You might want a more sophisticated logic if multiple versions are kept
            existing_files.sort(reverse=True) # Sort to get the latest by filename timestamp
            latest_existing_file = existing_files[0]
            existing_filepath = os.path.join(DOWNLOAD_DIR, latest_existing_file)
            
            try:
                with open(existing_filepath, "r") as f:
                    existing_data = json.load(f)
                existing_last_edited_str = existing_data.get("last_edited")
                existing_last_edited = parse_timestamp(existing_last_edited_str)

                if downloaded_last_edited and existing_last_edited:
                    if downloaded_last_edited <= existing_last_edited:
                        print(f"firstIAiditem.json not saved: Downloaded version (last_edited: {downloaded_last_edited_str}) is not newer than existing (last_edited: {existing_last_edited_str}).")
                        should_save = False
                    else:
                        print(f"Downloaded firstIAiditem.json is newer (last_edited: {downloaded_last_edited_str}). Saving...")
                elif downloaded_last_edited and not existing_last_edited:
                    print("Existing firstIAiditem.json has no valid last_edited timestamp. Saving new version.")
                elif not downloaded_last_edited and existing_last_edited:
                    print("Downloaded firstIAiditem.json has no valid last_edited timestamp. Not saving if existing has one.")
                    should_save = False # Don't save if new has no timestamp but old does
                else:
                    print("Neither downloaded nor existing firstIAiditem.json has a valid last_edited timestamp. Saving new version.")

            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Warning: Could not read or parse existing firstIAiditem.json ({latest_existing_file}): {e}. Saving new version.")
                should_save = True

        if should_save:
            # Use current timestamp for filename, consistent with first_aid_kit.json
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"firstIAiditem_{timestamp}.json"
            filepath = os.path.join(DOWNLOAD_DIR, filename)

            with open(filepath, "w") as f:
                json.dump(downloaded_data, f, indent=2)
            print(f"Downloaded and saved {filename}")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading firstIAiditem.json: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from firstIAiditem.json: {e}")

if __name__ == "__main__":
    # Create the download directory if it doesn't exist
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    print(f"Ensured download directory exists: {DOWNLOAD_DIR}")

    download_and_save_first_aid_kit()
    download_and_save_first_aid_item_file()