import io
import json
from types import SimpleNamespace

from src.actions import feed as feed_module
from src.actions.feed import ShowFeedAction
from src.config import DIRECTORY_JSON_URL
from src.identity.keypair import KeyPair
from src.identity.signer import Signer


def _signed_action(fields, keypair):
    action = dict(fields)
    action["signature"] = Signer(keypair.private_key()).sign_json(action)
    return action


def _write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def _feed_fixture(tmp_path, monkeypatch):
    social_path = tmp_path / "alice-social" / "social"
    actions_path = social_path / "actions"
    actions_path.mkdir(parents=True)

    alice = KeyPair()
    bob = KeyPair()
    carol = KeyPair()
    _write_json(
        social_path / "profile.json",
        {"handle": "alice.social", "publicKey": alice.public_key()},
    )

    bob_url = "https://raw.githubusercontent.com/bob/bob-social/main/social/profile.json"
    carol_url = "https://raw.githubusercontent.com/carol/carol-social/main/social/profile.json"
    directory = {
        "bob.social": {"repoURL": "https://github.com/bob/bob-social.git"},
        "carol.social": {"repoURL": "https://github.com/carol/carol-social.git"},
    }
    remote_profiles = {
        bob_url: {"handle": "bob.social", "publicKey": bob.public_key()},
        carol_url: {"handle": "carol.social", "publicKey": carol.public_key()},
    }

    def open_url(url, timeout):
        value = directory if url == DIRECTORY_JSON_URL else remote_profiles[url]
        return io.BytesIO(json.dumps(value).encode("utf-8"))

    monkeypatch.setattr("src.actions.feed.urllib.request.urlopen", open_url)

    records = [
        _signed_action(
            {
                "id": "follow-alice.social-001",
                "type": "follow",
                "author": alice.public_key(),
                "target": bob.public_key(),
                "created": "2026-01-01T00:00:00Z",
            },
            alice,
        ),
        _signed_action(
            {
                "id": "post-alice.social-001",
                "type": "post",
                "author": alice.public_key(),
                "content": "Alice's post",
                "created": "2026-01-01T00:00:30Z",
            },
            alice,
        ),
        _signed_action(
            {
                "id": "post-bob.social-001",
                "type": "post",
                "author": bob.public_key(),
                "content": "Bob's post",
                "created": "2026-01-01T00:01:00Z",
            },
            bob,
        ),
        _signed_action(
            {
                "id": "post-carol.social-001",
                "type": "post",
                "author": carol.public_key(),
                "content": "Carol's post",
                "created": "2026-01-01T00:02:00Z",
            },
            carol,
        ),
        _signed_action(
            {
                "id": "like-alice.social-001",
                "type": "like",
                "author": alice.public_key(),
                "target": "post-bob.social-001",
                "targetHandle": "bob.social",
                "created": "2026-01-01T00:03:00Z",
            },
            alice,
        ),
        _signed_action(
            {
                "id": "like-alice.social-002",
                "type": "like",
                "author": alice.public_key(),
                "target": "post-bob.social-001",
                "targetHandle": "bob.social",
                "created": "2026-01-01T00:04:00Z",
            },
            alice,
        ),
        _signed_action(
            {
                "id": "reply-carol.social-001",
                "type": "reply",
                "author": carol.public_key(),
                "content": "A reply",
                "inReplyTo": "post-bob.social-001",
                "targetHandle": "bob.social",
                "created": "2026-01-01T00:05:00Z",
            },
            carol,
        ),
    ]
    for record in records:
        _write_json(actions_path / f"{record['id']}.json", record)

    invalid = dict(records[1])
    invalid["content"] = "Tampered"
    _write_json(actions_path / "tampered.json", invalid)
    (actions_path / "broken.json").write_text("{", encoding="utf-8")
    (actions_path / "notes.txt").write_text("ignored", encoding="utf-8")

    return social_path


def test_feed_renders_posts_engagement_and_rejects_bad_action_files(
    tmp_path, monkeypatch, capsys
):
    social_path = _feed_fixture(tmp_path, monkeypatch)
    feed = ShowFeedAction(str(social_path))

    feed.run(SimpleNamespace(followers_only=False))

    output = capsys.readouterr().out
    assert "bob.social" in output
    assert "Alice's post" in output
    assert "Bob's post" in output
    assert "Carol's post" in output
    assert "1 likes" in output  # duplicate likes by Alice are collapsed
    assert "alice.social liked this" in output
    assert "carol.social: A reply" in output
    assert "Rejected invalid action" in output
    assert "Error reading" in output


