from src.actions.base import ActionBase
class LikeAction(ActionBase):
    # Add fields unique to a "Like" action
    def _extend(self, obj, target):
        obj["target"] = target
        return obj 
    def create_like(self, target_id: str):
        return self._create("like", target=target_id)
