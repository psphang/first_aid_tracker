import requests
import logging
from datetime import datetime
import os
import json

# Configure logging
logging.basicConfig(
    filename='pinger.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

URL = "https://first-aid-tracker.onrender.com/"

LAST_DOWNLOAD_DATE_DIR = os.path.join(os.path.dirname(__file__), 'last_download_dates')

def get_last_download_date(file_identifier):
    """
    Reads the last download datetime for a specific file from its timestamp file.
    """
    file_path = os.path.join(LAST_DOWNLOAD_DATE_DIR, f'last_download_date_{file_identifier}.txt')
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            date_str = f.read().strip()
            if date_str:
                return datetime.fromisoformat(date_str)
    return None

def set_last_download_date(file_identifier, dt):
    """
    Writes the last download datetime for a specific file to its timestamp file.
    """
    os.makedirs(LAST_DOWNLOAD_DATE_DIR, exist_ok=True)
    file_path = os.path.join(LAST_DOWNLOAD_DATE_DIR, f'last_download_date_{file_identifier}.txt')
    with open(file_path, 'w') as f:
        f.write(dt.isoformat())

def ping_site():
    """
    Sends a GET request to the specified URL and downloads files once per day if there are updates.
    """
    logging.info("Scheduled pinger script started.")

    # Perform the regular ping
    try:
        response = requests.get(URL)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if response.status_code == 200:
            logging.info(f"Ping successful. Status Code: {response.status_code}")
            print(f"[{timestamp}] Ping successful. Status Code: {response.status_code}")
        else:
            logging.warning(f"Ping failed with Status Code: {response.status_code}")
            print(f"[{timestamp}] Ping failed with Status Code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.error(f"An error occurred: {e}")
        print(f"[{timestamp}] An error occurred: {e}")

    # Check for updates before downloading
    # We will now check for updates per file
    download_url_kit = "https://first-aid-tracker.onrender.com/download/first_aid_kit.json"
    download_url_item = "https://first-aid-tracker.onrender.com/download/firstIAiditem.json"
    
    # Get the last edited date from the remote first_aid_kit.json for comparison
    remote_first_aid_kit_last_edited = None
    remote_first_aid_item_last_edited = None

    # Fetch first_aid_kit.json
    try:
        response_kit = requests.get(download_url_kit)
        if response_kit.status_code == 200:
            try:
                data = json.loads(response_kit.content)
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, dict) and 'last_edited' in value:
                            last_edited_str = value['last_edited']
                            last_edited_dt = datetime.fromisoformat(last_edited_str)
                            if remote_first_aid_kit_last_edited is None or last_edited_dt > remote_first_aid_kit_last_edited:
                                remote_first_aid_kit_last_edited = last_edited_dt
            except (json.JSONDecodeError, TypeError) as e:
                logging.error(f"Error processing JSON from first_aid_kit.json for pre-check: {e}")

    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred during pre-download check for first_aid_kit.json: {e}")

    # Fetch firstIAiditem.json
    try:
        response_item = requests.get(download_url_item)
        if response_item.status_code == 200:
            try:
                data = json.loads(response_item.content)
                if isinstance(data, dict) and 'last_edited' in data:
                    last_edited_str = data['last_edited']
                    remote_first_aid_item_last_edited = datetime.fromisoformat(last_edited_str)
            except (json.JSONDecodeError, TypeError) as e:
                logging.error(f"Error processing JSON from firstIAiditem.json for pre-check: {e}")

    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred during pre-download check for firstIAiditem.json: {e}")

    # Determine if a full download is needed based on individual file updates
    should_perform_full_download = False

    last_download_dt_first_aid_kit = get_last_download_date('first_aid_kit')
    if remote_first_aid_kit_last_edited and \
       (last_download_dt_first_aid_kit is None or remote_first_aid_kit_last_edited > last_download_dt_first_aid_kit):
        should_perform_full_download = True

    last_download_dt_first_aid_item = get_last_download_date('firstIAiditem')
    if remote_first_aid_item_last_edited and \
       (last_download_dt_first_aid_item is None or remote_first_aid_item_last_edited > last_download_dt_first_aid_item):
        should_perform_full_download = True

    if should_perform_full_download:
        DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'downloaded_data')
        if not os.path.exists(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR)

        files_to_download = {
            'first_aid_kit.json': response_kit.content, 
            'firstIAiditem.json': response_item.content
        }

        for filename, content in files_to_download.items():
            file_identifier = os.path.splitext(filename)[0] # e.g., 'first_aid_kit'
            
            # Save the downloaded file with a timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base, ext = os.path.splitext(filename)
            dated_filename = f"{base}_{timestamp}{ext}"
            download_path = os.path.join(DOWNLOAD_DIR, dated_filename)
            
            with open(download_path, 'wb') as f:
                f.write(content)
            
            logging.info(f"Daily download successful for {filename}. File saved to {download_path}")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Daily download successful for {filename}. File saved to {download_path}")

            # Extract and save last_edited for this specific file if it's a JSON
            if filename == 'first_aid_kit.json':
                file_latest_last_edited = remote_first_aid_kit_last_edited
            elif filename == 'firstIAiditem.json':
                file_latest_last_edited = remote_first_aid_item_last_edited
            else:
                file_latest_last_edited = None

            if file_latest_last_edited:
                set_last_download_date(file_identifier, file_latest_last_edited)
                logging.info(f"Saved last_edited for {filename}: {file_latest_last_edited}")

    logging.info("Scheduled pinger script finished.")


if __name__ == "__main__":
    ping_site()