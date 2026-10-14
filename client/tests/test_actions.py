import io
import os
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from git import Repo

from src.actions.action_verifier import ActionVerifier
from src.actions.follow import FollowAction
from src.actions.reply import ReplyAction
from src.actions.like import LikeAction
from src.actions.post import PostAction
from src.identity.profile_verifier import ProfileVerifier
from src.identity.profile import ProfileCreator
import src.actions.base as base


def setup_identity(project_root):
    # Create client/
    client_root = os.path.join(project_root, "client")
    os.makedirs(client_root, exist_ok=True)

    # Create identity.json
    identity_json_path = os.path.join(client_root, "identity.json")
    with open(identity_json_path, "w") as f:
        json.dump({"activeIdentity": "bharat"}, f)

    # Create full repo
    creator = ProfileCreator(project_root)
    creator.create_profile("bharat.social", "Bharat", "Student at USYD")

    # Real social path
    return os.path.join(project_root, "bharat-social", "social")


def patch_load_identity(project_root, monkeypatch):
    """
    Monkey‑patch ActionBase._load_identity so it loads keys
    from the TEST project_root instead of the REAL project.
    """

    def _load_identity(self):
        # Load public key from test profile.json
        profile_path = os.path.join(self.social_path, "profile.json")
        with open(profile_path, "r") as f:
            profile = json.load(f)

        public_key = profile["publicKey"]

        # Load private key from test client/state/<identity>/keystore/private.key
        identity_json_path = os.path.join(project_root, "client", "identity.json")
        with open(identity_json_path, "r") as f:
            identity_data = json.load(f)

        active_identity = identity_data["activeIdentity"]

        private_key_path = os.path.join(
            project_root,
            "client",
            "state",
            active_identity,
            "keystore",
            "private.key"
        )

        with open(private_key_path, "r") as f:
            private_key = f.read().strip()

        return public_key, private_key, profile["handle"]

    monkeypatch.setattr(base.ActionBase, "_load_identity", _load_identity)


