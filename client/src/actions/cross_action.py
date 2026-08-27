import os
import git
from src.actions.base import ActionBase

class CrossRepoActionBase(ActionBase):
    """
    Base class for cross‑repo actions (like, reply).
    Handles:
    - nested clone lookup
    - safety check
    - reading .git/config
    - cloning/pulling real repo
    - commit + push
    """
    publish_locally = False
    
    # --------------------------------------------------------
    # MAIN ENTRY POINT
    # ---------------------------------------------------------
    def run(self, args):
        target_handle = args.target_handle        # e.g. carl.social
        target_action = args.target_action        # e.g. post-003
        # 1. Locate nested clone of target user
        nested_clone_path = self.get_nested_clone_path(target_handle)

        # REQUIRED SAFETY CHECK
        if not os.path.exists(nested_clone_path):
            raise Exception(f"You must follow {target_handle} before performing this action.")

        # 2. Read real repo URL from nested clone's .git/config
        repo_url = self.get_repo_url_from_git_config(nested_clone_path)

        # 3. Clone/pull the target user's real repo into project root
        real_repo_path = self.ensure_real_repo_clone(target_handle, repo_url)

        # 4. Target repo's actions directory
        actions_dir = os.path.join(real_repo_path, "social", "actions")

        # 5. Delegate to child class
        path, obj = self.perform_action(args, actions_dir)

        # 6. Commit + push target repo
        repo = git.Repo(real_repo_path)
        repo.git.add(path)
        repo.index.commit(f"Add {obj['id']}")
        repo.remotes.origin.push()
        print(f"[{obj['type'].upper()}] Added {obj['id']} to {target_handle}'s real repo.")
        return path, obj

    # ---------------------------------------------------------
    # SHARED CROSS-REPO HELPER METHODS
    # ---------------------------------------------------------

    def get_nested_clone_path(self, handle):
        """
        Locate the nested clone inside:
        <active-identity-repo>/social/following_repos/<handle>-social/
        """
        repo_name = handle.replace(".social", "") + "-social"
        return os.path.join(self.social_path, "following_repos", repo_name)

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
        project_root = os.path.dirname(os.path.dirname(self.social_path))

        # Step 2: Construct the real repo folder name
        repo_name = handle.replace(".social", "") + "-social"

        # Step 3: Build the full path to the real repo
        target_repo_path = os.path.join(project_root, repo_name)

        # Step 4: Clone or pull the real repo
        if not os.path.exists(target_repo_path):
            print(f"[CROSS-REPO] Cloning real repo: {repo_url}")
            git.Repo.clone_from(repo_url, target_repo_path)
        else:
            print(f"[CROSS-REPO] Pulling latest changes for {handle}")
            repo = git.Repo(target_repo_path)
            repo.remotes.origin.pull()

        return target_repo_path
