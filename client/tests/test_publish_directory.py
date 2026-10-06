import json
from types import SimpleNamespace

from git import Repo
from git.remote import PushInfo
import pytest

from src.publishing.publish_manager import PublishManager


def _write_directory(repo_path, entries):
    directory_file = repo_path / "directory.json"
    directory_file.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")


def _commit_directory(repo, message):
    repo.git.add("directory.json")
    repo.index.commit(message)


def test_update_directory_merges_remote_registrations(tmp_path):
    bare_path = tmp_path / "directory-origin.git"
    Repo.init(bare_path, bare=True)

    source_path = tmp_path / "source"
    source_repo = Repo.init(source_path)
    source_repo.git.checkout("-b", "main")
    source_repo.config_writer().set_value("user", "name", "Test User").release()
    source_repo.config_writer().set_value(
        "user", "email", "test@example.com"
    ).release()
    _write_directory(source_path, {"existing.social": {"repoURL": "existing-url"}})
    _commit_directory(source_repo, "Initialize directory")
    source_repo.create_remote("origin", str(bare_path))
    source_repo.git.push("--set-upstream", "origin", "main")
    (bare_path / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")

    local_directory_path = tmp_path / "social-directory"
    local_repo = Repo.clone_from(str(bare_path), local_directory_path)

    _write_directory(
        source_path,
        {
            "existing.social": {"repoURL": "existing-url"},
            "remote.social": {"repoURL": "remote-url"},
        },
    )
    _commit_directory(source_repo, "Register remote user")
    source_repo.remotes.origin.push("main")

    _write_directory(
        local_directory_path,
        {
            "existing.social": {"repoURL": "existing-url"},
            "local.social": {"repoURL": "local-url"},
        },
    )
    _commit_directory(local_repo, "Register local user")

    manager = PublishManager(str(tmp_path))
    manager.update_directory("new.social", "new-url", "new-public-key")

    final_directory = json.loads(
        (local_directory_path / "directory.json").read_text(encoding="utf-8")
    )
    verification_repo = Repo.clone_from(str(bare_path), tmp_path / "verification")
    remote_directory = json.loads(
        verification_repo.git.show("main:directory.json")
    )

    expected_entries = {
        "existing.social": {"repoURL": "existing-url"},
        "local.social": {"repoURL": "local-url"},
        "remote.social": {"repoURL": "remote-url"},
        "new.social": {
            "repoURL": "new-url",
            "publicKey": "new-public-key",
        },
    }
    assert final_directory == expected_entries
    assert remote_directory == expected_entries


def test_directory_registration_rejects_public_key_replacement():
    directory = {
        "alice.social": {
            "repoURL": "https://github.com/alice/alice-social.git",
            "publicKey": "ed25519:original-key",
        }
    }

    with pytest.raises(RuntimeError, match="Refusing to replace"):
        PublishManager._assert_registered_key(
            directory, "alice.social", "ed25519:new-key"
        )


def test_directory_registration_requires_key_for_existing_handle():
    directory = {"alice.social": {"repoURL": "https://github.com/alice/alice-social.git"}}

    with pytest.raises(RuntimeError, match="has no registered public key"):
        PublishManager._assert_registered_key(
            directory, "alice.social", "ed25519:new-key"
        )


def test_site_publication_adds_site_url_to_registered_directory_entry(tmp_path):
    bare_path = tmp_path / "directory-origin.git"
    Repo.init(bare_path, bare=True)

    source_path = tmp_path / "source"
    source_repo = Repo.init(source_path)
    source_repo.git.checkout("-b", "main")
    with source_repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")
    _write_directory(
        source_path,
        {
            "alice.social": {
                "repoURL": "https://github.com/alice/alice-social.git",
                "publicKey": "ed25519:alice-key",
            }
        },
    )
    _commit_directory(source_repo, "Initialize directory")
    source_repo.create_remote("origin", str(bare_path))
    source_repo.git.push("--set-upstream", "origin", "main")
    (bare_path / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")

    directory_path = tmp_path / "social-directory"
    Repo.clone_from(str(bare_path), directory_path)
    manager = PublishManager(str(tmp_path))
    manager.update_site_url(
        "alice.social",
        "https://github.com/alice/alice-social.git",
        "ed25519:alice-key",
        "https://alice.github.io/alice-social/",
    )

    local_directory = json.loads(
        (directory_path / "directory.json").read_text(encoding="utf-8")
    )
    remote_directory_repo = Repo.clone_from(
        str(bare_path), tmp_path / "verification"
    )
    remote_directory = json.loads(
        remote_directory_repo.git.show("main:directory.json")
    )
    expected_entry = {
        "repoURL": "https://github.com/alice/alice-social.git",
        "publicKey": "ed25519:alice-key",
        "siteURL": "https://alice.github.io/alice-social/",
    }
    assert local_directory["alice.social"] == expected_entry
    assert remote_directory["alice.social"] == expected_entry


def test_directory_push_rejection_is_reported_as_failure():
    remote = SimpleNamespace(
        push=lambda branch: [
            SimpleNamespace(
                flags=PushInfo.REJECTED,
                summary="non-fast-forward",
            )
        ]
    )
    directory_repo = SimpleNamespace(
        remotes=SimpleNamespace(origin=remote)
    )

    with pytest.raises(RuntimeError, match="Push failed: non-fast-forward"):
        PublishManager._push_directory(directory_repo)
