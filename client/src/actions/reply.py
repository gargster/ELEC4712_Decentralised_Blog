from src.actions.cross_action import CrossRepoActionBase

class ReplyAction(CrossRepoActionBase):
    def _extend(self, obj, content, target):
        obj["content"] = content
        obj["inReplyTo"] = target
        return obj
    def perform_action(self, args, actions_dir):
        return self._create(
            "reply",
            actions_path=actions_dir,
            content=args.content,
            target=args.target_action
        )


 