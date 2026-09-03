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
    def __init__(self, client_root, social_root):
        # client_root = client/ directory 
        self.client_root = client_root
        self.social_root = social_root

        identity = load_identity()
        identity_name = identity["activeIdentity"]
        self.follow_file = os.path.join(client_root, "state", identity_name, "following.json")
        self.feed_file = os.path.join(client_root, "state", identity_name, "feed.json")

    # NEW model replication: git pull cloned repos
    def sync_following_repos(self):
        #following_root = os.path.join(self.client_root, "following_repos")
        following_root = os.path.join(self.social_root, "following_repos")
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
        # NEW: Pull updates from ORG clones
        self.sync_following_repos()
        

       