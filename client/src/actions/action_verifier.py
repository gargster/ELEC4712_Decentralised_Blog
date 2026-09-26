from src.identity.verifier import Verifier
class ActionVerifier:
    @staticmethod
    def verify(action: dict) -> bool:
        """Verify an action using the public key and signature it contains."""
        try:
            public_key = action["author"]
            signature = action["signature"]
        except (KeyError, TypeError):
            return False

        try:
            return Verifier(public_key).verify_json(action, signature)
        except (TypeError, ValueError):
            return False
