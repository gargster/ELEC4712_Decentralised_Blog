import os
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
        # Temporary: resolve handle to local profile.json path
        #base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        base_dir = os.path.dirname(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(__file__)
                    )
                )
            )
        if handle == "bharat.social":
            profile_path = os.path.join(base_dir, "bharat-social", "social", "profile.json")
        elif handle == "alice.social":
            profile_path = os.path.join(base_dir, "alice-social", "social", "profile.json")
        else:
            raise ValueError(f"Unknown handle (temporary mapping): {handle}")
        # 1. Verify profile.json and extrac publicKey + repoURL
        pv = ProfileVerifier(profile_path)
        info = pv.verify()
        target_public_key = info["publicKey"]
        repo_url = info["repoURL"]

        # 2. Create the follow social action (signed JSON)
        path, obj = self.create_follow(target_public_key)

        # 3. Update following.json
        client_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


        fm = FollowManager(client_root)
        fm.add_follow(
            handle = info["handle"],
            public_key = target_public_key,
            repo_url= repo_url
        )
        return path, obj

        # # Create the follow social action
        # path, obj = self.create_follow(args.target_public_key)
        # # Update following.json
        # #client_root = os.path.dirname(os.path.dirname(__file__))
        # client_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        # fm = FollowManager(client_root)
        # # Temporary until Discovery layer
        # fm.add_follow(
        #     handle = args.target_public_key,
        #     public_key=args.target_public_key,
        #     repo_url="https://github.com/bgar5324/ELEC4712_Decentralised_Blog.git"
        # )
        # return path, obj
