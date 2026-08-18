import os
import json
from git import Repo
from src.identity.signer import Signer
from src.utils.identity_loader import load_identity

from src.config import ORG_URL

class PublishManager:
    def __init__(self, project_root):
        self.project_root = project_root

    def publish(self, remote_url):
        # Load identity.json to get the active identity
        identity = load_identity()
        identity_name = identity["activeIdentity"]

        repo_root = os.path.join(self.project_root, identity["repoPath"])
        social_path = os.path.join(repo_root, "social")
        profile_path = os.path.join(social_path, "profile.json")

        print(f"Publishing identity {identity_name}.social...")
        print(f"Setting remote origin to: {remote_url}")

        repo = Repo(repo_root)
        # Set remote origin  
        if "origin" in repo.remotes:
            repo.remotes.origin.set_url(remote_url)
        else:
            repo.create_remote("origin", remote_url)

        # Push repo
        print("Pushing repo to hosting provider...")
        repo.git.push("--set-upstream", "origin", "main")
        # Load + update profile.json
        with open(profile_path, "r") as f:
            profile = json.load(f)
        profile["repoURL"] = remote_url

        # NEW: Load private key from client/state/<identity>/keystore/
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

        # Save updated profile.json
        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

        # Commit + push updated profile.json
        repo.git.add(profile_path)
        repo.git.commit("-m", "Update repoURL to hosted provider")
        repo.git.push()

        # Update directory.json 
        client_root = os.path.join(self.project_root, "client")
        directory_path = os.path.join(client_root, "directory.json")

        with open(directory_path, "r") as f:
            directory_data = json.load(f)

        
        # FIXED: preserve full structure
        directory_data[profile["handle"]] = {
            "localPath": identity["repoPath"],
            "repoURL": remote_url
        }

        with open(directory_path, "w") as f:
            json.dump(directory_data, f, indent=2)

        print("Publish complete! Your identity is now hosted.")

    def publish_to_org(self):
        # Publish the active identity's repo to the shared GitHub org
        # This doesn not replace normal publish() flow, but simply 
        # re-publishes the repo to the org
        identity = load_identity()
        repo_name = identity["repoPath"] # e.g. "alice-social"
        remote_url = ORG_URL + repo_name + ".git"

        print(f"[ORG PUBLISH] Publishing to {remote_url}")
        self.publish(remote_url) 

        repo_root = os.path.join(self.project_root, repo_name)
        repo = Repo(repo_root)

        if "origin" in repo.remotes:
            repo.remotes.origin.set_url(remote_url)
        else:
            repo.create_remote("origin", remote_url)

        print("[ORG PUBLISH] Org remote set as default. All future actions will push here.")




        

    

            




