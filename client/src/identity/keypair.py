# Generates an Ed25519 keypair for user identity
# Public key goes into profile.json
# Private key is used for signing actions

import nacl.signing
import nacl.encoding
class KeyPair:
    def __init__(self):
        # Generate a new Ed25519 private signing key
        # This key is raw binary data internally
        self.signing_key = nacl.signing.SigningKey.generate()
        # Derive the corresponding verification public verification key
        self.verify_key = self.signing_key.verify_key
    def public_key(self):
        # Convert raw public key bytes to hex string  
        hex_bytes = self.verify_key.encode(encoder=nacl.encoding.HexEncoder)
        # Convert hex bytes to normal Python string
        hex_string = hex_bytes.decode()
        # Add prefix so clients know which algorithm this key uses
        return "ed25519:" + hex_string
    def private_key(self):
        # Convert raw private key bytes to hex string
        hex_bytes = self.signing_key.encode(encoder=nacl.encoding.HexEncoder)
        # Convert hex bytes to normal Python string
        hex_string = hex_bytes.decode()
        return hex_string


    
