import os
import json

from src.actions.follow import FollowAction
from src.actions.reply import ReplyAction
from src.actions.like import LikeAction
from src.actions.post import PostAction
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


def patch_load_identity(project_root):
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

        return public_key, private_key

    base.ActionBase._load_identity = _load_identity


def test_post_action(tmp_path):
    project_root = tmp_path / "project"
    os.makedirs(project_root)

    # Patch ActionBase to use TEST identity paths
    patch_load_identity(str(project_root))

    # Build full identity + repo structure
    social_path = setup_identity(str(project_root))

    # Run the action
    action = PostAction(social_path)
    path, obj = action.create_post("Hello world")

    # Assertions
    assert os.path.exists(path)
    assert obj["type"] == "post"
    assert obj["content"] == "Hello world"
    assert obj["author"].startswith("ed25519:")
    assert "signature" in obj


# -----------------------------
#        ReplyAction Test
# -----------------------------
def test_reply_action(tmp_path):
    project_root = tmp_path / "project"
    os.makedirs(project_root)

    patch_load_identity(str(project_root))
    social_path = setup_identity(str(project_root))

    action = ReplyAction(social_path)
    path, obj = action.create_reply("post-001", "Nice!")

    assert os.path.exists(path)
    assert obj["type"] == "reply"
    assert obj["inReplyTo"] == "post-001"
    assert obj["content"] == "Nice!"
    assert obj["author"].startswith("ed25519:")
    assert "signature" in obj

# -----------------------------
#        LikeAction Test
# -----------------------------
def test_like_action(tmp_path):
    project_root = tmp_path / "project"
    os.makedirs(project_root)

    patch_load_identity(str(project_root))
    social_path = setup_identity(str(project_root))

    action = LikeAction(social_path)
    path, obj = action.create_like("post-001")

    assert os.path.exists(path)
    assert obj["type"] == "like"
    assert obj["target"] == "post-001"
    assert obj["author"].startswith("ed25519:")
    assert "signature" in obj

# -----------------------------
#        FollowAction Test
# -----------------------------
def test_follow_action(tmp_path):
    project_root = tmp_path / "project"
    os.makedirs(project_root)

    patch_load_identity(str(project_root))
    social_path = setup_identity(str(project_root))

    action = FollowAction(social_path)
    path, obj = action.create_follow("ed25519:abc123")

    assert os.path.exists(path)
    assert obj["type"] == "follow"
    assert obj["target"] == "ed25519:abc123"
    assert obj["author"].startswith("ed25519:")
    assert "signature" in obj


# ---------------------------------------------------------
# FollowAction.run() test
# ---------------------------------------------------------

def test_follow_action_run(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    os.makedirs(project_root)

    # Use working identity setup
    patch_load_identity(str(project_root))
    social_path = setup_identity(str(project_root))

    # Mock DirectoryLoader.resolve
    def fake_resolve(self, handle):
        return {
            "localPath": "alice-social",
            "repoURL": "https://github.com/alice/social.git"
        }
    monkeypatch.setattr("src.actions.follow.DirectoryLoader.resolve", fake_resolve)

    # Mock GitPython
    class FakeRepo:
        def __init__(self, path):
            self.path = path
            self.remotes = type("R", (), {"origin": self})
        def pull(self): pass
        def reset(self, *args): pass

    monkeypatch.setattr("git.repo.base.Repo.clone_from", lambda url, path: None)
    monkeypatch.setattr("git.repo.base.Repo", FakeRepo)

    # Mock ProfileVerifier.verify
    def fake_verify(self):
        return {
            "handle": "alice.social",
            "publicKey": "ed25519:abc123",
            "repoURL": "https://github.com/alice/social.git"
        }
    monkeypatch.setattr("src.actions.follow.ProfileVerifier.verify", fake_verify)

    # Mock FollowManager.add_follow
    def fake_add_follow(self, handle, public_key, repo_url):
        return {"handle": handle, "publicKey": public_key, "repoURL": repo_url}
    monkeypatch.setattr("src.actions.follow.FollowManager.add_follow", fake_add_follow)

    # Args
    class Args:
        target_handle = "alice.social"

    action = FollowAction(str(social_path))
    path, obj = action.run(Args())

    assert obj["type"] == "follow"
    assert obj["target"] == "ed25519:abc123"
    assert "id" in obj
