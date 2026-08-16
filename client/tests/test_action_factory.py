import pytest
from src.actions.action_factory import ActionRegistry, ActionFactory
from src.actions.post import PostAction
from src.actions.reply import ReplyAction

def test_action_registry_register_and_get():
    ActionRegistry.registry = {}
    ActionRegistry.register("post", PostAction)
    ActionRegistry.register("reply", ReplyAction)

    assert ActionRegistry.get("post") is PostAction
    assert ActionRegistry.get("reply") is ReplyAction
    assert ActionRegistry.get("like") is None

def test_action_factory_create_valid():
    ActionRegistry.registry = {}
    ActionRegistry.register("post", PostAction)

    action = ActionFactory.create("post", "/tmp/social")
    assert isinstance(action, PostAction)
    assert action.social_path == "/tmp/social"

def test_action_factory_create_invalid():
    ActionRegistry.registry = {}
    with pytest.raises(ValueError):
        ActionFactory.create("unknown", "/tmp/social")
