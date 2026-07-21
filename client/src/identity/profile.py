# Purpose:
# Create profile.json containing identity metadata
# Sign profile.json using the private key 
import json
from datetime import datetime, timezone
import os
from .keypair import KeyPair
from .signer import Signer
class ProfileCreator:
    def __init__(self, base_path: str):
        # Path to the user's /social/ directory 
        self.base_path = base_path
        # Keystore path for storing the private key
        self.keystore_path = os.path.join(self.base_path, "keystore")
        self.private_key_file = os.path.join(self.keystore_path, "private.key")
    
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
    
    def save_private_key(self, private_key: str):
        # Save private key to /social/keystore/private.key
        os.makedirs(self.keystore_path, exist_ok=True)
        with open(self.private_key_file, "w") as file:
            file.write(private_key)
    
    def create_profile(self, handle: str, display_name: str, bio: str):
        # High-level method that calls the three steps to create and save a signed profile.json
        # Step 1: Build JSON 
        profile, private_key = self.build_profile_json(handle, display_name, bio)
        # Step 2: Sign the profile JSON
        signed_profile = self.sign_profile_json(profile, private_key)
        # Step 3: Save the signed profile JSON
        profile_path = self.save_profile_json(signed_profile)
        # Step 4: Save private key to keystore
        self.save_private_key(private_key)
        # Add debug output
        print("Account created.")
        print("Public key:", signed_profile["publicKey"])
        print("Private key (store securely):", private_key)
        return profile_path

    
    


    
        

    