from src.actions.base import ActionBase
class PostAction(ActionBase):
    # Child-specific hook
    def _extend(self, obj, content):
        obj["content"] = content
        return obj

    # Implements the "post" action as defined in design.md
    def create_post(self, content: str):
        return self._create("post", content=content)
