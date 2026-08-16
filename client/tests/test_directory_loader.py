import json
import os
import pytest
from src.discovery.directory_loader import DirectoryLoader

def test_directory_loader_resolve_existing_handle(tmp_path):
    client_root = tmp_path
    directory_path = client_root / "directory.json"

    data = {
        "alice.social": {
            "localPath": "alice-social",
            "repoURL": "https://github.com/alice/alice-social.git"
        }
    }
    directory_path.write_text(json.dumps(data))

    loader = DirectoryLoader(str(client_root))
    info = loader.resolve("alice.social")

    assert info["localPath"] == "alice-social"
    assert info["repoURL"] == "https://github.com/alice/alice-social.git"

def test_directory_loader_resolve_missing_handle(tmp_path):
    client_root = tmp_path
    directory_path = client_root / "directory.json"
    directory_path.write_text(json.dumps({}))

    loader = DirectoryLoader(str(client_root))

    with pytest.raises(ValueError):
        loader.resolve("unknown.social")
