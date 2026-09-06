import os
import json
from git import Repo
from src.identity.signer import Signer
from src.utils.identity_loader import load_identity

CANONICAL_URL = "https://github.com/gargster/canonical-social.git"

class PublishManager:
    def __init__(self, project_root):
        self.project_root = project_root

    def publish(self, remote_url):
        """
        Publish the current user's repo to their GitHub remote.
        This is used for BOTH canonical and normal users.
        """
        identity = load_identity()
        identity_name = identity["activeIdentity"]
        repo_name = identity["repoPath"]  # e.g. bharat-social
        repo_root = os.path.join(self.project_root, repo_name)

        social_path = os.path.join(repo_root, "social")
        profile_path = os.path.join(social_path, "profile.json")

        print(f"[PUBLISH] Publishing {identity_name}.social → {remote_url}")

        repo = Repo(repo_root)

        # ------------------------------------------------------------
        # 1. Set origin to user's GitHub repo
        # ------------------------------------------------------------
        if "origin" in repo.remotes:
            repo.remotes.origin.set_url(remote_url)
        else:
            repo.create_remote("origin", remote_url)

        # ------------------------------------------------------------
        # 2. Push main branch to GitHub
        # ------------------------------------------------------------
        print("[PUBLISH] Pushing repo to GitHub...")
        repo.git.push("--set-upstream", "origin", "main")

        # ------------------------------------------------------------
        # 3. Update profile.json with new repoURL
        # ------------------------------------------------------------
        with open(profile_path, "r") as f:
            profile = json.load(f)

        profile["repoURL"] = remote_url

        # ------------------------------------------------------------
        # 4. Re-sign profile.json with user's private key
        # ------------------------------------------------------------
        private_key_path = os.path.join(
            self.project_root,
            "client",
            "state",
            identity_name,
            "keystore",
            "private.key"
        )

        with open(private_key_path, "r") as f:
            private_key = f.read()

        signer = Signer(private_key)
        profile["signature"] = signer.sign_json(profile)

        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)

        # Commit + push updated profile.json
        repo.git.add(profile_path)
        try:
            repo.git.commit("-m", "Update repoURL + signature")
        except:
            pass
        repo.git.push()

        # ------------------------------------------------------------
        # 5. Add canonical as a second remote (critical!)
        # ------------------------------------------------------------
        if "canonical" not in [r.name for r in repo.remotes]:
            print("[PUBLISH] Adding canonical remote...")
            repo.create_remote("canonical", CANONICAL_URL)

        print("[PUBLISH] Complete.")
