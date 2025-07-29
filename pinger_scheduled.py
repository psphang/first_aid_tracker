import requests
import logging
from datetime import datetime, timezone
import os
import json
import subprocess

# Configure logging
logging.basicConfig(
    filename='pinger.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

URL = "https://first-aid-tracker.onrender.com/"

LAST_DOWNLOAD_DATE_DIR = os.path.join(os.path.dirname(__file__), 'last_download_dates')
LOCAL_DATA_FILE = os.path.join(os.path.dirname(__file__), 'first_aid_kit.json')
LOCAL_ITEMS_FILE = os.path.join(os.path.dirname(__file__), 'firstIAiditem.json')

def to_utc(dt):
    """Converts a datetime object to UTC, making it timezone-aware."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def get_last_download_date(file_identifier):
    """
    Reads the last download datetime for a specific file from its timestamp file.
    """
    file_path = os.path.join(LAST_DOWNLOAD_DATE_DIR, f'last_download_date_{file_identifier}.txt')
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            date_str = f.read().strip()
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str)
                    return to_utc(dt)
                except ValueError:
                    logging.warning(f"Could not parse date '{date_str}' from {file_path}")
                    return None
    return None

def set_last_download_date(file_identifier, dt):
    """
    Writes the last download datetime for a specific file to its timestamp file.
    """
    os.makedirs(LAST_DOWNLOAD_DATE_DIR, exist_ok=True)
    file_path = os.path.join(LAST_DOWNLOAD_DATE_DIR, f'last_download_date_{file_identifier}.txt')
    with open(file_path, 'w') as f:
        f.write(dt.isoformat())

def push_to_github(commit_message, files_to_add):
    """
    Stages, commits, and pushes specified files to the GitHub repository.
    """
    logging.info(f"Attempting to push to GitHub with commit message: {commit_message}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Attempting to push to GitHub...")

    try:
        # Stage specified files
        for file_path in files_to_add:
            subprocess.run(['git', 'add', file_path], cwd=os.path.dirname(__file__), check=True, capture_output=True, text=True)
        logging.info(f"Staged files: {files_to_add}")

        # Check if there are any changes to commit
        result = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            logging.info("No changes to commit.")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No changes to commit.")
            return

        # Commit the changes
        subprocess.run(['git', 'commit', '-m', commit_message], cwd=os.path.dirname(__file__), check=True, capture_output=True, text=True)
        logging.info("Committed changes.")

        # Push the changes to GitHub
        result = subprocess.run(['git', 'push', '--verbose', 'origin', 'master'], cwd=os.path.dirname(__file__), check=True, capture_output=True, text=True)
        logging.info(f"Pushed changes to GitHub. Stdout: {result.stdout}, Stderr: {result.stderr}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Git Push successful.")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Git Push Stdout:\n{result.stdout}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Git Push Stderr:\n{result.stderr}")

    except subprocess.CalledProcessError as e:
        logging.error(f"Git operation failed with exit code {e.returncode}")
        logging.error(f"Stdout: {e.stdout}")
        logging.error(f"Stderr: {e.stderr}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: Git operation failed.")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Stderr:\n{e.stderr}")
    except Exception as e:
        logging.error(f"An error occurred during git push: {e}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: An error occurred during git push: {e}")

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
    download_url_kit = "https://first-aid-tracker.onrender.com/download/first_aid_kit.json"
    download_url_item = "https://first-aid-tracker.onrender.com/download/firstIAiditem.json"
    
    remote_first_aid_kit_last_edited = None
    remote_first_aid_item_last_edited = None
    response_kit = None
    response_item = None

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
                            last_edited_dt = to_utc(datetime.fromisoformat(last_edited_str))
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
                    remote_first_aid_item_last_edited = to_utc(datetime.fromisoformat(last_edited_str))
            except (json.JSONDecodeError, TypeError) as e:
                logging.error(f"Error processing JSON from firstIAiditem.json for pre-check: {e}")

    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred during pre-download check for firstIAiditem.json: {e}")

    # --- Compare and Download first_aid_kit.json ---
    local_first_aid_kit_last_edited = None
    if os.path.exists(LOCAL_DATA_FILE):
        try:
            with open(LOCAL_DATA_FILE, 'r') as f:
                local_data = json.load(f)
                if isinstance(local_data, dict):
                    for key, value in local_data.items():
                        if isinstance(value, dict) and 'last_edited' in value:
                            last_edited_str = value['last_edited']
                            last_edited_dt = to_utc(datetime.fromisoformat(last_edited_str))
                            if local_first_aid_kit_last_edited is None or last_edited_dt > local_first_aid_kit_last_edited:
                                local_first_aid_kit_last_edited = last_edited_dt
        except (json.JSONDecodeError, TypeError, FileNotFoundError) as e:
            logging.warning(f"Error reading local first_aid_kit.json for comparison: {e}")

    logging.info(f"first_aid_kit.json: Remote last_edited: {remote_first_aid_kit_last_edited}, Local last_edited: {local_first_aid_kit_last_edited}")
    if response_kit and remote_first_aid_kit_last_edited and (local_first_aid_kit_last_edited is None or remote_first_aid_kit_last_edited > local_first_aid_kit_last_edited):
        try:
            with open(LOCAL_DATA_FILE, 'wb') as f:
                f.write(response_kit.content)
            logging.info(f"Updated {LOCAL_DATA_FILE} with newer version from remote.")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Updated {LOCAL_DATA_FILE} with newer version from remote.")
            set_last_download_date('first_aid_kit', remote_first_aid_kit_last_edited)

            DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'downloaded_data')
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dated_filename = f"first_aid_kit_{timestamp}.json"
            download_path = os.path.join(DOWNLOAD_DIR, dated_filename)
            with open(download_path, 'wb') as f:
                f.write(response_kit.content)
            logging.info(f"Saved historical copy of first_aid_kit.json to {download_path}")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Saved historical copy of first_aid_kit.json to {download_path}")

            commit_message = f"Update first_aid_kit.json from remote at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            push_to_github(commit_message, [LOCAL_DATA_FILE])
        except Exception as e:
            logging.error(f"Error during first_aid_kit.json update or push: {e}")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: {e}")
    elif local_first_aid_kit_last_edited and (remote_first_aid_kit_last_edited is None or local_first_aid_kit_last_edited > remote_first_aid_kit_last_edited):
        try:
            # Read, update timestamp, and rewrite local file to ensure Git detects change
            with open(LOCAL_DATA_FILE, 'r') as f:
                local_data = json.load(f)
            if isinstance(local_data, dict):
                for key, value in local_data.items():
                    if isinstance(value, dict) and 'last_edited' in value:
                        value['last_edited'] = datetime.now(timezone.utc).isoformat()
            with open(LOCAL_DATA_FILE, 'w') as f:
                json.dump(local_data, f, indent=4)
            logging.info(f"Rewrote {LOCAL_DATA_FILE} with updated timestamp for local changes.")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Rewrote {LOCAL_DATA_FILE} for local changes.")

            commit_message = f"Update first_aid_kit.json from local changes at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            push_to_github(commit_message, [LOCAL_DATA_FILE])
        except Exception as e:
            logging.error(f"Error during first_aid_kit.json push for local changes: {e}")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: {e}")

    # --- Compare and Download firstIAiditem.json ---
    local_first_aid_item_last_edited = None
    if os.path.exists(LOCAL_ITEMS_FILE):
        try:
            with open(LOCAL_ITEMS_FILE, 'r') as f:
                local_data = json.load(f)
                if isinstance(local_data, dict) and 'last_edited' in local_data:
                    last_edited_str = local_data['last_edited']
                    local_first_aid_item_last_edited = to_utc(datetime.fromisoformat(last_edited_str))
        except (json.JSONDecodeError, TypeError, FileNotFoundError) as e:
            logging.warning(f"Error reading local firstIAiditem.json for comparison: {e}")

    logging.info(f"firstIAiditem.json: Remote last_edited: {remote_first_aid_item_last_edited}, Local last_edited: {local_first_aid_item_last_edited}")
    if response_item and remote_first_aid_item_last_edited and (local_first_aid_item_last_edited is None or remote_first_aid_item_last_edited > local_first_aid_item_last_edited):
        try:
            with open(LOCAL_ITEMS_FILE, 'wb') as f:
                f.write(response_item.content)
            logging.info(f"Updated {LOCAL_ITEMS_FILE} with newer version from remote.")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Updated {LOCAL_ITEMS_FILE} with newer version from remote.")
            set_last_download_date('firstIAiditem', remote_first_aid_item_last_edited)

            DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'downloaded_data')
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dated_filename = f"firstIAiditem_{timestamp}.json"
            download_path = os.path.join(DOWNLOAD_DIR, dated_filename)
            with open(download_path, 'wb') as f:
                f.write(response_item.content)
            logging.info(f"Saved historical copy of firstIAiditem.json to {download_path}")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Saved historical copy of firstIAiditem.json to {download_path}")

            commit_message = f"Update firstIAiditem.json from remote at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            push_to_github(commit_message, [LOCAL_ITEMS_FILE])
        except Exception as e:
            logging.error(f"Error during firstIAiditem.json update or push: {e}")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: {e}")
    elif local_first_aid_item_last_edited and (remote_first_aid_item_last_edited is None or local_first_aid_item_last_edited > remote_first_aid_item_last_edited):
        try:
            # Read, update timestamp, and rewrite local file to ensure Git detects change
            with open(LOCAL_ITEMS_FILE, 'r') as f:
                local_data = json.load(f)
            if isinstance(local_data, dict) and 'last_edited' in local_data:
                local_data['last_edited'] = datetime.now(timezone.utc).isoformat()
            with open(LOCAL_ITEMS_FILE, 'w') as f:
                json.dump(local_data, f, indent=4)
            logging.info(f"Rewrote {LOCAL_ITEMS_FILE} with updated timestamp for local changes.")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Rewrote {LOCAL_ITEMS_FILE} for local changes.")

            commit_message = f"Update firstIAiditem.json from local changes at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            push_to_github(commit_message, [LOCAL_ITEMS_FILE])
        except Exception as e:
            logging.error(f"Error during firstIAiditem.json push for local changes: {e}")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: {e}")

    logging.info("Scheduled pinger script finished.")


if __name__ == "__main__":
    ping_site()