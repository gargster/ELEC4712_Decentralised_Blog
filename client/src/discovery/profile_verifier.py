import json
from src.identity.verifier import Verifier

class ProfileVerifier:
    def __init__(self, profile_dict: dict):
        """
        Accepts an already-loaded profile.json dictionary.
        """
        self.profile = profile_dict

    def verify(self):
        profile = self.profile

        public_key = profile["publicKey"]
        signature = profile["signature"]

        # Remove signature before verifying
        unsigned_profile = profile.copy()
        unsigned_profile.pop("signature")

        verifier = Verifier(public_key)

        if not verifier.verify_json(unsigned_profile, signature):
            raise ValueError("Invalid profile.json signature")

        return {
            "handle": profile["handle"],
            "publicKey": public_key,
            "repoURL": profile["repoURL"]
        }
