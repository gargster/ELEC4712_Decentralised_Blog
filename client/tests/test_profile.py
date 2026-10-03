import os
import json
import pytest
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
    repo_path, profile_path = creator.create_profile(
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
    assert os.path.isdir(os.path.join(repo_path, "social", "actions"))


def test_normal_profile_creation_rejects_canonical_handle(tmp_path):
    creator = ProfileCreator(str(tmp_path))

    with pytest.raises(ValueError, match="reserved for the configured canonical"):
        creator.create_profile("canonical.social", "Canonical", "Genesis")
