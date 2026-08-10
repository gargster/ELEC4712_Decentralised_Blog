import os

import git
from src.discovery.directory_loader import DirectoryLoader
from src.discovery.profile_verifier import ProfileVerifier
from src.actions.base import ActionBase
from src.replication.follow_manager import FollowManager

class FollowAction(ActionBase):
    # Add fields unique to a "follow" action
    def _extend(self, obj, target):
        obj["target"] = target
        return obj 
    
    def create_follow(self, target_public_key: str):
        return self._create("follow", target=target_public_key)
    
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
        # project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        # # client root (ELEC4712_Decentralised_Blog/client/)
        # client_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(__file__)
                )
            )
        )
        client_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(__file__)
            )
        )
        # 1. Resolve handle to repoURL 
        dl = DirectoryLoader(client_root)

        info = dl.resolve(handle)
        # info = { "localPath": "...", "repoURL": "..." }
        # 2. AUTO-CLONE / AUTO-PULL: If the repo is not present locally, clone it. If it is present, pull the latest changes.
        local_repo_path = os.path.join(project_root, info["localPath"])
        if not os.path.exists(local_repo_path):
            # If the repo does NOT exist locally → clone it
            print(f"[FOLLOW] Local repo missing, cloning {info['repoURL']}...")
            git.Repo.clone_from(info["repoURL"], local_repo_path)
        else:
            print(f"[FOLLOW] Local repo exists, pulling latest changes from {info['repoURL']}...")
            repo = git.Repo(local_repo_path)
            origin = repo.remotes.origin
            origin.pull()

            # HARD RESET TO MATCH REMOTE EXACTLY
            print("[FOLLOW] Resetting local repo to match origin/main...")
            repo.git.reset('--hard', 'origin/main')

        # 3. Load profile.json from the updated local repo 
        profile_path = os.path.join(local_repo_path, "social", "profile.json")

        # 4. Verify profile.json 
        pv = ProfileVerifier(profile_path)
        verified = pv.verify()

        # 5. Create follow action
        path, obj = self.create_follow(verified["publicKey"])

        # 6. Update following.json
        fm = FollowManager(client_root)
        fm.add_follow(
                    handle = verified["handle"],
                    public_key = verified["publicKey"],
                    repo_url= info["repoURL"]
        )
        return path, obj
