import git
import json
import os

from src.actions.action_verifier import ActionVerifier
from src.discovery.profile_verifier import ProfileVerifier


class Replicator:
    def __init__(self, identity_repo_root):
        self.identity_repo_root = identity_repo_root
        self.repo = git.Repo(identity_repo_root)

    def _replicate_verified_actions(self, remote_name):
        ref = f"{remote_name}/main"
        action_files = self.repo.git.ls_tree(
            "-r", "--name-only", ref, "--", "social/actions"
        ).splitlines()
        replicated = 0

        for action_file in action_files:
            if not action_file.endswith(".json"):
                continue

            try:
                raw_action = self.repo.git.show(f"{ref}:{action_file}")
                action = json.loads(raw_action)
            except (git.GitCommandError, json.JSONDecodeError) as error:
                print(f"[REPLICATE] Rejected unreadable action {action_file}: {error}")
                continue

            if not ActionVerifier.verify(action):
                print(f"[REPLICATE] Rejected invalid action {action_file}")
                continue

            local_path = os.path.join(self.identity_repo_root, action_file)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "w", encoding="utf-8") as action_handle:
                json.dump(action, action_handle, indent=2)
            replicated += 1

        return replicated

    def _verified_remote_public_key(self, remote_name):
        ref = f"{remote_name}/main"
        raw_profile = self.repo.git.show(f"{ref}:social/profile.json")
        profile = json.loads(raw_profile)
        return ProfileVerifier(profile).verify()["publicKey"]

    def run(self):
        print("[REPLICATE] Starting replication (fetch + verify: actions only)")

        for remote in self.repo.remotes:
            if remote.name == "origin":
                continue

            print(f"[REPLICATE] Fetching from {remote.name} → {remote.url}")

            try:
                # 1. Fetch remote main
                remote.fetch("main")

                print(f"[REPLICATE] Verifying actions from {remote.name}/main...")
                self._verified_remote_public_key(remote.name)
                replicated = self._replicate_verified_actions(remote.name)

                # Only verified actions are written into the local actions directory.
                self.repo.git.add("social/actions")

                if self.repo.is_dirty(index=True, working_tree=True, untracked_files=True):
                    self.repo.git.commit(
                        "-m",
                        f"Merge verified actions from {remote.name}/main"
                    )

                print(f"[REPLICATE] Replicated {replicated} verified actions from {remote.name}")

            except (git.GitCommandError, json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"[REPLICATE] Failed to verify/replicate {remote.name}: {e}")
                continue

        # 5. Push updated main
        try:
            print("[REPLICATE] Pushing updated main to origin...")
            self.repo.remotes["origin"].push("main")
            print("[REPLICATE] Push complete")
        except git.GitCommandError as e:
            print(f"[REPLICATE] Failed to push main: {e}")

        print("[REPLICATE] Complete")
