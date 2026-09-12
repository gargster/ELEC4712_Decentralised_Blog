import git
import os

class Replicator:
    def __init__(self, identity_repo_root):
        self.identity_repo_root = identity_repo_root
        self.repo = git.Repo(identity_repo_root)

    def run(self):
        print("[REPLICATE] Starting replication (fetch + merge: actions only)")

        for remote in self.repo.remotes:
            if remote.name == "origin":
                continue

            print(f"[REPLICATE] Fetching from {remote.name} → {remote.url}")

            try:
                # 1. Fetch remote main
                remote.fetch("main")

                print(f"[REPLICATE] Merging actions from {remote.name}/main...")

                # 2. Merge ONLY the actions directory
                # This checks out the remote's version of social/actions
                # into the current working tree, without touching profile.json.
                self.repo.git.checkout(
                    f"{remote.name}/main",
                    "--",
                    "social/actions"
                )

                # 3. Stage the updated actions
                self.repo.git.add("social/actions")

                # 4. Commit the merge of actions
                self.repo.git.commit(
                    "-m",
                    f"Merge actions from {remote.name}/main"
                )

                print(f"[REPLICATE] Actions merged from {remote.name}")

            except git.GitCommandError as e:
                print(f"[REPLICATE] Failed to fetch/merge {remote.name}: {e}")
                continue

        # 5. Push updated main
        try:
            print("[REPLICATE] Pushing updated main to origin...")
            self.repo.remotes["origin"].push("main")
            print("[REPLICATE] Push complete")
        except git.GitCommandError as e:
            print(f"[REPLICATE] Failed to push main: {e}")

        print("[REPLICATE] Complete")
