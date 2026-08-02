import os
import json
from src.identity.verifier import Verifier
from src.utils.identity_loader import load_identity

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
        # extract Base64 aignature
        signature_b64 = action_json["signature"]
        # create verifier using public key
        verifier = Verifier(author_key)
        # Verify message + signature 
        return verifier.verify_json(action_json, signature_b64)

    def run(self):
        # core replication workflow:
        # 1. Load following.json
        # 2. Load feed.json
        # 3. Scan /social/actions for all JSON files
        # 4. For each action: check if author is followed, verify signature, insert into feed.json
        following = self.load_following()
        feed = self.load_feed()
        # project root (ELEC4712_Decentralised_Blog/)
        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(__file__)
            )
        )
        followed_keys = {f["publicKey"] for f in following}

        for entry in following:
            repo_url = entry["repoURL"]

            # repoURL is relative to project root 
            repo_social_path = os.path.join(project_root, repo_url, "social")
            actions_dir = os.path.join(repo_social_path, "actions")

            # scan actions in this repo 
            for name in os.listdir(actions_dir):
                if not name.endswith(".json"):
                    continue

                path = os.path.join(actions_dir, name)
                with open(path, "r") as file:
                    action = json.load(file)

                # Only replicate actions from authors we follow
                if action["author"] not in followed_keys:
                    continue
                # Avoid duplicates in feed.json
                if any(a["id"] == action["id"] for a in feed["feed"]):
                    continue
                # Verify signature
                if not self.verify_action(action):
                    print("Invalid signature:", action["id"])
                    continue
                # Insert into feed
                feed["feed"].append(action)

        self.save_feed(feed)
        print(f"Replication complete. Feed now contains {len(feed['feed'])} actions.")
