from src.actions.base import ActionBase

class FollowAction(ActionBase):
    # Add fields unique to a "follow" action
    def _extend(self, obj, target):
        obj["target"] = target
        return obj 
    def create_follow(self, target_public_key: str):
        return self._create("follow", target=target_public_key)