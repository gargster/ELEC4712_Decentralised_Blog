import json
import nacl.signing
import nacl.encoding

class Verifier:
    def __init__(self, public_key_str: str):
        # remove "ed25519:" prefix if present
        if public_key_str.startswith("ed25519:"):
            public_key_str = public_key_str[len("ed25519:"):]
        # convert hex public key to bytes
        public_key_bytes = bytes.fromhex(public_key_str)
        # create VerifyKey object
        self.verify_key = nacl.signing.VerifyKey(public_key_bytes)

    def verify_json(self, obj: dict, signature_b64: str) -> bool:
        # remove signature field before verifying
        obj_no_sig = dict(obj)
        if "signature" in obj_no_sig:
            del obj_no_sig["signature"]
        # canonical JSON (same as signing)
        message = json.dumps(obj_no_sig, sort_keys=True).encode("utf-8")
        # decode Base64 signature
        try:
            signature_bytes = nacl.encoding.Base64Encoder.decode(signature_b64)
        except:
            return False 
        # verify
        try:
            self.verify_key.verify(message, signature_bytes)
            return True 
        except Exception:
            return False 
        
        