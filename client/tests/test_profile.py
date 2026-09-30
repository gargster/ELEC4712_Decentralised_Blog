import os
import json
from src.identity import profile
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


def test_canonical_creation_does_not_create_unused_index(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(profile.subprocess, "run", lambda *args, **kwargs: None)

    repo_path, profile_path = ProfileCreator(str(project_root)).create_profile(
        "canonical.social",
        "Canonical",
        "Genesis",
    )

    assert os.path.isfile(profile_path)
    assert os.path.isdir(os.path.join(repo_path, "social", "actions"))
    assert not os.path.exists(
        os.path.join(repo_path, "social", "index.json")
    )
