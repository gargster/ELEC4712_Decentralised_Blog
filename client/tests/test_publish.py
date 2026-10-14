import json

from git import Repo

from src.identity.keypair import KeyPair
from src.identity.profile_verifier import ProfileVerifier
from src.identity.signer import Signer
from src.publishing import publish_manager
from src.publishing.publish_manager import PublishManager


def _configure(repo):
    with repo.config_writer() as config:
        config.set_value("user", "name", "Publish Test")
        config.set_value("user", "email", "publish-test@example.com")


def test_publish_updates_signed_profile_and_pushes_to_configured_origin(
    tmp_path, monkeypatch
):
    project_root = tmp_path / "project"
    repo_path = project_root / "alice-social"
    repo_path.mkdir(parents=True)
    repo = Repo.init(repo_path)
    repo.git.checkout("-b", "main")
    _configure(repo)

    keypair = KeyPair()
    profile = {
        "handle": "alice.social",
        "publicKey": keypair.public_key(),
        "repoURL": None,
        "displayName": "Alice",
        "bio": "Test profile",
        "created": "2026-10-01T00:00:00Z",
    }
    profile["signature"] = Signer(keypair.private_key()).sign_json(profile)
    profile_path = repo_path / "social" / "profile.json"
    profile_path.parent.mkdir(parents=True)
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    repo.git.add(A=True)
    repo.index.commit("Create signed profile")

    origin_path = tmp_path / "alice-origin.git"
    Repo.init(origin_path, bare=True)
    repo.create_remote("origin", str(origin_path))
    repo.git.push("--set-upstream", "origin", "main")

    key_path = project_root / "client" / "state" / "alice" / "keystore" / "private.key"
    key_path.parent.mkdir(parents=True)
    key_path.write_text(keypair.private_key(), encoding="utf-8")
    site_directory_updates = []
    monkeypatch.setattr(
        publish_manager,
        "load_identity",
        lambda: {"activeIdentity": "alice", "repoPath": "alice-social"},
    )
    monkeypatch.setattr(PublishManager, "_ensure_registered_key", lambda *args: None)
    monkeypatch.setattr(
        PublishManager,
        "update_directory",
        lambda self, handle, url, public_key: site_directory_updates.append(
            (handle, url, public_key)
        ),
    )

    PublishManager(str(project_root)).publish(str(origin_path))

    updated_profile = json.loads(profile_path.read_text(encoding="utf-8"))
    assert updated_profile["repoURL"] == str(origin_path)
    assert ProfileVerifier(updated_profile).verify()["publicKey"] == keypair.public_key()
    assert site_directory_updates == [
        ("alice.social", str(origin_path), keypair.public_key())
    ]
    assert repo.remotes.canonical.url.endswith("canonical-social.git")

    remote_profile = json.loads(Repo(origin_path).git.show("main:social/profile.json"))
    assert remote_profile == updated_profile
