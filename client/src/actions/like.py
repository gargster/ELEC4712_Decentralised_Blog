from src.actions.base import ActionBase

class LikeAction(ActionBase):
    def _extend(self, obj, target, targetHandle):
        obj["target"] = target
        obj["targetHandle"] = targetHandle
        return obj

    def create_like(self, target, targetHandle):
        return self._create(
            "like",
            target=target,
            targetHandle=targetHandle
        )

    def run(self, args):
        return self.create_like(
            args.target_action,
            args.target_handle
        )

