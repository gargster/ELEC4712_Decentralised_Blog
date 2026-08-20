import os
import json

import git
from src.identity.verifier import Verifier
from src.utils.identity_loader import load_identity
from git import Repo
# Minimal replication engine which reads follow.json, 
# scans /social/actions for JSON files,
# verifies signatures and insert valid actions into feed.json
class Replicator:
    def __init__(self, client_root):
        # client_root = client/ directory 
        self.client_root = client_root

        identity = load_identity()
        identity_name = identity["activeIdentity"]
        self.follow_file = os.path.join(client_root, "state", identity_name, "following.json")
        self.feed_file = os.path.join(client_root, "state", identity_name, "feed.json")

    def load_following(self):
        # load the list of accounts the user follows.
        with open(self.follow_file, "r") as file:
            return json.load(file)["following"]

    def load_feed(self):
        # Load feed.json, creating it if missing which stores all replicated actions
        # Later this will transform to a feed DB with 
        # ordering, reply linking, like/follow metadata
        if not os.path.exists(self.feed_file):
            with open(self.feed_file, "w") as file:
                json.dump({"feed": []}, file, indent=2)
        with open(self.feed_file, "r") as file:
            return json.load(file)

    def save_feed(self, feed):
        # write updated feed.json back to disk
        with open(self.feed_file, "w") as file:
            json.dump(feed, file, indent=2)

    def ensure_local_clone(self, handle: str, repo_url: str):
        # clone the remote URL into:
        # client/following_repos<handle>-social/
        # If already cloned, run:
        # git fetch origin, git pull 
        clone_root = os.path.join(self.client_root, "following_repos")
        os.makedirs(clone_root, exist_ok=True)
        # local clone path for this followed user 
        local_path = os.path.join(clone_root, f"{handle.split('.')[0]}-social")
        if not os.path.exists(local_path):
            # Clone the remote repo
            print(f"[Replicator] Cloining remote repo: {repo_url}")
            Repo.clone_from(repo_url, local_path)
        else:
            # Repo already cloned, fetch and pull latest changes
            print(f"[Replicator] Fetching and pulling latest changes for: {handle}")
            repo = Repo(local_path)
            origin = repo.remotes.origin
            origin.fetch()
            origin.pull("main")

        return local_path

    def parse_actions(self, local_repo_path: str):
        # Read all JSON files inside: <local_repo_path>/social/actions/*.json
        # These are the replicated social actions 
        actions_dir = os.path.join(local_repo_path, "social", "actions")
        if not os.path.exists(actions_dir):
            return []
        actions = []
        for filename in os.listdir(actions_dir):
            if filename.endswith(".json"):
                with open(os.path.join(actions_dir, filename), "r") as file:
                    action = json.load(file)
                    actions.append(action)
        return actions


    def list_action_files(self):
        # scan /social/actions for all JSON files.
        # currently all authors publish into same repo, so replication
        # is just scanning this repo
        # Later:
        # we will fetch remote repo and scan each repos's respective /social/actions
        actions_dir = os.path.join(self.social_root, "actions")
        files = []
        for name in os.listdir(actions_dir):
            if name.endswith(".json"):
                files.append(os.path.join(actions_dir, name))
        return files

    def verify_action(self, action_json):
        # verify the signature of a social action
        # actions_json contains author (publicKey), signature and other fields
        # extract author's public key
        author_key = action_json["author"]
        # extract Base64 signature
        signature_b64 = action_json["signature"]
        # create verifier using public key
        verifier = Verifier(author_key)
        # Verify message + signature 
        return verifier.verify_json(action_json, signature_b64)

    # NEW model replication: git pull cloned repos
    def sync_following_repos(self):
        following_root = os.path.join(self.client_root, "following_repos")
        if not os.path.exists(following_root):
            return

        for name in os.listdir(following_root):
            repo_path = os.path.join(following_root, name)
            if not os.path.isdir(repo_path):
                continue

            print(f"[REPLICATE] Pulling updates for {name}...")
            repo = git.Repo(repo_path)
            repo.remotes.origin.pull()

    def run(self):
        # core replication workflow:
        # 1. Load following.json
        # 2. Load feed.json
        # 3. For each followed user:
        # - Clone or fetch their remote Git repo
        # - Parse /social/actions/*.json from the cloned repo
        # - Verify signature of each action
        # - Insert valid actions into feed.json

        # NEW: Pull updates from ORG clones
        self.sync_following_repos()

        following = self.load_following()
        feed = self.load_feed()
        # Track existing action IDs to avoid duplicates
        existing_ids = {action["id"] for action in feed["feed"]}

        for entry in following:
            handle = entry["handle"]
            repoURL = entry["repoURL"]
            # 1. Clone or fetch remote repo
            local_repo_path = self.ensure_local_clone(handle, repoURL)
            # 2. Parse ations from cloned repo
            actions = self.parse_actions(local_repo_path)
            # 3. Verify + merge actions  
            for action in actions:
                if action["id"] in existing_ids:
                    continue
                if not self.verify_action(action):
                    print(f"[Replicator] Invalid signature for action {action['id']}")
                    continue
                feed["feed"].append(action)
                existing_ids.add(action["id"])

        # 4. Save updated feed.json
        self.save_feed(feed)
        print(f"[Replicator] Replication complete. Feed now contains {len(feed['feed'])} actions.")

       