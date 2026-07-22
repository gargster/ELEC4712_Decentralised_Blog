import os
import json
from src.identity.profile import ProfileCreator

def test_profile_creation(tmp_path):
    social_path = tmp_path / "social"
    os.makedirs(social_path)

    creator = ProfileCreator(str(social_path))
    path = creator.create_profile("bharat.social", "Bharat", "Student at USYD")

    assert os.path.exists(path)

    with open(path) as f:
        data = json.load(f)

    assert data["handle"] == "bharat.social"
    assert data["displayName"] == "Bharat"
    assert data["bio"] == "Student at USYD"
    assert data["publicKey"].startswith("ed25519:")