def test_followers_only_feed_excludes_unfollowed_and_own_posts(
    tmp_path, monkeypatch, capsys
):
    social_path = _feed_fixture(tmp_path, monkeypatch)
    feed = ShowFeedAction(str(social_path))

    feed.run(SimpleNamespace(followers_only=True))

    output = capsys.readouterr().out
    assert "Bob's post" in output
    assert "Carol's post" not in output
    assert "Alice's post" not in output
    assert "FOLLOW-ONLY MODE" in output


def test_followers_only_feed_reports_when_no_users_are_followed(
    tmp_path, monkeypatch, capsys
):
    social_path = tmp_path / "alice-social" / "social"
    actions_path = social_path / "actions"
    actions_path.mkdir(parents=True)
    _write_json(
        social_path / "profile.json",
        {"handle": "alice.social", "publicKey": "alice-key"},
    )
    monkeypatch.setattr(
        "src.actions.feed.urllib.request.urlopen",
        lambda url, timeout: io.BytesIO(b"{}"),
    )

    ShowFeedAction(str(social_path)).run(SimpleNamespace(followers_only=True))

    assert "you are not following anyone" in capsys.readouterr().out


def test_load_profiles_from_remotes_skips_origin_and_handles_bad_remote(
    tmp_path, monkeypatch, capsys
):
    remote_git = SimpleNamespace(
        show=lambda ref: json.dumps(
            {"handle": "bob.social", "publicKey": "bob-key"}
        )
    )
    repo = SimpleNamespace(
        working_tree_dir=str(tmp_path),
        remotes=[
            SimpleNamespace(name="origin"),
            SimpleNamespace(name="bob.social"),
            SimpleNamespace(
                name="broken.social",
            ),
        ],
    )

    def show(ref):
        if ref.startswith("broken.social/"):
            raise RuntimeError("missing remote profile")
        return remote_git.show(ref)

    git_cmd = SimpleNamespace(show=show)
    monkeypatch.setattr(feed_module.git, "Repo", lambda path: repo)
    monkeypatch.setattr(feed_module.git.cmd, "Git", lambda path: git_cmd)
    social_path = tmp_path / "alice-social" / "social"
    feed = ShowFeedAction(str(social_path))

    feed.load_profiles_from_remotes()

    assert feed.pubkey_to_handle == {"bob-key": "bob.social"}
    assert "Could not load profile from remote broken.social" in capsys.readouterr().out


def test_profile_mapping_handles_missing_files_directory_errors_and_unknown_keys(
    tmp_path, monkeypatch, capsys
):
    social_path = tmp_path / "alice-social" / "social"
    social_path.mkdir(parents=True)
    feed = ShowFeedAction(str(social_path))
    feed.actions = [{"author": "unknown-key"}, {"type": "post"}]
    monkeypatch.setattr(
        feed_module.urllib.request,
        "urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("offline")),
    )

    feed.load_profile_mapping()

    assert feed.pubkey_to_handle == {"unknown-key": "unknown-key"}
    output = capsys.readouterr().out
    assert "Could not load profile.json" in output
    assert "Could not load discovery directory" in output


def test_profile_mapping_discovers_github_profile_and_skips_other_hosts(
    tmp_path, monkeypatch, capsys
):
    social_path = tmp_path / "alice-social" / "social"
    social_path.mkdir(parents=True)
    _write_json(
        social_path / "profile.json",
        {"handle": "alice.social", "publicKey": "alice-key"},
    )
    remote_url = (
        "https://raw.githubusercontent.com/bob/bob-social/main/social/profile.json"
    )

    def open_url(url, timeout):
        if url == DIRECTORY_JSON_URL:
            directory = {
                "bob.social": {"repoURL": "https://github.com/bob/bob-social.git"},
                "other.social": {"repoURL": "https://gitlab.com/other/repo"},
                "offline.social": {"repoURL": "https://github.com/offline/repo"},
            }
            return io.BytesIO(json.dumps(directory).encode())
        if url == remote_url:
            return io.BytesIO(b'{"handle": "bob.social", "publicKey": "bob-key"}')
        raise OSError("not available")

    monkeypatch.setattr(feed_module.urllib.request, "urlopen", open_url)
    feed = ShowFeedAction(str(social_path))
    feed.load_profile_mapping()

    assert feed.pubkey_to_handle == {
        "alice-key": "alice.social",
        "bob-key": "bob.social",
    }
    assert "Could not load profile for offline.social" in capsys.readouterr().out
