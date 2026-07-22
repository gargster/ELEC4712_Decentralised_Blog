from src.actions.base import ActionBase
class ReplyAction(ActionBase):
    def _extend(self, obj, content, inReplyTo):
        obj["content"] = content
        obj["inReplyTo"] = inReplyTo
        return obj
    
    def create_reply(self, parent_id: str, content: str):
        return self._create("reply", content=content, inReplyTo=parent_id)
    
    def run(self, args):
        return self.create_reply(args.parent_id, args.content)

 