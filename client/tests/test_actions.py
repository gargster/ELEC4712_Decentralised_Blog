import os
import json
from src.actions.post import PostAction
from src.actions.reply import ReplyAction
from src.actions.like import LikeAction
from src.actions.follow import FollowAction
from src.identity.profile import ProfileCreator

def setup_identity(social_path):
    creator = ProfileCreator(social_path)
    creator.create_profile("bharat.social", "Bharat", "Student at USYD")

def test_post_action(tmp_path):
    social_path = tmp_path / "social"
    os.makedirs(social_path / "actions")

    setup_identity(str(social_path))

    action = PostAction(str(social_path))
    path, obj = action.create_post("Hello world")

    assert os.path.exists(path)
    assert obj["type"] == "post"
    assert obj["content"] == "Hello world"
    assert obj["author"].startswith("ed25519:")
    assert "signature" in obj

def test_reply_action(tmp_path):
    social_path = tmp_path / "social"
    os.makedirs(social_path / "actions")

    setup_identity(str(social_path))

    action = ReplyAction(str(social_path))
    path, obj = action.create_reply("post-001", "Nice!")

    assert obj["type"] == "reply"
    assert obj["inReplyTo"] == "post-001"

def test_like_action(tmp_path):
    social_path = tmp_path / "social"
    os.makedirs(social_path / "actions")

    setup_identity(str(social_path))

    action = LikeAction(str(social_path))
    path, obj = action.create_like("post-001")

    assert obj["type"] == "like"
    assert obj["target"] == "post-001"

def test_follow_action(tmp_path):
    social_path = tmp_path / "social"
    os.makedirs(social_path / "actions")

    setup_identity(str(social_path))

    action = FollowAction(str(social_path))
    path, obj = action.create_follow("ed25519:abc123")

    assert obj["type"] == "follow"
    assert obj["target"] == "ed25519:abc123"
