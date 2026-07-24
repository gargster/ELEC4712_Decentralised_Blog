# Responsible for publishing new social actiosn to the Git Repo
import os
# GitPython
from git import Repo
class GitPublisher:
    def __init__(self, repo_path: str):
        # repo_path: path to the Git repository reoot
        # currently this is the project root: ELEC4712_Decentralised_Blog/
        # but we will need to modify it to have separate repo with actions and profile etc alone
        self.repo_path = repo_path
        self.repo = self.load_or_init_repo()
    
    def load_or_init_repo(self) -> Repo:
        # Load existing repo if .git exists, otherwise intialise a new one.
        git_dir = os.path.join(self.repo_path, ".git")
        if not os.path.exists(git_dir):
            # Intitialise a new Git repo at repo_path
            return Repo.init(self.repo_path)
        # Load existing repo
        return Repo(self.repo_path)
    
    def publish(self, file_path: str, message: str):
        # Publish a single JSON action file:
        # file_path: absolute path to the JSON file (e.g. /social/actions/post-001.json)
        # message: commit message (e.g. "Add post-001")
        # Steps:
        # 1. Convert file_path to a path relative to repo root
        # 2. git add <relative path>
        # 3. git commit -m "<message>"
        # 4. git push origin

        # Ensure path is relative to repo root
        rel_path = os.path.relpath(file_path, self.repo_path)
        # Stage the file
        self.repo.git.add(rel_path)
        # Commit the change
        self.repo.index.commit(message)
        # Push to remote 'origin' (if configured)
        try:
            origin = self.repo.remote(name="origin")
            origin.push()
        except Exception as e:
            print("Warning: git push failed", e)





