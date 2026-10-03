import os
import json
from pathlib import Path

from src.actions.action_verifier import ActionVerifier
from src.actions.follow import FollowAction
from src.actions.reply import ReplyAction
from src.actions.like import LikeAction
from src.actions.post import PostAction
from src.discovery.profile_verifier import ProfileVerifier
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
        FollowAction,
        "add_remote",
        lambda self, repo, handle, repo_url: None,
    )
    monkeypatch.setattr(
        FollowAction,
        "fetch_profile_git",
        lambda self, repo, handle: {"profile": "unverified"},
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
