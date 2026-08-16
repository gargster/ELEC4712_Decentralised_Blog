import os
import json
from src.identity.profile import ProfileCreator


def test_profile_creation(tmp_path):
    # Create fake project root
    project_root = tmp_path / "project"
    os.makedirs(project_root)

    # Create client/ folder (ProfileCreator expects this)
    client_root = project_root / "client"
    os.makedirs(client_root, exist_ok=True)

    # Create identity.json (required for keystore path)
    identity_json_path = client_root / "identity.json"
    with open(identity_json_path, "w") as f:
        json.dump({"activeIdentity": "bharat"}, f)

    # Run profile creation
    creator = ProfileCreator(str(project_root))
    profile_path = creator.create_profile(
        "bharat.social",
        "Bharat",
        "Student at USYD"
    )

    # Verify file exists
    assert os.path.exists(profile_path)

    # Load and verify contents
    with open(profile_path) as f:
        data = json.load(f)

    assert data["handle"] == "bharat.social"
    assert data["displayName"] == "Bharat"
    assert data["bio"] == "Student at USYD"
    assert data["publicKey"].startswith("ed25519:")
