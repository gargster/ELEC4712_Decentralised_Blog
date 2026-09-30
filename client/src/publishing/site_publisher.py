import json
import os
import shutil

from git import GitCommandError, Repo
from git.remote import PushInfo

from src.actions.action_verifier import ActionVerifier
from src.discovery.profile_verifier import ProfileVerifier


class SitePublisher:
    def __init__(self, project_root: str, identity_repo_root: str):
        self.project_root = project_root
        self.identity_repo_root = identity_repo_root
        self.repo = Repo(identity_repo_root)
        self.social_path = os.path.join(identity_repo_root, "social")
        self.template_path = os.path.join(
            project_root,
            "canonical-social",
            "site-template"
        )

    def _load_profile(self, profile_path: str) -> dict:
        with open(profile_path, "r", encoding="utf-8") as profile_file:
            profile = json.load(profile_file)
        ProfileVerifier(profile).verify()
        return profile

    def _load_verified_actions(self) -> list[dict]:
        actions_path = os.path.join(self.social_path, "actions")
        actions = []

        for filename in sorted(os.listdir(actions_path)):
            if not filename.endswith(".json"):
                continue

            path = os.path.join(actions_path, filename)
            try:
                with open(path, "r", encoding="utf-8") as action_file:
                    action = json.load(action_file)
            except (OSError, json.JSONDecodeError) as error:
                print(f"[SITE] Rejected unreadable action {filename}: {error}")
                continue

            if not ActionVerifier.verify(action):
                print(f"[SITE] Rejected invalid action {filename}")
                continue

            actions.append(action)

        return actions

    def _load_profile_names(self, own_profile: dict) -> dict[str, str]:
        profiles = {
            own_profile["publicKey"]:
                own_profile.get("displayName") or own_profile["handle"]
        }

        for remote in self.repo.remotes:
            if remote.name == "origin":
                continue

            try:
                raw_profile = self.repo.git.show(
                    f"{remote.name}/main:social/profile.json"
                )
                remote_profile_data = json.loads(raw_profile)
                remote_profile = ProfileVerifier(remote_profile_data).verify()
                profiles[remote_profile["publicKey"]] = (
                    remote_profile_data.get("displayName")
                    or remote_profile["handle"]
                )
            except (
                GitCommandError,
                json.JSONDecodeError,
                KeyError,
                TypeError,
                ValueError,
            ) as error:
                print(
                    f"[SITE] Could not load verified profile from "
                    f"{remote.name}: {error}"
                )

        return profiles

    def _build_feed(self) -> dict:
        profile_path = os.path.join(self.social_path, "profile.json")
        profile = self._load_profile(profile_path)
        return {
            "profile": profile,
            "profiles": self._load_profile_names(profile),
            "actions": self._load_verified_actions(),
        }

    def _validate_template(self) -> None:
        required_files = ("index.html", "app.js", "style.css")
        if not os.path.isdir(self.template_path):
            raise FileNotFoundError(
                f"Site template not found: {self.template_path}"
            )

        missing_files = [
            name for name in required_files
            if not os.path.isfile(os.path.join(self.template_path, name))
        ]
        if missing_files:
            raise FileNotFoundError(
                "Site template is missing required files: "
                + ", ".join(missing_files)
            )

    def _prepare_branch(self) -> None:
        if self.repo.is_dirty(untracked_files=True):
            raise RuntimeError(
                "Commit or remove local changes in the user repository before "
                "publishing its site."
            )

        if self.repo.head.is_detached:
            raise RuntimeError(
                "Cannot publish the site while the user repository is in "
                "detached HEAD state."
            )

        if "origin" not in self.repo.remotes:
            raise RuntimeError(
                "The user repository needs an origin remote before its site "
                "can be published."
            )

        origin = self.repo.remotes.origin
        origin.fetch()
        remote_ref = next(
            (
                ref for ref in self.repo.refs
                if ref.path == "refs/remotes/origin/gh-pages"
            ),
            None
        )
        local_branch = next(
            (branch for branch in self.repo.branches if branch.name == "gh-pages"),
            None
        )

        if local_branch is not None:
            self.repo.git.checkout("gh-pages")
            if remote_ref is not None:
                self.repo.git.merge("--ff-only", remote_ref.path)
        elif remote_ref is not None:
            local_branch = self.repo.create_head("gh-pages", remote_ref)
            local_branch.set_tracking_branch(remote_ref)
            self.repo.git.checkout("gh-pages")
        else:
            self.repo.git.checkout("--orphan", "gh-pages")
            self.repo.git.rm("-r", "-f", ".")

    def _write_site_files(self, feed: dict) -> None:
        for item in os.listdir(self.template_path):
            source = os.path.join(self.template_path, item)
            destination = os.path.join(self.identity_repo_root, item)
            if os.path.isdir(source):
                shutil.copytree(source, destination, dirs_exist_ok=True)
            elif item != "feed.json":
                shutil.copy2(source, destination)

        with open(
            os.path.join(self.identity_repo_root, "feed.json"),
            "w",
            encoding="utf-8"
        ) as feed_file:
            json.dump(feed, feed_file, indent=2)
            feed_file.write("\n")

    def _commit_and_push(self) -> None:
        self.repo.git.add(A=True)
        if self.repo.is_dirty(index=True, working_tree=True):
            self.repo.index.commit("Publish social site")

        push_results = self.repo.remotes.origin.push("gh-pages")
        failed_pushes = [
            result for result in push_results
            if result.flags & (PushInfo.ERROR | PushInfo.REJECTED)
        ]
        if failed_pushes:
            details = "; ".join(result.summary for result in failed_pushes)
            raise RuntimeError(f"[SITE] Push failed: {details}")

    def publish(self) -> None:
        self._validate_template()
        feed = self._build_feed()

        original_branch = self.repo.active_branch.name
        try:
            self._prepare_branch()
            self._write_site_files(feed)
            self._commit_and_push()
            print("[SITE] Published site to gh-pages")
        finally:
            if self.repo.active_branch.name != original_branch:
                self.repo.git.checkout(original_branch)
