# Purpose :
# Sign JSON objects using the user's private key.
# Followers verify signatures using the public key 
import json
import nacl.signing
import nacl.encoding
class Signer:
    def __init__(self, private_key_hex: str):
        # Convert hex string to raw bytes
        private_key_bytes = bytes.fromhex(private_key_hex)
        # Create a SigningKey object from the raw bytes
        # This loads the actual Ed25519 private key for signing
        self.signing_key = nacl.signing.SigningKey(private_key_bytes)
    def sign_json(self, obj: dict) -> str:
        # Convert JSON to canonical string (sorted keys)
        # Remove signature field before signing
        obj_to_sign = {k: v for k, v in obj.items() if k != "signature"}
        message = json.dumps(obj_to_sign, sort_keys=True).encode('utf-8')
        # Sign the message using the Ed25519 private key
        signed = self.signing_key.sign(message)
        # Extract only the signature (not the signed message).
        signature_bytes = signed.signature
        # Encode signature to Base64 string for JSON storage
        return nacl.encoding.Base64Encoder.encode(signature_bytes).decode() 
    
    