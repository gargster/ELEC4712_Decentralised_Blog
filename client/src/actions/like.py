from src.actions.cross_action import CrossRepoActionBase

class LikeAction(CrossRepoActionBase):
    # Writes likes directly into the TARGET USER'S REAL REPO.
    # Reads repoURL from the nested clone's .git/config (Rahul model).
    def _extend(self, obj, target):
        obj["target"] = target
        return obj

    def perform_action(self, args, actions_dir):
        return self._create(
            "like",
            actions_path=actions_dir,
            target=args.target_action
        )