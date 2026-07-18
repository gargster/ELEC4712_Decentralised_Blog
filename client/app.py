# Purpose
# Step-by-step testing of core components(Identuty, Signing, Profile Creation)
# Before adding CLI commands, or Git integration
import os
import json

# Import identity modules
from src.identity.keypair import KeyPair
from src.identity.signer import Signer
from src.identity.profile import ProfileCreator

# Path to test social repo
SOCIAL_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "social"
)
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

def main():
    public_key, private_key = test_keypair_generation()
    test_signing(public_key, private_key)
    test_profile_creation()


if __name__ == "__main__":
    main()
