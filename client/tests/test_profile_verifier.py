import json
from pathlib import Path
from src.discovery.profile_verifier import ProfileVerifier
from src.identity.keypair import KeyPair
from src.identity.signer import Signer

def test_profile_verifier_valid(tmp_path):
    profile_path = tmp_path / "profile.json"

    kp = KeyPair()
    public_key = kp.public_key()
    private_key = kp.private_key()

    profile = {
        "publicKey": public_key,
        "handle": "bharat.social",
        "repoURL": "https://github.com/bharat/social.git",
        "displayName": "Bharat",
        "bio": "Student at USYD",
        "created": "2026-06-28T19:57:00Z",
    }
    signer = Signer(private_key)
    profile["signature"] = signer.sign_json(profile)

    profile_path.write_text(json.dumps(profile))

    pv = ProfileVerifier(str(profile_path))
    verified = pv.verify()

    assert verified["handle"] == "bharat.social"
    assert verified["publicKey"] == public_key
    assert verified["repoURL"] == "https://github.com/bharat/social.git"
