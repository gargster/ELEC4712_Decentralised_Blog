import os
import json
from datetime import datetime, timezone
# Manages follow.json (local list of repos the user follows)
# This file is not signed or pushed, but is private to the client
class FollowManager:
    def __init__(self, client_root: str):
        # following.json will live in the client root
        self.client_root = client_root
        self.follow_file = os.path.join(client_root, "following.json")
        # If file doesn't exist, create an empty structure
        if not os.path.exists(self.follow_file):
            with open(self.follow_file, "w") as file:
                json.dump({"following": []}, file, indent=2)

    def load(self):
        # Load following.json
        with open(self.follow_file, "r") as file:
            return json.load(file)

    def save(self, data):
        # Save following.json
        with open(self.follow_file, "w") as file:
            json.dump(data, file, indent=2)

    def add_follow(self, handle: str, public_key: str, repo_url: str):
        # Add a new entry to following.json with handle, publicKey, repoURL and added (timestamp)
        data = self.load()
        entry = {
            "handle": handle,
            "publicKey": public_key,
            "repoURL": repo_url,
            "added": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }
        data["following"].append(entry)
        self.save(data)
        return entry

    
