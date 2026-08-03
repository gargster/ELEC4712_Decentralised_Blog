import os
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
        repo_path = dl.resolve(handle)

        # 2. Load profile.json from that repo 
        profile_path = os.path.join(project_root, repo_path, "social", "profile.json")

        # 3. Verify profile.json 
        pv = ProfileVerifier(profile_path)
        info = pv.verify()

        # 4. Create follow action
        path, obj = self.create_follow(info["publicKey"])

        # 5. Update following.json
        fm = FollowManager(client_root)
        fm.add_follow(
                    handle = info["handle"],
                    public_key = info["publicKey"],
                    repo_url= info["repoURL"]
        )
        return path, obj
