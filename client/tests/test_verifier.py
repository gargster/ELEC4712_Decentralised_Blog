import json
from src.identity.keypair import KeyPair
from src.identity.signer import Signer
from src.identity.verifier import Verifier

def test_verifier_valid_signature():
    kp = KeyPair()
    public_key = kp.public_key()
    private_key = kp.private_key()

    obj = {"publicKey": public_key, "handle": "bharat.social"}
    signer = Signer(private_key)
    sig = signer.sign_json(obj)

    v = Verifier(public_key)
    assert v.verify_json(obj, sig) is True

def test_verifier_invalid_signature():
    kp = KeyPair()
    public_key = kp.public_key()

    obj = {"publicKey": public_key, "handle": "bharat.social"}
    fake_sig = "ZmFrZXNpZw=="  # base64 of "fakesig"

    v = Verifier(public_key)
    assert v.verify_json(obj, fake_sig) is False
