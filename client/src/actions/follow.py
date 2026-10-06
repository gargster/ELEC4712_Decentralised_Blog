import os
import git
import json
import urllib.request
from src.actions.base import ActionBase
from src.config import DIRECTORY_JSON_URL
from src.discovery.profile_verifier import ProfileVerifier


class FollowAction(ActionBase):

    def _extend(self, obj, target):
        obj["target"] = target
        return obj

    def create_follow(self, target_repo_url):
        return self._create("follow", target=target_repo_url)

    # -------------------------------------------------------
    # Git-native profile.json fetch (AFTER remote + fetch)
    # -------------------------------------------------------
    def fetch_profile_git(self, repo, handle):
        """
        Fetch profile.json using pure Git:
        1. git fetch <handle> main
        2. git show <handle>/main:social/profile.json
        """

        print(f"[FOLLOW] Fetching remote branch: {handle}/main")
        repo.remotes[handle].fetch("main")

        git_cmd = git.cmd.Git(repo.working_tree_dir)

        try:
            raw_json = git_cmd.show(f"{handle}/main:social/profile.json")
        except Exception as e:
            raise Exception(
                f"[FOLLOW] profile.json missing in remote branch {handle}/main\n{e}"
            )

        print("[FOLLOW] Successfully fetched profile.json via Git")
        return json.loads(raw_json)

    # -------------------------------------------------------
    # Add remote BEFORE fetching profile.json
    # -------------------------------------------------------
    def add_remote(self, repo, handle, repo_url):
        if handle not in [r.name for r in repo.remotes]:
            print(f"[FOLLOW] Adding remote {handle} → {repo_url}")
            repo.create_remote(handle, repo_url)
        else:
            print(f"[FOLLOW] Remote {handle} already exists")

    def _registered_identity(self, handle):
        with urllib.request.urlopen(DIRECTORY_JSON_URL, timeout=5) as response:
            directory = json.load(response)
        if not isinstance(directory, dict):
            raise ValueError("Social directory must be a JSON object")

        entry = directory.get(handle)
        if not isinstance(entry, dict):
            raise ValueError(
                f"Handle '{handle}' is not registered in the social directory"
            )

        registered_key = entry.get("publicKey")
        if not isinstance(registered_key, str) or not registered_key:
            raise ValueError(
                f"Handle '{handle}' has no registered public key in the social directory"
            )
        return entry

    # -------------------------------------------------------
    # Main FOLLOW logic
    # -------------------------------------------------------
    def run(self, args):
        handle = args.target_handle
        repo_url = args.target_repo_url

        print(f"[FOLLOW] Following {handle}")
        print(f"[FOLLOW] Repo URL = {repo_url}")

        registered_identity = self._registered_identity(handle)
        if registered_identity.get("repoURL") != repo_url:
            raise ValueError(
                f"Repository URL for '{handle}' does not match the social directory"
            )

        # Load identity repo
        identity_repo_root = os.path.dirname(self.social_path)
        repo = git.Repo(identity_repo_root)

        # Step 1: Add remote FIRST
        self.add_remote(repo, handle, repo_url)

        # Step 2: Fetch remote + read profile.json
        profile = self.fetch_profile_git(repo, handle)

        # Step 3: Verify profile.json
        pv = ProfileVerifier(profile)
        verified = pv.verify()
        if verified["handle"] != handle:
            raise ValueError(
                f"Requested handle '{handle}' does not match signed profile "
                f"handle '{verified['handle']}'"
            )
        if verified["publicKey"] != registered_identity["publicKey"]:
            raise ValueError(
                f"Public key for '{handle}' does not match the social directory"
            )
        if profile["repoURL"] != repo_url:
            raise ValueError(
                f"Signed repository URL for '{handle}' does not match the supplied URL"
            )
        target_public_key = verified["publicKey"]
        print(f"[FOLLOW] Verified publicKey = {target_public_key}")

        # Step 4: Create follow action JSON
        path, obj = self.create_follow(target_public_key)
        print(f"[FOLLOW] Created follow action at {path}")

        # Step 5: Commit + push
        repo.git.add(A=True)
        try:
            repo.index.commit(f"Follow {handle}")
        except:
            print("[FOLLOW] Nothing to commit")

        repo.remotes.origin.push()
        print("[FOLLOW] Pushed follow action to origin")
        return path, obj
