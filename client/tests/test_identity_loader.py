import json

import pytest

from src.utils import identity_loader


def test_load_identity_reads_client_identity_file(tmp_path, monkeypatch):
    client_root = tmp_path / "client"
    module_path = client_root / "src" / "utils" / "identity_loader.py"
    module_path.parent.mkdir(parents=True)
    identity = {"activeIdentity": "alice", "repoPath": "alice-social"}
    (client_root / "identity.json").write_text(
        json.dumps(identity), encoding="utf-8"
    )
    monkeypatch.setattr(identity_loader, "__file__", str(module_path))

    assert identity_loader.load_identity() == identity


def test_load_identity_reports_missing_configuration(tmp_path, monkeypatch):
    module_path = tmp_path / "client" / "src" / "utils" / "identity_loader.py"
    module_path.parent.mkdir(parents=True)
    monkeypatch.setattr(identity_loader, "__file__", str(module_path))

    with pytest.raises(FileNotFoundError):
        identity_loader.load_identity()
