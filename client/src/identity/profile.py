# Purpose:
# Create profile.json containing identity metadata
# Sign profile.json using the private key 
import json
from datetime import datetime, timezone
import os
import subprocess
from .keypair import KeyPair
from .signer import Signer

from src.utils.identity_loader import load_identity

class ProfileCreator:
    def __init__(self, project_root: str):
        self.project_root = project_root

    def create_repo_structure(self, repo_name):
        # Automatically creates the /social/ directory structure for the user
        # e.g. <repo_name>/social/actions/
        repo_path = os.path.join(self.project_root, repo_name)
        social_path = os.path.join(repo_path, "social")
        # Create all required folders
        os.makedirs(os.path.join(social_path, "actions"), exist_ok=True)
        os.makedirs(os.path.join(social_path, "keystore"), exist_ok=True)
        os.makedirs(os.path.join(social_path, "discovery"), exist_ok=True)
        os.makedirs(os.path.join(social_path, "media"), exist_ok=True)
        os.makedirs(os.path.join(social_path, "moderation"), exist_ok=True)
        # Create empty index.json 
        with open(os.path.join(social_path, "index.json"), "w") as f:
            json.dump({}, f, indent=2)

        return repo_path, social_path

    def generate_profile(self, handle: str, display_name: str, bio: str, repo_name: str):
        # Generate + sign profile.json
        keypair = KeyPair()
        public_key = keypair.public_key()
        private_key = keypair.private_key()

        # Build path to the bar remote repo  
        remotes_root = os.path.join(self.project_root, "remotes")
        bare_remote_path = os.path.join(remotes_root, f"{repo_name}.git")

        profile = {
            "publicKey": public_key,
            "handle": handle,
            "repoURL": bare_remote_path,
            "displayName": display_name,
            "bio": bio,
            "created": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }
        # Sign profile.json using the private key
        signer = Signer(private_key)
        profile["signature"] = signer.sign_json(profile)

        return profile, private_key
       
    def save_profile_json(self, social_path: str, profile: dict):
        # Save profile.json inside: <repo>/social/profile.json
        profile_path = os.path.join(social_path, "profile.json")
        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)
        return profile_path

    def save_private_key(self, social_path: str, private_key: str):
        # Save private key inside: <repo>/social/keystore/private.key
        keystore_path = os.path.join(social_path, "keystore")
        private_key_file = os.path.join(keystore_path, "private.key")
        with open(private_key_file, "w") as file:
            file.write(private_key)

    def update_directory(self, client_root, handle, repo_name):
        # Automatically update the directory.json file in the client root to include the new handle to repo mapping
        directory_path = os.path.join(client_root, "directory.json")
        # Create directory.json if it doesn't exist
        if not os.path.exists(directory_path):
            with open(directory_path, "w") as f:
                json.dump({}, f, indent=2)

        # Load the existing directory data
        with open(directory_path, "r") as f:
            directory_data = json.load(f)

        # Ensure directory_data is a dict 
        if not isinstance(directory_data, dict):
            directory_data = {}

        # FIXED: write full object, not just repo_name 
        directory_data[handle] = {
            "localPath": repo_name,
            "repoURL": f"{self.project_root}/remotes/{repo_name}.git"
        }

        # Save the updated directory data
        with open(directory_path, "w") as f:
            json.dump(directory_data, f, indent=2)

    def git_init(self, repo_path):
        # Automatically runs:
        # git init 
        # git add .
        # git commit -m "Initial account creation"
        # This replaces manual git init 
        # 1. Init working repo
        subprocess.run(["git", "init"], cwd=repo_path)
        subprocess.run(["git", "add", "."], cwd=repo_path)
        subprocess.run(["git", "commit", "-m", "Initial account creation"], cwd=repo_path)
        # 2. Create local bar remote under /remotes/<repo>.git
        repo_name = os.path.basename(repo_path)
        remotes_root= os.path.join(self.project_root, "remotes")
        os.makedirs(remotes_root, exist_ok=True)

        bare_remote_path = os.path.join(remotes_root, f"{repo_name}.git")
        subprocess.run(["git", "init", "--bare", bare_remote_path])

        # 3. Add remote origin 
        subprocess.run(["git", "remote", "add", "origin", bare_remote_path], cwd=repo_path)

        # FIXED: use main branch
        # Rename branch to main (safe even if already main)
        subprocess.run(["git", "branch", "-M", "main"], cwd=repo_path)
        # Push main
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=repo_path)

        print(f"Initialized git repo at {repo_path} and pushed to bare remote at {bare_remote_path}")
    
    def create_profile(self, handle: str, display_name: str, bio: str):
        # Convert handle to repo name (e.g. alice.social -> alice-social)
        repo_name = f"{handle.split('.')[0]}-social"
        # 1. Auto-create repo structure
        repo_path, social_path = self.create_repo_structure(repo_name)
        # 2. Build + sign profile.json 
        profile, private_key = self.generate_profile(handle, display_name, bio, repo_name)
        # 3. Save profile.json + private key
        profile_path = self.save_profile_json(social_path, profile)
        self.save_private_key(social_path, private_key)
        # 4. Update directory.json in client root
        client_root = os.path.join(self.project_root, "client")
        self.update_directory(client_root, handle, repo_name)
        # 5. Create state folder + required files
        identity_name = handle.split('.')[0]  # e.g. "alice" from "alice.social"
        state_path = os.path.join(client_root, "state", identity_name)
        os.makedirs(state_path, exist_ok=True)
        # Map filename to schemas
        state_files = {
            "following.json": {"following": []},
            "feed.json": {"feed": []}
        }
        # Create state files with initial content
        for filename, content in state_files.items():
            file_path = os.path.join(state_path, filename)
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    json.dump(content, f, indent=2)

        # 6. Initialize git repo
        self.git_init(repo_path)
        # Debug output
        print("Account created:", handle)
        print("Repo:", repo_name)
        print("Public key:", profile["publicKey"])
        print("Private key:", private_key)

        return profile_path

    
    


    
        

    