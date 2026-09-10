import git

class Replicator:
    def __init__(self, identity_repo_root):
        self.identity_repo_root = identity_repo_root
        self.repo = git.Repo(identity_repo_root)

    def run(self):
        print("[REPLICATE] Starting replication (fetch + merge)")

        for remote in self.repo.remotes:
            if remote.name == "origin":
                continue

            print(
                f"[REPLICATE] Fetching from {remote.name} "
                f"→ {remote.url}"
            )

            try:
                remote.fetch("main")

                print(
                    f"[REPLICATE] Merging "
                    f"{remote.name}/main into local main..."
                )

                self.repo.git.merge(f"{remote.name}/main")

                print(
                    f"[REPLICATE] Merge from "
                    f"{remote.name} complete"
                )

            except git.GitCommandError as e:
                print(
                    f"[REPLICATE] Failed to fetch/merge "
                    f"{remote.name}: {e}"
                )
                return

        try:
            print("[REPLICATE] Pushing updated main to origin...")
            self.repo.remotes["origin"].push("main")
            print("[REPLICATE] Push complete")

        except git.GitCommandError as e:
            print(f"[REPLICATE] Failed to push main: {e}")

        print("[REPLICATE] Complete")