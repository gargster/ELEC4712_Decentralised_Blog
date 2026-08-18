import os
class StaticPublisher:
    # Publishes only profile.json to a user-chosen static hosting repo
    def __init__(self, project_root):
        self.project_root = project_root
        self.client_root = os.path.join(project_root, "client")

    def publish_profile(self, identity_name, pages_repo_path, hosted_base_url):
        # 1. Copy profile.json to static hosting 
        pass



