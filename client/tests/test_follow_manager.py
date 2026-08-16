import json
from pathlib import Path
from src.replication.follow_manager import FollowManager

def test_follow_manager_creates_file_if_missing(tmp_path, monkeypatch):
    client_root = str(tmp_path)

    # Fake identity
    def fake_load_identity():
        return {"activeIdentity": "bharat", "repoPath": "bharat-social"}

    monkeypatch.setattr("src.replication.follow_manager.load_identity", fake_load_identity)

    # Create required directory structure
    state_dir = tmp_path / "state" / "bharat"
    state_dir.mkdir(parents=True)

    fm = FollowManager(client_root)
    data = fm.load()
    assert "following" in data
    assert data["following"] == []

def test_follow_manager_add_follow(tmp_path, monkeypatch):
    client_root = str(tmp_path)

    def fake_load_identity():
        return {"activeIdentity": "bharat", "repoPath": "bharat-social"}

    monkeypatch.setattr("src.replication.follow_manager.load_identity", fake_load_identity)

    # Create required directory structure
    state_dir = tmp_path / "state" / "bharat"
    state_dir.mkdir(parents=True)

    fm = FollowManager(client_root)
    entry = fm.add_follow(
        handle="alice.social",
        public_key="ed25519:abc123",
        repo_url="https://github.com/alice/social.git",
    )

    data = fm.load()
    assert len(data["following"]) == 1
    assert data["following"][0]["handle"] == "alice.social"
    assert data["following"][0]["publicKey"] == "ed25519:abc123"
    assert data["following"][0]["repoURL"] == "https://github.com/alice/social.git"
    assert "added" in data["following"][0]
