import os
import json
import urllib.parse
from git import GitCommandError, Repo
from git.remote import PushInfo
from src.config import CANONICAL_REPO_URL, DIRECTORY_REPO_URL
from src.identity.signer import Signer
from src.utils.identity_loader import load_identity


class PublishManager:
    def __init__(self, project_root):
        self.project_root = project_root

    @staticmethod
    def _merge_directory_json(directory_repo):
        conflicted_files = set(directory_repo.index.unmerged_blobs())
        if conflicted_files != {"directory.json"}:
            directory_repo.git.merge("--abort")
            raise RuntimeError(
                "Cannot automatically merge social-directory conflicts: "
                + ", ".join(sorted(conflicted_files))
            )

        local_directory = json.loads(directory_repo.git.show(":2:directory.json"))
        remote_directory = json.loads(directory_repo.git.show(":3:directory.json"))

        for handle in local_directory.keys() & remote_directory.keys():
            local_key = local_directory[handle].get("publicKey")
            remote_key = remote_directory[handle].get("publicKey")
            if local_key != remote_key:
                directory_repo.git.merge("--abort")
                raise RuntimeError(
                    f"Conflicting registered public keys for '{handle}'; "
                    "resolve the identity change manually."
                )

        merged_directory = dict(remote_directory)
        merged_directory.update(local_directory)

        directory_path = os.path.join(
            directory_repo.working_tree_dir,
            "directory.json"
        )
        with open(directory_path, "w", encoding="utf-8") as directory_file:
            json.dump(merged_directory, directory_file, indent=2)
            directory_file.write("\n")

        directory_repo.git.add("directory.json")
        directory_repo.git.commit("--no-edit")

    @staticmethod
    def _push_directory(directory_repo):
        push_results = directory_repo.remotes.origin.push("main")
        failed_pushes = [
            result for result in push_results
            if result.flags & (PushInfo.ERROR | PushInfo.REJECTED)
        ]
        if failed_pushes:
            details = "; ".join(result.summary for result in failed_pushes)
            raise RuntimeError(f"[DIRECTORY] Push failed: {details}")

        print("[DIRECTORY] Push complete")

    @staticmethod
    def _sync_directory_repo(directory_repo):
        if directory_repo.is_dirty(untracked_files=True):
            raise RuntimeError(
                "The local social-directory repository has uncommitted changes; "
                "commit or resolve them before publishing."
            )

        origin = directory_repo.remotes.origin
        origin.fetch("main")
        try:
            directory_repo.git.merge("origin/main", "--no-edit")
        except GitCommandError:
            if not directory_repo.index.unmerged_blobs():
                raise
            PublishManager._merge_directory_json(directory_repo)

    def _directory_repo(self):
        directory_root = os.path.join(
            self.project_root,
            "social-directory"
        )
         # Clone directory repo if it does not exist locally
        if not os.path.exists(directory_root):
            print("[DIRECTORY] Cloning social-directory...")
            Repo.clone_from(
                DIRECTORY_REPO_URL,
                directory_root
            )

        directory_repo = Repo(directory_root)
        self._sync_directory_repo(directory_repo)
        return directory_repo

    @staticmethod
    def _assert_registered_key(directory, handle, public_key):
        entry = directory.get(handle)
        if entry is None:
            return
        if not isinstance(entry, dict):
            raise ValueError(f"Invalid social directory entry for '{handle}'")

        registered_key = entry.get("publicKey")
        if not registered_key:
            raise RuntimeError(
                f"Handle '{handle}' has no registered public key. "
                "Register its verified key before publishing."
            )
        if registered_key != public_key:
            raise RuntimeError(
                f"Refusing to replace the registered public key for '{handle}'. "
                "Use the identity recovery process to change keys."
            )

    def _ensure_registered_key(self, handle, public_key):
        directory_repo = self._directory_repo()
        directory_path = os.path.join(
            directory_repo.working_tree_dir,
            "directory.json"
        )
        with open(directory_path, "r", encoding="utf-8") as directory_file:
            directory = json.load(directory_file)
        self._assert_registered_key(directory, handle, public_key)

    def update_directory(self, handle, remote_url, public_key):
        directory_repo = self._directory_repo()
        directory_path = os.path.join(
            directory_repo.working_tree_dir,
            "directory.json"
        )
        with open(directory_path, "r", encoding="utf-8") as directory_file:
            directory = json.load(directory_file)

        self._assert_registered_key(directory, handle, public_key)
        entry = directory.get(handle, {})
        directory[handle] = {
            **entry,
            "repoURL": remote_url,
            "publicKey": public_key,
        }

        print(f"[DIRECTORY] Registering {handle} -> {remote_url}")

        # Save directory.json
        with open(directory_path, "w", encoding="utf-8") as f:
            json.dump(directory, f, indent=2)

        # Commit and push directory repo
        directory_repo.git.add("directory.json")

        if directory_repo.is_dirty(index=True, working_tree=True):
            directory_repo.index.commit(f"Register {handle}")

        self._push_directory(directory_repo)

    @staticmethod
    def github_pages_url(remote_url):
        try:
            parsed_url = urllib.parse.urlsplit(remote_url)
        except ValueError:
            return None

        if (
            parsed_url.scheme != "https"
            or parsed_url.netloc != "github.com"
            or parsed_url.query
            or parsed_url.fragment
        ):
            return None

        parts = parsed_url.path.strip("/").split("/")
        if len(parts) != 2 or not all(parts):
            return None

        owner, repository = parts
        if repository.lower().endswith(".git"):
            repository = repository[:-4]
        if not repository:
            return None

        pages_host = f"{owner.lower()}.github.io"
        if repository.lower() == pages_host:
            return f"https://{pages_host}/"
        return f"https://{pages_host}/{repository}/"

    def update_site_url(self, handle, remote_url, public_key, site_url):
        directory_repo = self._directory_repo()
        directory_path = os.path.join(
            directory_repo.working_tree_dir,
            "directory.json"
        )
        with open(directory_path, "r", encoding="utf-8") as directory_file:
            directory = json.load(directory_file)

        entry = directory.get(handle)
        if not isinstance(entry, dict):
            raise RuntimeError(
                f"Cannot register a site for '{handle}': handle is not in "
                "the social directory."
            )
        self._assert_registered_key(directory, handle, public_key)
        if entry.get("repoURL") != remote_url:
            raise RuntimeError(
                f"Cannot register a site for '{handle}': repository URL does "
                "not match the social directory."
            )

        if entry.get("siteURL") == site_url:
            return
        entry["siteURL"] = site_url

        with open(directory_path, "w", encoding="utf-8") as directory_file:
            json.dump(directory, directory_file, indent=2)
            directory_file.write("\n")

        directory_repo.git.add("directory.json")
        if directory_repo.is_dirty(index=True, working_tree=True):
            directory_repo.index.commit(f"Publish site for {handle}")
            self._push_directory(directory_repo)

    def publish(self, remote_url):
        """
        Publish the current user's repo to their GitHub remote.
        This is used for BOTH canonical and normal users.
        """
        identity = load_identity()
        identity_name = identity["activeIdentity"]
        repo_name = identity["repoPath"]  # e.g. bharat-social
        repo_root = os.path.join(self.project_root, repo_name)

        social_path = os.path.join(repo_root, "social")
        profile_path = os.path.join(social_path, "profile.json")

        print(f"[PUBLISH] Publishing {identity_name}.social → {remote_url}")

        repo = Repo(repo_root)

        with open(profile_path, "r", encoding="utf-8") as profile_file:
            profile = json.load(profile_file)
        handle = profile["handle"]
        public_key = profile["publicKey"]

        private_key_path = os.path.join(
            self.project_root,
            "client",
            "state",
            identity_name,
            "keystore",
            "private.key"
        )
        with open(private_key_path, "r", encoding="utf-8") as private_key_file:
            private_key = private_key_file.read()

        signer = Signer(private_key)
        derived_public_key = (
            "ed25519:" + signer.signing_key.verify_key.encode().hex()
        )
        if derived_public_key != public_key:
            raise ValueError(
                "Profile public key does not match the active identity's private key"
            )

        self._ensure_registered_key(handle, public_key)

        # ------------------------------------------------------------
        # 1. Set origin to user's GitHub repo
        # ------------------------------------------------------------
        if "origin" in repo.remotes:
            repo.remotes.origin.set_url(remote_url)
        else:
            repo.create_remote("origin", remote_url)

        # ------------------------------------------------------------
        # 2. Push main branch to GitHub
        # ------------------------------------------------------------
        print("[PUBLISH] Pushing repo to GitHub...")
        repo.git.push("--set-upstream", "origin", "main")

        # ------------------------------------------------------------
        # 3. Update profile.json with new repoURL
        # ------------------------------------------------------------
        profile["repoURL"] = remote_url

        # ------------------------------------------------------------
        # 4. Re-sign profile.json with user's private key
        # ------------------------------------------------------------
        profile["signature"] = signer.sign_json(profile)

        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)

        # Commit + push updated profile.json
        repo.git.add(profile_path)
        try:
            repo.git.commit("-m", "Update repoURL + signature")
        except:
            pass
        repo.git.push()

        # ------------------------------------------------------------
        # 5. Add canonical as a second remote (critical!)
        # ------------------------------------------------------------
        if "canonical" not in [r.name for r in repo.remotes]:
            print("[PUBLISH] Adding canonical remote...")
            repo.create_remote("canonical", CANONICAL_REPO_URL)

        # update directory
        self.update_directory(handle, remote_url, public_key)

        print("[PUBLISH] Complete.")