def test_post_action(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    os.makedirs(project_root)

    # Patch ActionBase to use TEST identity paths
    patch_load_identity(str(project_root), monkeypatch)

    # Build full identity + repo structure
    social_path = setup_identity(str(project_root))

    # Run the action
    action = PostAction(social_path)
    path, obj = action.create_post("Hello world")

    # Assertions
    assert os.path.exists(path)
    assert obj["type"] == "post"
    assert obj["id"] == "post-bharat.social-001"
    assert obj["author"].startswith("ed25519:")
    assert obj["content"] == "Hello world"
    assert json.loads(Path(path).read_text(encoding="utf-8")) == obj
    assert ActionVerifier.verify(obj)


# -----------------------------
#        ReplyAction Test
# -----------------------------
def test_reply_action(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    os.makedirs(project_root)

    patch_load_identity(str(project_root), monkeypatch)
    social_path = setup_identity(str(project_root))

    action = ReplyAction(social_path)
    path, obj = action.create_reply("Nice!", "post-alice.social-001", "alice.social")

    assert os.path.exists(path)
    assert obj["type"] == "reply"
    assert obj["content"] == "Nice!"
    assert obj["inReplyTo"] == "post-alice.social-001"
    assert obj["targetHandle"] == "alice.social"
    assert obj["author"].startswith("ed25519:")
    assert ActionVerifier.verify(obj)

# -----------------------------
#        LikeAction Test
# -----------------------------
def test_like_action(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    os.makedirs(project_root)

    patch_load_identity(str(project_root), monkeypatch)
    social_path = setup_identity(str(project_root))

    action = LikeAction(social_path)
    path, obj = action.create_like("post-alice.social-001", "alice.social")

    assert os.path.exists(path)
    assert obj["type"] == "like"
    assert obj["target"] == "post-alice.social-001"
    assert obj["targetHandle"] == "alice.social"
    assert obj["author"].startswith("ed25519:")
    assert ActionVerifier.verify(obj)

# -----------------------------
#        FollowAction Test
# -----------------------------
def test_follow_action(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    os.makedirs(project_root)

    patch_load_identity(str(project_root), monkeypatch)
    social_path = setup_identity(str(project_root))

    action = FollowAction(social_path)
    path, obj = action.create_follow("ed25519:abc123")

    assert os.path.exists(path)
    assert obj["type"] == "follow"
    assert obj["target"] == "ed25519:abc123"
    assert obj["author"].startswith("ed25519:")
    assert ActionVerifier.verify(obj)


def test_follow_action_run_uses_verified_profile_and_git_remote(
    tmp_path, monkeypatch
):
    from src.actions import follow as follow_module

    social_path = tmp_path / "user" / "social"
    social_path.mkdir(parents=True)
    origin = type("Origin", (), {"push": lambda self: None})()
    repo = type(
        "Repo",
        (),
        {
            "remotes": type("Remotes", (), {"origin": origin})(),
            "git": type("Git", (), {"add": lambda self, *args, **kwargs: None})(),
            "index": type(
                "Index",
                (),
                {"commit": lambda self, message: None},
            )(),
        },
    )()
    monkeypatch.setattr(follow_module.git, "Repo", lambda path: repo)
    monkeypatch.setattr(
        follow_module.urllib.request,
        "urlopen",
        lambda url, timeout: io.BytesIO(
            json.dumps(
                {
                    "alice.social": {
                        "repoURL": "https://github.com/alice/alice-social.git",
                        "publicKey": "ed25519:abc123",
                    }
                }
            ).encode("utf-8")
        ),
    )
    monkeypatch.setattr(
        FollowAction,
        "add_remote",
        lambda self, repo, handle, repo_url: None,
    )
    monkeypatch.setattr(
        FollowAction,
        "fetch_profile_git",
        lambda self, repo, handle: {
            "handle": "alice.social",
            "repoURL": "https://github.com/alice/alice-social.git",
        },
    )
    monkeypatch.setattr(
        follow_module.ProfileVerifier,
        "verify",
        lambda self: {
            "handle": "alice.social",
            "publicKey": "ed25519:abc123",
            "repoURL": "https://github.com/alice/alice-social.git",
        },
    )
    monkeypatch.setattr(
        FollowAction,
        "create_follow",
        lambda self, public_key: (
            str(tmp_path / "follow.json"),
            {"type": "follow", "target": public_key, "id": "follow-001"},
        ),
    )

    class Args:
        target_handle = "alice.social"
        target_repo_url = "https://github.com/alice/alice-social.git"

    path, action = FollowAction(str(social_path)).run(Args())

    assert path == str(tmp_path / "follow.json")
    assert action == {
        "type": "follow",
        "target": "ed25519:abc123",
        "id": "follow-001",
    }


def test_follow_action_rejects_profile_with_unregistered_key(
    tmp_path, monkeypatch
):
    from src.actions import follow as follow_module

    social_path = tmp_path / "user" / "social"
    social_path.mkdir(parents=True)
    repo = type(
        "Repo",
        (),
        {
            "remotes": type("Remotes", (), {"origin": object()})(),
            "git": type("Git", (), {"add": lambda self, *args, **kwargs: None})(),
            "index": type("Index", (), {"commit": lambda self, message: None})(),
        },
    )()
    monkeypatch.setattr(follow_module.git, "Repo", lambda path: repo)
    monkeypatch.setattr(
        follow_module.urllib.request,
        "urlopen",
        lambda url, timeout: io.BytesIO(
            json.dumps(
                {
                    "alice.social": {
                        "repoURL": "https://github.com/alice/alice-social.git",
                        "publicKey": "ed25519:registered-key",
                    }
                }
            ).encode("utf-8")
        ),
    )
    monkeypatch.setattr(FollowAction, "add_remote", lambda *args: None)
    monkeypatch.setattr(
        FollowAction,
        "fetch_profile_git",
        lambda *args: {
            "handle": "alice.social",
            "repoURL": "https://github.com/alice/alice-social.git",
        },
    )
    monkeypatch.setattr(
        follow_module.ProfileVerifier,
        "verify",
        lambda self: {
            "handle": "alice.social",
            "publicKey": "ed25519:new-key",
            "repoURL": "https://github.com/alice/alice-social.git",
        },
    )
    monkeypatch.setattr(
        FollowAction,
        "create_follow",
        lambda *args: pytest.fail("Must reject an unregistered key"),
    )

    class Args:
        target_handle = "alice.social"
        target_repo_url = "https://github.com/alice/alice-social.git"

    with pytest.raises(ValueError, match="does not match the social directory"):
        FollowAction(str(social_path)).run(Args())


def test_follow_action_rejects_handle_missing_from_directory(
    tmp_path, monkeypatch
):
    from src.actions import follow as follow_module

    social_path = tmp_path / "user" / "social"
    social_path.mkdir(parents=True)
    monkeypatch.setattr(
        follow_module.urllib.request,
        "urlopen",
        lambda url, timeout: io.BytesIO(b"{}"),
    )
    monkeypatch.setattr(
        follow_module.git,
        "Repo",
        lambda path: pytest.fail("Must reject before accessing the user repo"),
    )

    class Args:
        target_handle = "alice.social"
        target_repo_url = "https://github.com/alice/alice-social.git"

    with pytest.raises(ValueError, match="not registered in the social directory"):
        FollowAction(str(social_path)).run(Args())


def test_action_run_methods_forward_cli_arguments(tmp_path, monkeypatch):
    social_path = str(tmp_path / "social")
    args = SimpleNamespace(
        content="message",
        target_action="post-bob.social-001",
        target_handle="bob.social",
    )
    cases = [
        (PostAction, "create_post", "message"),
        (ReplyAction, "create_reply", ("message", "post-bob.social-001", "bob.social")),
        (LikeAction, "create_like", ("post-bob.social-001", "bob.social")),
    ]

    for action_class, method_name, expected in cases:
        action = action_class(social_path)
        calls = []
        monkeypatch.setattr(
            action,
            method_name,
            lambda *values: calls.append(values) or ("action.json", {}),
        )

        assert action.run(args) == ("action.json", {})
        assert calls == [expected if isinstance(expected, tuple) else (expected,)]


def test_follow_adds_remote_once_and_fetches_profile_from_main(tmp_path):
    remote_path = tmp_path / "bob-social"
    remote_repo = Repo.init(remote_path)
    remote_repo.git.checkout("-b", "main")
    with remote_repo.config_writer() as config:
        config.set_value("user", "name", "Follow Test")
        config.set_value("user", "email", "follow-test@example.com")
    profile = {"handle": "bob.social", "publicKey": "bob-key"}
    profile_path = remote_path / "social" / "profile.json"
    profile_path.parent.mkdir(parents=True)
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    remote_repo.git.add(A=True)
    remote_repo.index.commit("Add profile")

    local_path = tmp_path / "alice-social"
    local_repo = Repo.init(local_path)
    action = FollowAction(str(local_path / "social"))
    action.add_remote(local_repo, "bob.social", str(remote_path))
    action.add_remote(local_repo, "bob.social", str(remote_path))

    fetched_profile = action.fetch_profile_git(local_repo, "bob.social")

    assert fetched_profile == profile
    assert [remote.name for remote in local_repo.remotes] == ["bob.social"]


def test_action_base_generates_incrementing_signed_ids(tmp_path, monkeypatch):
    keypair = base.KeyPair()
    action_base = base.ActionBase(str(tmp_path / "social"))
    monkeypatch.setattr(
        action_base,
        "_load_identity",
        lambda: (keypair.public_key(), keypair.private_key(), "alice.social"),
    )

    first_path, first = action_base._create("post")
    second_path, second = action_base._create("post")

    assert first["id"] == "post-alice.social-001"
    assert second["id"] == "post-alice.social-002"
    assert first["created"].endswith("Z")
    assert Path(first_path).is_file()
    assert Path(second_path).is_file()
    assert ActionVerifier.verify(first)
    assert ActionVerifier.verify(second)


def test_action_base_refuses_private_key_that_does_not_match_profile(
    tmp_path, monkeypatch
):
    profile_key = base.KeyPair()
    active_key = base.KeyPair()
    action_base = base.ActionBase(str(tmp_path / "social"))
    monkeypatch.setattr(
        action_base,
        "_load_identity",
        lambda: (
            profile_key.public_key(),
            active_key.private_key(),
            "alice.social",
        ),
    )

    with pytest.raises(ValueError, match="does not match private.key"):
        action_base._create("post")

    assert not list(Path(action_base.actions_path).iterdir())


def test_action_base_loads_active_identity_key_from_client_state(
    tmp_path, monkeypatch
):
    project_root = tmp_path / "project"
    fake_module_path = project_root / "client" / "src" / "actions" / "base.py"
    fake_module_path.parent.mkdir(parents=True)
    monkeypatch.setattr(base, "__file__", str(fake_module_path))

    keypair = base.KeyPair()
    social_path = project_root / "alice-social" / "social"
    social_path.mkdir(parents=True)
    (social_path / "profile.json").write_text(
        json.dumps(
            {"handle": "alice.social", "publicKey": keypair.public_key()}
        ),
        encoding="utf-8",
    )
    client_path = project_root / "client"
    (client_path / "identity.json").write_text(
        json.dumps({"activeIdentity": "alice"}), encoding="utf-8"
    )
    key_path = client_path / "state" / "alice" / "keystore" / "private.key"
    key_path.parent.mkdir(parents=True)
    key_path.write_text(keypair.private_key(), encoding="utf-8")

    loaded = base.ActionBase(str(social_path))._load_identity()

    assert loaded == (
        keypair.public_key(),
        keypair.private_key(),
        "alice.social",
    )


def test_action_base_skips_invalid_ids_and_writes_to_an_explicit_directory(
    tmp_path, monkeypatch
):
    keypair = base.KeyPair()
    action = base.ActionBase(str(tmp_path / "social"))
    (Path(action.actions_path) / "post-alice.social-not-a-number.json").write_text(
        "{}", encoding="utf-8"
    )
    (Path(action.actions_path) / "unrelated.json").write_text(
        "{}", encoding="utf-8"
    )
    monkeypatch.setattr(
        action,
        "_load_identity",
        lambda: (keypair.public_key(), keypair.private_key(), "alice.social"),
    )
    other_actions = tmp_path / "custom-actions"
    other_actions.mkdir()

    path, record = action._create("reply", actions_path=str(other_actions))

    assert record["id"] == "reply-alice.social-001"
    assert Path(path).parent == other_actions
    assert ActionVerifier.verify(record)


def test_action_base_write_strips_json_suffix_from_action_id(tmp_path):
    action = base.ActionBase(str(tmp_path / "social"))

    path = action._write({"id": "post-001.json"})

    assert Path(path).name == "post-001.json"
    assert json.loads(Path(path).read_text(encoding="utf-8")) == {
        "id": "post-001.json"
    }


def test_follow_rejects_non_object_directory_and_missing_registered_key(
    tmp_path, monkeypatch
):
    from src.actions import follow as follow_module

    action = FollowAction(str(tmp_path / "social"))
    monkeypatch.setattr(
        follow_module.urllib.request,
        "urlopen",
        lambda url, timeout: io.BytesIO(b"[]"),
    )
    with pytest.raises(ValueError, match="must be a JSON object"):
        action._registered_identity("alice.social")

    monkeypatch.setattr(
        follow_module.urllib.request,
        "urlopen",
        lambda url, timeout: io.BytesIO(b'{"alice.social": {}}'),
    )
    with pytest.raises(ValueError, match="no registered public key"):
        action._registered_identity("alice.social")


def test_follow_reports_missing_profile_in_fetched_remote(tmp_path, monkeypatch):
    from src.actions import follow as follow_module

    monkeypatch.setattr(
        follow_module.git.cmd,
        "Git",
        lambda path: SimpleNamespace(
            show=lambda ref: (_ for _ in ()).throw(RuntimeError("not found"))
        ),
    )
    remote = SimpleNamespace(fetch=lambda branch: None)
    repo = SimpleNamespace(
        working_tree_dir=str(tmp_path),
        remotes={"alice.social": remote},
    )
    with pytest.raises(Exception, match="profile.json missing"):
        FollowAction(str(tmp_path / "social")).fetch_profile_git(
            repo, "alice.social"
        )
