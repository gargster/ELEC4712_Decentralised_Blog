# Purpose:
# Shared base class for all social actions (post, reply, like, follow)
import json
from datetime import datetime, timezone
import os

from src.identity.signer import Signer
from src.identity.keypair import KeyPair

class ActionBase:
    def __init__(self, social_path: str):
        self.social_path = social_path
        self.actions_path = os.path.join(social_path, "actions")
        os.makedirs(self.actions_path, exist_ok=True)
    
    # Build fields common to all actions
    def _build_base(self, action_type: str, public_key: str, action_id: str):
        return {
            "id": action_id,
            "type": action_type,
            "author": public_key,
            "created": self._timestamp()
        }
    # Child classes override this to add extra fields
    def _extend(self, obj: dict, **kwargs):
        return obj
    
    # Template method: shared creation workflow
    def _create(self, action_type: str, **kwargs):
        public_key, private_key = self._load_identity()
        action_id = self._next_id(action_type)
        # Base fields
        obj = self._build_base(action_type, public_key, action_id)
        # Child-specific fields
        obj = self._extend(obj, **kwargs)
        # Sign + write
        self._sign_action(obj, private_key)
        path = self._write(obj)
        return path, obj

    def _next_id(self, prefix: str) -> str:
        # Generate the next sequential ID for this action type.
        # Example: 
        # prefix = "post", existing files = ["post_1.json", "post_2.json"] 
        # => next ID = "post-003"
        # 1. List all files inside /social/actions/
        all_files  = os.listdir(self.actions_path)
        # 2. Filter only files which match the patter "<prefix>-XXX.json"
        # e.g. "post-001.json", "post-002.json"
        existing  = [
            name for name in all_files
            if name.startswith(prefix + "-") and name.endswith(".json")
        ]
        # This list will store extracted numeric parts of the filenames (e.g. 1,2,10)
        numbers = []
        # 3. Extract the numeric part of each filename
        # Example: "post-001.json"
        # prefix = "post"
        # name[len(prefix)+1 : -len(".jsom")] => name[5, -5] -> "001"
        for name in existing:
            try:
                # Extract the number between "post-" and ".json"
                num_str = name[len(prefix) + 1 : -len(".json")]
                num = int(num_str)
                numbers.append(num)
            except ValueError:
                # If the filename is malformed, skip it
                continue
        # 4. Determine the next number, if no existing files, start at 1
        next_num = (max(numbers) + 1) if numbers else 1

        # 5. Format the ID as "<prefix>-XXX" with zero-padding
        return f"{prefix}-{next_num:03d}" 
    def _timestamp(self) -> str:
        # Return the current UTC timestamp in ISO 8601 format with 'Z' suffix
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
   
    def _sign_action(self, action: dict, private_key: str) -> None:
        # Sign the action JSON using the provided private key
        signer = Signer(private_key)
        action["signature"] = signer.sign_json(action)

    def _write(self, action: dict) -> str:
        # Write the JSON object to /social/actions/<id>.json.
        # Note: The action object already contains and "id" (added earlier by the action creator using_next_id())
        # This simply uses that existing ID to name the file
        filename = f"{action['id']}.json"
        path = os.path.join(self.actions_path, filename)
        # Save the JSON object to disk
        with open(path, "w") as f:
            json.dump(action, f, indent=2)
        return path
    
    def _load_identity(self):
        # TEMPORARY:
        # For early testing, generate a new keypair each time.
        # Later this will load the user's real keys from profile.json + keystor
        # keyPair = KeyPair()
        # return keyPair.public_key(), keyPair.private_key()
        
        # Load publicKey from /social/profile.json
        profile_path = os.path.join(self.social_path, "profile.json")
        with open(profile_path, "r") as file:
            profile = json.load(file)
        public_key = profile["publicKey"]

        # Load privateKey from /social/keystore/private.key
        keystore_path = os.path.join(self.social_path, "keystore", "private.key")
        with open(keystore_path, "r") as file:
            private_key = file.read().strip()
        return public_key, private_key
    

    
    
    
