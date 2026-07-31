import json
import os
from src.identity.verifier import Verifier
# Verifies /social/profile.json by:
# loading profile.json, using publicKey to verify signature 
# and then returning (handle, publicKey, repoURL) if valid
class ProfileVerifier:
    def __init__(self, profile_path: str):
        self.profile_path = profile_path 

    def load_profile(self):
        with open(self.profile_path, "r") as file:
            return json.load(file)

    def verify(self):
        profile = self.load_profile()
        public_key = profile["publicKey"]
        signature = profile["signature"]
        verifier = Verifier(public_key)
        # Verify the profile JSON
        if not verifier.verify_json(profile, signature):
            raise ValueError("Invalid profile.json signature")
        handle = profile["handle"]
        repo_url = profile["repoURL"]
        return {
            "handle": handle,
            "publicKey": public_key,
            "repoURL": repo_url
        }

    
