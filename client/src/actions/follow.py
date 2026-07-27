import os
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
        #return self.create_follow(args.target_public_key)
        # Create follow social action (e.g. follow-001.json)
        # Update following.json (local follow list)

        # Create the follow social action
        path, obj = self.create_follow(args.target_public_key)
        # Update following.json
        #client_root = os.path.dirname(os.path.dirname(__file__))
        client_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        fm = FollowManager(client_root)
        # Temporary until Discovery layer
        fm.add_follow(
            handle = args.target_public_key,
            public_key=args.target_public_key,
            repo_url="https://github.com/bgar5324/ELEC4712_Decentralised_Blog.git"
        )
        return path, obj
