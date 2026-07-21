# Purpose
# Step-by-step testing of core components(Identuty, Signing, Profile Creation)
# Before adding CLI commands, or Git integration
import os
import json

# Import identity modules
from src.identity.keypair import KeyPair
from src.identity.signer import Signer
from src.identity.profile import ProfileCreator
# Import social action modules
from src.actions.post import PostAction
from src.actions.reply import ReplyAction
from src.actions.like import LikeAction
from src.actions.follow import FollowAction


# Path to test social repo
SOCIAL_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "social"
)
# Identity test functions
def test_keypair_generation():
    print("\n=== Test: KeyPair Generation ===")
    keypair = KeyPair()
    public_key = keypair.public_key()
    private_key = keypair.private_key()
    print("Public Key:", public_key)
    print("Private Key:", private_key)
    return public_key, private_key
def test_signing(public_key, private_key):
    print("\n=== Test: Signing JSON ===")
    # Sample JSON data to sign
    sample_obj = {
        "author": public_key,
        "message": "Testing signature"
    }
    signer = Signer(private_key)
    signature = signer.sign_json(sample_obj)
    sample_obj["signature"] = signature
    print("Signed JSON:")
    print(json.dumps(sample_obj, indent=2))
    return signature
def test_profile_creation():
    print("\n=== Test: Profile Creation ===")
    profile_creator = ProfileCreator(SOCIAL_PATH)

    handle = "bharat.social"
    display_name = "Bharat"
    bio = "Student at USYD."

    profile_path = profile_creator.create_profile(handle, display_name, bio)
    print("Profile created at:", profile_path)
    with open(profile_path, "r") as file:
        profile_data = json.load(file)
    print("Profile.json contents: ")
    print(json.dumps(profile_data, indent=2))
# Social action test functions
def test_post_action():
    print("\n=== Test: Post Action ===")
    post_action = PostAction(SOCIAL_PATH)
    path, post_obj = post_action.create_post("Hello world from Bharat!")
    print("Post created at:", path)
    print("Post JSON contents:")
    print(json.dumps(post_obj, indent=2))

def test_reply_action():
    print("\n=== Test: Reply Action ===")
    reply_action = ReplyAction(SOCIAL_PATH)
    # Reply to an existing post (e.g. post-001)
    path, reply_obj = reply_action.create_reply(
        parent_id="post-001",
        content="Replying to your post!"
    )
    print("Reply created at:", path)
    print("Reply JSON contents:")
    print(json.dumps(reply_obj, indent=2))

def test_like_action():
    print("\n=== Test: Like Action ===")
    like_action = LikeAction(SOCIAL_PATH)
    # Like an existing post (e.g. post-001)
    path, like_obj = like_action.create_like("post-001")

    print("Like created at:", path)
    print("Like JSON contents:")
    print(json.dumps(like_obj, indent=2))

def test_follow_action():
    print("\n=== Test: Follow Action ===")
    follow_action = FollowAction(SOCIAL_PATH)

    # Follow another user (their public key)
    target_pk = "ed25519:def456..."  # placeholder for testing

    path, follow_obj = follow_action.create_follow(target_pk)

    print("Follow created at:", path)
    print("Follow JSON contents:")
    print(json.dumps(follow_obj, indent=2))

def main():
    # Identity
    public_key, private_key = test_keypair_generation()
    test_signing(public_key, private_key)
    test_profile_creation()
    # Social Action
    test_post_action()
    test_reply_action()
    test_like_action()
    test_follow_action()

if __name__ == "__main__":
    main()
