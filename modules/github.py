import requests
import toml
import os
from track_data import open_json, save_json

# List of repositories to track
repositories = [
    "theroyallab/tabbyAPI",
    "SillyTavern/SillyTavern",
    "LostRuins/koboldcpp",
    "oobabooga/text-generation-webui",
    "comfyanonymous/ComfyUI"
]

config = toml.load("settings.toml")

# Your GitHub personal access token
access_token = config['github']['auth_token']

# Headers to use in the API request
headers = {
    'Authorization': f'token {access_token}',
    'Accept': 'application/vnd.github.v3+json'
}

# Base URL for GitHub API
base_url = 'https://api.github.com/repos/'

# Function to get the latest commit from the default branch
def get_latest_commit(repo):
    url = f"{base_url}{repo}/commits"
    params = {'per_page': 1}  # Fetch only the latest commit
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        return data[0]['sha'], data[0]['commit']['message']  # Return the SHA and message of the latest commit
    else:
        return None, None

# Function to get the latest release or commit
def get_latest_release_or_commit(repo):
    url = f"{base_url}{repo}/releases/latest"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return 'release', data.get('id'), data.get('tag_name')  # Returning type, ID, and tag name (version)
    elif response.status_code == 404:
        # If no release found, fetch the latest commit
        commit_id, commit_message = get_latest_commit(repo)
        if commit_id:
            return 'commit', commit_id, commit_message  # Return the commit message instead of SHA
        else:
            return 'error', None, None
    else:
        return 'error', None, None

# Function to collect status updates as a string
def get_status_updates(email_read=False):
    # File to store the last known releases and commits
    tracking_file = os.path.join(os.path.dirname(__file__), 'github.json')
    tracking_data = open_json(tracking_file)
    
    # Initialize the tracking data if it doesn't exist
    if not tracking_data:
        tracking_data = {
            "repos": {},
            "seen_updates": {} if email_read else {}
        }
    
    # If email was read, move tracked repos to seen updates
    if email_read:
        for repo in tracking_data.get("repos", {}):
            tracking_data["seen_updates"][repo] = tracking_data["repos"][repo]
    
    status_updates = "<tr><td class='content'>"
    status_updates += f"<h3>Github Repo Updates</h3>"
    
    for repo in repositories:
        item_type, item_id, item_name = get_latest_release_or_commit(repo)
        repo_link = f"https://github.com/{repo}"  # Creating link to the repository
        
        # Store current data in tracking
        if item_type != 'error' and item_id:
            tracking_data.setdefault("repos", {})[repo] = {
                "type": item_type,
                "id": item_id,
                "name": item_name
            }
            
            # Check if this is new compared to seen updates
            is_new = (
                repo not in tracking_data.get("seen_updates", {}) or 
                tracking_data["seen_updates"][repo]["id"] != item_id
            )
            
            if is_new:
                if item_type == 'release':
                    status_updates += f"<a href='{repo_link}'>{repo}</a> (New!)<br>New release<br>Version: {item_name}<br><br>"
                else:
                    status_updates += f"<a href='{repo_link}'>{repo}</a> (New!)<br>New commit<br>Message: {item_name}<br><br>"
            else:
                if item_type == 'release':
                    status_updates += f"<a href='{repo_link}'>{repo}</a><br>No new release<br>Current Version: {item_name}<br><br>"
                else:
                    status_updates += f"<a href='{repo_link}'>{repo}</a><br>No new commit<br>Current Message: {item_name}<br><br>"
        else:
            status_updates += f"<a href='{repo_link}'>{repo}</a><br>No release or commit information available.<br><br>"
    
    status_updates += "</td></tr>"

    save_json(tracking_file, tracking_data)

    return ''.join(status_updates)
