from src.actions.action_verifier import ActionVerifier
from src.identity.keypair import KeyPair
from src.identity.signer import Signer


def signed_action():
    keypair = KeyPair()
    action = {
        "id": "post-alice.social-001",
        "type": "post",
        "author": keypair.public_key(),
        "content": "Hello world",
        "created": "2026-09-25T00:00:00Z",
    }
    action["signature"] = Signer(keypair.private_key()).sign_json(action)
    return action


def test_action_verifier_accepts_valid_action():
    assert ActionVerifier.verify(signed_action()) is True


def test_action_verifier_rejects_tampered_action():
    action = signed_action()
    action["content"] = "Tampered"

    assert ActionVerifier.verify(action) is False


def test_action_verifier_rejects_action_without_signature():
    action = signed_action()
    del action["signature"]

    assert ActionVerifier.verify(action) is False
