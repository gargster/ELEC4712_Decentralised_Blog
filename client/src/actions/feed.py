import os
import json
import git

from src.actions.base import ActionBase


class ShowFeedAction(ActionBase):

    publish_locally = False

    def __init__(self, social_path):
        super().__init__(social_path)

        # Keeps track of users already visited.
        # Prevents infinite recursion if the following graph contains cycles.
        self.user_feed_processed = set()

    # --------------------------------------------------------
    # MAIN ENTRY POINT
    # --------------------------------------------------------

    def run(self, args):
        target_handle = args.target_handle

        # Start recursive traversal from the requested user.
        self.show_social_media(target_handle, self.social_path)

        return None, None

    # --------------------------------------------------------
    # RECURSIVE FEED TRAVERSAL
    # --------------------------------------------------------

    def show_social_media(self, target_handle, repo_path):

        # Prevent cycles:
        #
        # Carl -> Lina -> Carl
        #
        # Carl should only be processed once.
        if target_handle in self.user_feed_processed:
            return

        self.user_feed_processed.add(target_handle)

        print(f"\n========== FEED: {target_handle} ==========")

        # ----------------------------------------------------
        # 1. Process this user's actions
        # ----------------------------------------------------

        actions_dir = os.path.join(
            repo_path,
            "actions"
        )

        self.process_actions(actions_dir, target_handle)

        # ----------------------------------------------------
        # 2. Find repositories this user follows
        # ----------------------------------------------------

        following_dir = os.path.join(
            repo_path,
            "following_repos"
        )

        if not os.path.isdir(following_dir):
            return

        # ----------------------------------------------------
        # 3. Recursively process every followed user
        # ----------------------------------------------------

        for repo_name in os.listdir(following_dir):

            followed_repo_path = os.path.join(
                following_dir,
                repo_name
            )

            if not os.path.isdir(followed_repo_path):
                continue

            # Example:
            #
            # carl-social
            #     ↓
            # carl.social
            #
            follower_handle = repo_name.replace(
                "-social",
                ".social"
            )
            # followed_repo_path currently points to: /lina-social/social/following_repos/carl-social
            # We need to descend into its /social directory.
            followed_social_path = os.path.join(
                followed_repo_path,
                "social"
            )  

            self.show_social_media(
                follower_handle,
                followed_social_path
            )

    # --------------------------------------------------------
    # PROCESS ACTIONS
    # --------------------------------------------------------

    def process_actions(self, actions_dir, owner_handle):

        if not os.path.isdir(actions_dir):
            return

        for filename in sorted(os.listdir(actions_dir)):

            if not filename.endswith(".json"):
                continue

            file_path = os.path.join(
                actions_dir,
                filename
            )

            try:
                with open(
                    file_path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    data = json.load(f)

                print(
                    f"\n{owner_handle} | "
                    f"{data['type']} | "
                    f"{data['id']}"
                )

                print(
                    json.dumps(
                        data,
                        indent=4
                    )
                )

            except Exception as e:

                print(
                    f"Error reading "
                    f"{file_path}: {e}"
                )
