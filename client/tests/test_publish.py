# import os
# import json
# from git import Repo
# from src.publishing.publish_manager import PublishManager
# from src.utils import identity_loader


# def test_publish_updates_profile_and_directory(tmp_path, monkeypatch):
#     # -----------------------------
#     # 1. Create fake project root
#     # -----------------------------
#     project_root = tmp_path / "project"
#     os.makedirs(project_root)

#     # -----------------------------
#     # 2. Create client/ + identity.json
#     # -----------------------------
#     client_root = project_root / "client"
#     os.makedirs(client_root, exist_ok=True)

#     identity_json_path = client_root / "identity.json"
#     with open(identity_json_path, "w") as f:
#         json.dump({
#             "activeIdentity": "bharat",
#             "repoPath": "bharat-social"
#         }, f)

#     # Patch load_identity() so PublishManager uses our temp identity.json
#     def fake_load_identity():
#         with open(identity_json_path) as f:
#             return json.load(f)

#     monkeypatch.setattr(identity_loader, "load_identity", fake_load_identity)

#     # -----------------------------
#     # 3. Create fake repo structure
#     # -----------------------------
#     repo_root = project_root / "bharat-social"
#     social_root = repo_root / "social"
#     os.makedirs(social_root, exist_ok=True)

#     profile_path = social_root / "profile.json"
#     with open(profile_path, "w") as f:
#         json.dump({
#             "handle": "bharat.social",
#             "displayName": "Bharat",
#             "bio": "Student at USYD",
#             "publicKey": "ed25519:FAKEKEY",
#             "signature": "initialsig"
#         }, f)

#     # -----------------------------
#     # 4. Create keystore + private key
#     # -----------------------------
#     keystore_path = client_root / "state" / "bharat" / "keystore"
#     os.makedirs(keystore_path, exist_ok=True)

#     private_key_path = keystore_path / "private.key"
#     with open(private_key_path, "w") as f:
#         f.write("FAKE_PRIVATE_KEY")

#     # -----------------------------
#     # 5. Create directory.json
#     # -----------------------------
#     directory_path = client_root / "directory.json"
#     with open(directory_path, "w") as f:
#         json.dump({}, f)

#     # -----------------------------
#     # 6. Init local Git repo
#     # -----------------------------
#     repo = Repo.init(repo_root)
#     repo.index.add([str(profile_path)])
#     repo.index.commit("Initial commit")

#     # -----------------------------
#     # 7. Run publish()
#     # -----------------------------
#     pm = PublishManager(str(project_root))
#     pm.publish("https://example.com/bharat-social.git")

#     # -----------------------------
#     # 8. Verify profile.json updated
#     # -----------------------------
#     with open(profile_path) as f:
#         updated_profile = json.load(f)

#     assert updated_profile["repoURL"] == "https://example.com/bharat-social.git"
#     assert updated_profile["signature"] != "initialsig"

#     # -----------------------------
#     # 9. Verify directory.json updated
#     # -----------------------------
#     with open(directory_path) as f:
#         directory_data = json.load(f)

#     assert "bharat.social" in directory_data
#     assert directory_data["bharat.social"]["localPath"] == "bharat-social"
#     assert directory_data["bharat.social"]["repoURL"] == "https://example.com/bharat-social.git"
