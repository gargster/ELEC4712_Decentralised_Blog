import json
from src.identity.keypair import KeyPair
from src.identity.signer import Signer

def test_keypair_generation():
    kp = KeyPair()
    assert kp.public_key().startswith("ed25519:")
    assert len(kp.private_key()) > 0

def test_signing_json():
    kp = KeyPair()
    signer = Signer(kp.private_key())

    obj = {"author": kp.public_key(), "msg": "hello"}
    sig = signer.sign_json(obj)

    assert isinstance(sig, str)
    assert len(sig) > 0
