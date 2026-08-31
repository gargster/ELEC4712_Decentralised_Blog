import os
import json
from collections import defaultdict
from src.actions.base import ActionBase


class ShowFeedAction(ActionBase):

    publish_locally = False

    def __init__(self, social_path):
        super().__init__(social_path)

        # Prevent infinite recursion
        self.user_feed_processed = set()

        # Flat list of all actions collected from you + followed users
        self.collected_actions = []

        # Map: publicKey → handle (needed to show who actually liked/replied)
        self.pubkey_to_handle = {}

        # Indexed actions (posts, likes, replies, follows)
        self.indexed = None

        # Structured sections
        self.my_posts = []
        self.my_following = set()
        #self.my_followers = set()
        self.followed_users_posts = []

    # --------------------------------------------------------
    # MAIN ENTRY POINT
    # --------------------------------------------------------

    def run(self, args):
        active_handle = self.get_active_handle()

        # 1. Recursively collect actions + profile keys
        self.collect_actions(active_handle, self.social_path)

        # 2. Build indexes (posts, likes, replies, follows)
        indexed_actions = self.index_actions(self.collected_actions)
        self.indexed = indexed_actions

        # 3. Categorize into sections
        self.categorize_sections(active_handle, indexed_actions)

        # 4. Render structured feed
        self.render_structured_feed(active_handle)

        return None, None

    def get_active_handle(self):
        repo_name = os.path.basename(os.path.dirname(self.social_path))
        return repo_name.replace("-social", ".social")

    # --------------------------------------------------------
    # RECURSIVE COLLECTION
    # --------------------------------------------------------

    def collect_actions(self, handle, repo_path):

        if handle in self.user_feed_processed:
            return

        self.user_feed_processed.add(handle)

        # Load profile.json to map publicKey → handle
        profile_path = os.path.join(repo_path, "profile.json")
        if os.path.isfile(profile_path):
            try:
                with open(profile_path, "r", encoding="utf-8") as pf:
                    profile = json.load(pf)
                    public_key = profile.get("publicKey")
                    if public_key:
                        self.pubkey_to_handle[public_key] = handle
            except Exception as e:
                print(f"Error reading profile.json for {handle}: {e}")

        # Load actions
        actions_dir = os.path.join(repo_path, "actions")

        if os.path.isdir(actions_dir):
            for filename in os.listdir(actions_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(actions_dir, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            action_data = json.load(f)

                            # Track which repo this action came from
                            action_data["owner_handle"] = handle

                            self.collected_actions.append(action_data)

                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")

        # Traverse following_repos
        following_dir = os.path.join(repo_path, "following_repos")
        if not os.path.isdir(following_dir):
            return

        for repo_name in os.listdir(following_dir):
            followed_repo_path = os.path.join(following_dir, repo_name)
            if not os.path.isdir(followed_repo_path):
                continue

            followed_handle = repo_name.replace("-social", ".social")
            followed_social_path = os.path.join(followed_repo_path, "social")

            self.collect_actions(followed_handle, followed_social_path)

    # --------------------------------------------------------
    # INDEXING
    # --------------------------------------------------------

    def index_actions(self, actions_list):

        posts_by_id = {}
        likes_by_target = defaultdict(list)
        replies_by_target = defaultdict(list)
        follows = []

        for action in actions_list:
            action_type = action["type"]

            if action_type == "post":
                posts_by_id[action["id"]] = action

            elif action_type == "like":
                likes_by_target[action["target"]].append(action)

            elif action_type == "reply":
                replies_by_target[action["inReplyTo"]].append(action)

            elif action_type == "follow":
                follows.append(action)

        return {
            "posts": posts_by_id,
            "likes": likes_by_target,
            "replies": replies_by_target,
            "follows": follows,
        }

    # --------------------------------------------------------
    # CATEGORIZE SECTIONS
    # --------------------------------------------------------

    def categorize_sections(self, active_handle, indexed):

        posts = indexed["posts"]
        follows = indexed["follows"]

        # --- My posts ---
        for post in posts.values():
            if post["owner_handle"] == active_handle:
                self.my_posts.append(post)

        # --- Who I follow ---
        for follow_action in follows:
            if follow_action["owner_handle"] == active_handle:
                target_pk = follow_action["target"]
                target_handle = self.pubkey_to_handle.get(target_pk, target_pk)
                self.my_following.add(target_handle)

        # --- Who follows me ---
        # for follow_action in follows:
        #     target_pk = follow_action["target"]
        #     target_handle = self.pubkey_to_handle.get(target_pk, target_pk)
        #     if target_handle == active_handle:
        #         follower_pk = follow_action["author"]
        #         follower_handle = self.pubkey_to_handle.get(follower_pk, follower_pk)
        #         self.my_followers.add(follower_handle)

        # --- Posts from people I follow ---
        for post in posts.values():
            if post["owner_handle"] in self.my_following:
                self.followed_users_posts.append(post)

        # Sort posts chronologically
        self.my_posts.sort(key=lambda p: p["created"])
        self.followed_users_posts.sort(key=lambda p: p["created"])

    # --------------------------------------------------------
    # RENDER STRUCTURED FEED
    # --------------------------------------------------------

    def render_structured_feed(self, active_handle):

        print("\n===========================================================\n")

        # -------------------------
        # MY POSTS
        # -------------------------
        print("===== MY POSTS =====\n")
        if not self.my_posts:
            print("(no posts)\n")
        else:
            for post in self.my_posts:
                print(f"{active_handle} — {post['created']}")
                print(f"POST: {post.get('content','')}\n")
                print("----------------------------------------\n")

        # -------------------------
        # PEOPLE I FOLLOW
        # -------------------------
        print("===== PEOPLE I FOLLOW =====\n")
        if not self.my_following:
            print("(you follow no one)\n")
        else:
            for handle in sorted(self.my_following):
                print(f"- {handle}")
            print("\n----------------------------------------\n")

        # -------------------------
        # MY FOLLOWERS
        # -------------------------
        # print("===== MY FOLLOWERS =====\n")
        # if not self.my_followers:
        #     print("(no followers)\n")
        # else:
        #     for handle in sorted(self.my_followers):
        #         print(f"- {handle}")
        #     print("\n----------------------------------------\n")

        # -------------------------
        # FEED FROM PEOPLE I FOLLOW
        # -------------------------
        print("===== FEED FROM PEOPLE I FOLLOW =====\n")
        if not self.my_following:
            print("(no feed available — you are not following anyone)\n")
            return  # stop rendering feed section entirely

        for post in self.followed_users_posts:
            owner = post["owner_handle"]
            post_id = post["id"]
            content = post.get("content", "")
            created = post["created"]

            print(f"{owner} — {created}")
            print(f"POST: {content}")

            # Likes
            # like_actions = self.indexed["likes"].get(post_id, [])
            # If same author of like likes the same post more than once, should display only once
            raw_likes = self.indexed["likes"].get(post_id, [])
            unique_likes = {}
            for like_action in raw_likes:
                liker_pk = like_action["author"]
                unique_likes[liker_pk] = like_action

            like_actions = list(unique_likes.values())


            if like_actions:
                print(f"  ❤️ {len(like_actions)} likes")
                for like_action in like_actions:
                    liker_pk = like_action["author"]
                    liker_handle = self.pubkey_to_handle.get(liker_pk, liker_pk)
                    print(f"    - {liker_handle} liked this")

            # Replies
            reply_actions = self.indexed["replies"].get(post_id, [])
            if reply_actions:
                print(f"  💬 {len(reply_actions)} replies")
                for reply_action in reply_actions:
                    replier_pk = reply_action["author"]
                    replier_handle = self.pubkey_to_handle.get(replier_pk, replier_pk)
                    print(f"    - {replier_handle}: {reply_action['content']}")

            print("\n----------------------------------------\n")
