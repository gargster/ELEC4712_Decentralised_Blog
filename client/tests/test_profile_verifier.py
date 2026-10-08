import json
import pytest
from src.identity.profile_verifier import ProfileVerifier
from src.identity.keypair import KeyPair
from src.identity.signer import Signer


def signed_profile():
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
    return profile


def test_profile_verifier_valid():
    profile = signed_profile()

    pv = ProfileVerifier(profile)
    verified = pv.verify()

    assert verified["handle"] == "bharat.social"
    assert verified["publicKey"] == profile["publicKey"]
    assert verified["repoURL"] == "https://github.com/bharat/social.git"


def test_profile_verifier_rejects_tampered_profile():
    profile = signed_profile()
    profile["displayName"] = "Mallory"

    with pytest.raises(ValueError, match="Invalid profile.json signature"):
        ProfileVerifier(profile).verify()
