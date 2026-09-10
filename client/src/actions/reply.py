from src.actions.base import ActionBase

class ReplyAction(ActionBase):
    def _extend(self, obj, content, target, targetHandle):
        obj["content"] = content
        obj["inReplyTo"] = target
        obj["targetHandle"] = targetHandle
        return obj

    def create_reply(self, content, target, targetHandle):
        return self._create(
            "reply",
            content=content,
            target=target,
            targetHandle=targetHandle
        )

    def run(self, args):
        return self.create_reply(
            args.content,
            args.target_action,
            args.target_handle
        )

 