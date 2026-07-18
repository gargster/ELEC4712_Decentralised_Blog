# Purpose:
# Create profile.json containing identity metadata
# Sign profile.json using the private key 
import json
from datetime import datetime, timezone
from .keypair import KeyPair
from .signer import Signer
class ProfileCreator:
    def __init__(self, base_path: str):
        # Path to the user's /social/ directory 
        self.base_path = base_path
    
    def build_profile_json(self, handle: str, display_name: str, bio: str):
        # Step 1: Build the profile JSON object.
        keypair = KeyPair()
        public_key = keypair.public_key()
        private_key = keypair.private_key()
        
        profile = {
            "publicKey": public_key,
            "handle": handle,
            "displayName": display_name,
            "bio": bio,
            "created": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }
        # Return both the profile object and private key for signing
        return profile, private_key
    
    def sign_profile_json(self, profile: dict, private_key: str):
        # Step 2: Sign the profile JSON using the private key
        signer = Signer(private_key)
        signature = signer.sign_json(profile)
        # Add the signature to the profile JSON
        profile["signature"] = signature
        return profile
    
    def save_profile_json(self, profile: dict):
        # Step 3: Save profile.json to the user's /social/ directory
        profile_path = f"{self.base_path}/profile.json"
        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)
        return profile_path
    
    def create_profile(self, handle: str, display_name: str, bio: str):
        # High-level method that calls the three steps to create and save a signed profile.json
        # Step 1: Build JSON 
        profile, private_key = self.build_profile_json(handle, display_name, bio)
        # Step 2: Sign the profile JSON
        signed_profile = self.sign_profile_json(profile, private_key)
        # Step 3: Save the signed profile JSON
        profile_path = self.save_profile_json(signed_profile)
        # Add debug output
        print("Account created.")
        print("Public key:", signed_profile["publicKey"])
        print("Private key (store securely):", private_key)
        return profile_path

    
    


    
        

    