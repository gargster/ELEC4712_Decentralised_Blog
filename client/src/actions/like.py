import os
import json
import git
from datetime import datetime, timezone

from src.identity.signer import Signer
from src.utils.identity_loader import load_identity
class LikeAction:
    # Writes likes directly into the TARGET USER'S REAL REPO.
    # Reads repoURL from the nested clone's .git/config (Rahul model).
    def __init__(self, social_root):
        # social_root = <project_root>/<active-identity-repo>/social
        # Used ONLY to locate the nested following_repos folder.
        self.social_root = social_root

    # ---------------------------------------------------------
    # MAIN ENTRY POINT
    # ---------------------------------------------------------
    def run(self, args):
        target_handle = args.target_handle        # e.g. carl.social
        target_action = args.target_action        # e.g. post-003

        public_key, private_key = self._load_identity()

        # 1. Locate nested clone of target user
        nested_clone_path = self.get_nested_clone_path(target_handle)

        # REQUIRED SAFETY CHECK
        if not os.path.exists(nested_clone_path):
            raise Exception(f"You must follow {target_handle} before liking their posts.")

        # 2. Read real repo URL from nested clone's .git/config
        repo_url = self.get_repo_url_from_git_config(nested_clone_path)

        # 3. Clone/pull the target user's real repo into project root
        real_repo_path = self.ensure_real_repo_clone(target_handle, repo_url)

        # 4. Build like JSON
        like_id = self.generate_like_id(real_repo_path)
        like_obj = {
            "id": like_id,
            "type": "like",
            "author": public_key,
            "target": target_action,
            "created": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }

        # 5. Sign the like JSON
        signer = Signer(private_key)
        like_obj["signature"] = signer.sign_json(like_obj)

        # 6. Write like JSON into target repo
        actions_dir = os.path.join(real_repo_path, "social", "actions")
        os.makedirs(actions_dir, exist_ok=True)

        like_path = os.path.join(actions_dir, f"{like_id}.json")
        with open(like_path, "w") as f:
            json.dump(like_obj, f, indent=2)

        # 7. Commit + push target repo
        repo = git.Repo(real_repo_path)
        repo.git.add(like_path)
        repo.index.commit(f"Add {like_id}")
        repo.remotes.origin.push()

        print(f"[LIKE] Added {like_id} to {target_handle}'s real repo.")
        return like_path, like_obj

    # ---------------------------------------------------------
    # HELPER METHODS
    # ---------------------------------------------------------

    def get_nested_clone_path(self, handle):
        """
        Locate the nested clone inside:
        <active-identity-repo>/social/following_repos/<handle>-social/
        """
        repo_name = handle.replace(".social", "") + "-social"
        return os.path.join(self.social_root, "following_repos", repo_name)

    def get_repo_url_from_git_config(self, nested_clone_path):
        """
        Read the real repo URL from nested clone's .git/config.
        """
        repo = git.Repo(nested_clone_path)
        return repo.remotes.origin.url

    def ensure_real_repo_clone(self, handle, repo_url):
        """
        Ensure we have the REAL authoritative repo for the target user.
        This is at: <project_root>/<handle>-social/

        This is the repo we will write the LIKE into and push to GitHub.
        """
        # Step 1: Go from:
        #   <project_root>/lina-social/social
        # → <project_root>/lina-social
        # → <project_root>
        project_root = os.path.dirname(os.path.dirname(self.social_root))

        # Step 2: Construct the real repo folder name
        repo_name = handle.replace(".social", "") + "-social"

        # Step 3: Build the full path to the real repo
        target_repo_path = os.path.join(project_root, repo_name)

        # Step 4: Clone or pull the real repo
        if not os.path.exists(target_repo_path):
            print(f"[LIKE] Cloning real repo: {repo_url}")
            git.Repo.clone_from(repo_url, target_repo_path)
        else:
            print(f"[LIKE] Pulling latest changes for {handle}")
            repo = git.Repo(target_repo_path)
            repo.remotes.origin.pull()

        return target_repo_path

    def generate_like_id(self, repo_path):
        """
        Generate like-001, like-002, etc.
        Consistent with ActionBase: extract numeric suffixes and compute max+1.
        """
        actions_dir = os.path.join(repo_path, "social", "actions")
        os.makedirs(actions_dir, exist_ok=True)

        numbers = []

        for name in os.listdir(actions_dir):
            if not name.startswith("like-") or not name.endswith(".json"):
                continue

            try:
                # Extract numeric part: like-003.json → 003
                num_str = name.split("-")[1].replace(".json", "")
                num = int(num_str)
                numbers.append(num)
            except Exception:
                continue

        next_num = (max(numbers) + 1) if numbers else 1
        return f"like-{next_num:03d}"
    
    def _load_identity(self):
        """
        Load identity keys from client/state/<identity>/keystore/private.key
        and publicKey from profile.json.
        """

        # Load publicKey from profile.json
        profile_path = os.path.join(self.social_root, "profile.json")
        with open(profile_path, "r") as f:
            profile = json.load(f)
        public_key = profile["publicKey"]

        # Load identity.json
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        identity_json_path = os.path.join(project_root, "client", "identity.json")

        with open(identity_json_path, "r") as f:
            identity_data = json.load(f)
        active_identity = identity_data["activeIdentity"]

        # Load private key from client/state/<activeIdentity>/keystore/private.key
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


    



    


