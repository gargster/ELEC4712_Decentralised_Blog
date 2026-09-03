import os

import git
from src.discovery.directory_loader import DirectoryLoader
from src.discovery.profile_verifier import ProfileVerifier
from src.actions.base import ActionBase
from src.replication.follow_manager import FollowManager
import shutil, time

class FollowAction(ActionBase):
    # Add fields unique to a "follow" action
    def _extend(self, obj, target):
        obj["target"] = target
        return obj 
    
    def create_follow(self, target_public_key: str):
        return self._create("follow", target=target_public_key)


    # NEW: follow = clone from ORG
    def clone_from_org(self, handle, repo_url, client_root):
        """
        Clone/pull the target user's repo from the GitHub ORG.
        This is Rahul's model: follow = clone.
        """
        # new: e.g. following_repos folder in lina-social/social
        following_root = os.path.join(self.social_path, "following_repos")

        os.makedirs(following_root, exist_ok=True)

        repo_name = handle.replace(".social", "") + "-social"
        local_repo_path = os.path.join(following_root, repo_name)

        if not os.path.exists(local_repo_path):
            print(f"[FOLLOW] Cloning {handle} from ORG...")
            git.Repo.clone_from(repo_url, local_repo_path)
        else:
            print(f"[FOLLOW] Pulling updates for {handle} from ORG...")
            repo = git.Repo(local_repo_path)
            repo.remotes.origin.pull()

        return local_repo_path
    def run(self, args):
        # Discovery-aware follow:
        # - args.handle is a human-readable handle (e.g. 'bharat.social')
        # - Resolve handle -> profile.json
        # - Verify profile.json
        # - Extract publicKey + repoURL
        # - Update following.json
        # - Create follow-XXX.json social action
        handle = args.target_handle

        # project root (ELEC4712_Decentralised_Blog/)
        # project_root = os.path.dirname(
        #     os.path.dirname(
        #         os.path.dirname(
        #             os.path.dirname(__file__)
        #         )
        #     )
        # )
        client_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(__file__)
            )
        )
        # -------------------------------
        # REMOVE DIRECTORY.JSON COMPLETELY
        # -------------------------------
        repo_name = handle.replace(".social", "") + "-social"
        repo_url = f"https://github.com/social-protocol-org/{repo_name}"
        nested_clone_path = self.clone_from_org(handle, repo_url, client_root)

        profile_path = os.path.join(nested_clone_path, "social", "profile.json")
        pv = ProfileVerifier(profile_path)
        verified = pv.verify()
        # Remove .git inside nested clone so it becomes a normal folder
        git_dir = os.path.join(nested_clone_path, ".git")
        if os.path.exists(git_dir):
            try:
                repo = git.Repo(nested_clone_path)
                repo.close()
            except Exception:
                pass
            for _ in range(5):
                try:
                    shutil.rmtree(git_dir)
                    break
                except PermissionError:
                    time.sleep(0.2)
        # 5. Create follow action
        path, obj = self.create_follow(verified["publicKey"])

        identity_repo_root = os.path.dirname(self.social_path)
        identity_repo = git.Repo(identity_repo_root)
        identity_repo.git.add(A=True)
        identity_repo.index.commit(f"Follow {handle}")
        identity_repo.remotes.origin.push()

        return path, obj

