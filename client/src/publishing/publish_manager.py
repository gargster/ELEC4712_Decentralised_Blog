import os
import json
from git import Repo
from src.identity.signer import Signer
from src.utils.identity_loader import load_identity

from src.config import ORG_URL

class PublishManager:
    def __init__(self, project_root):
        self.project_root = project_root

    def publish_to_org(self):
        identity = load_identity()
        identity_name = identity["activeIdentity"]
        repo_name = identity["repoPath"]  # e.g. "alice-social"
        remote_url = ORG_URL + repo_name + ".git"

        repo_root = os.path.join(self.project_root, repo_name)
        social_path = os.path.join(repo_root, "social")
        profile_path = os.path.join(social_path, "profile.json")

        print(f"[PUBLISH] Publishing {identity_name}.social to {remote_url}")

        repo = Repo(repo_root)

        # Set remote origin to ORG
        if "origin" in repo.remotes:
            repo.remotes.origin.set_url(remote_url)
        else:
            repo.create_remote("origin", remote_url)

        # Push repo
        repo.git.push("--set-upstream", "origin", "main")

        # Update profile.json
        with open(profile_path, "r") as f:
            profile = json.load(f)

        profile["repoURL"] = remote_url

        # Sign profile.json
        private_key_path = os.path.join(
            self.project_root,
            "client",
            "state",
            identity_name,
            "keystore",
            "private.key"
        )
        with open(private_key_path, "r") as f:
            private_key = f.read()

        signer = Signer(private_key)
        profile["signature"] = signer.sign_json(profile)

        # Save + commit + push
        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

        repo.git.add(profile_path)
        repo.git.commit("-m", "Update repoURL + signature")
        repo.remotes.origin.push()

        print("[PUBLISH] Complete.")
