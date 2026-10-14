import json
from unittest.mock import Mock

from git import GitCommandError, Repo

from src.replication import replicator as replicator_module
from src.replication.replicator import Replicator
from src.identity.keypair import KeyPair
from src.identity.signer import Signer


def create_repo(path, branch):
    repo = Repo.init(path)
    with repo.config_writer() as config:
        config.set_value("user", "name", "Replicator Test")
        config.set_value("user", "email", "replicator-test@example.com")
    repo.git.checkout("-b", branch)
    (path / "README").write_text("test repository", encoding="utf-8")
    repo.git.add("README")
    repo.index.commit("Initialize repository")
    return repo


def test_replicate_refuses_non_main_branch_without_pushing(tmp_path, capsys):
    user_repo_path = tmp_path / "user"
    bare_origin_path = tmp_path / "origin.git"
    bare_origin = Repo.init(bare_origin_path, bare=True)
    repo = create_repo(user_repo_path, "gh-pages")
    repo.create_remote("origin", str(bare_origin_path))
    original_commit = repo.head.commit.hexsha

    Replicator(str(user_repo_path)).run()

    output = capsys.readouterr().out
    assert "Refusing to replicate from branch 'gh-pages'" in output
    assert repo.head.commit.hexsha == original_commit
    assert "refs/heads/gh-pages" not in bare_origin.refs


def test_replicate_still_pushes_from_main(monkeypatch, capsys):
    origin = Mock()

    class Remotes:
        def __iter__(self):
            return iter(())

        def __getitem__(self, name):
            assert name == "origin"
            return origin

    repo = Mock()
    repo.git.rev_parse.return_value = "main"
    repo.remotes = Remotes()
    monkeypatch.setattr(replicator_module.git, "Repo", lambda path: repo)

    Replicator("user").run()

    origin.push.assert_called_once_with("main")
    assert "Push complete" in capsys.readouterr().out


def _signed_record(fields, keypair):
    record = dict(fields)
    record["signature"] = Signer(keypair.private_key()).sign_json(record)
    return record


def test_replicate_imports_only_valid_action_json(tmp_path, capsys):
    origin_path = tmp_path / "origin.git"
    origin = Repo.init(origin_path, bare=True)
    user_path = tmp_path / "alice-social"
    user_repo = create_repo(user_path, "main")
    user_repo.create_remote("origin", str(origin_path))
    user_repo.git.push("--set-upstream", "origin", "main")
    (origin_path / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")

    remote_path = tmp_path / "bob-social"
    remote_repo = create_repo(remote_path, "main")
    bob = KeyPair()
    alice = KeyPair()
    social_path = remote_path / "social"
    actions_path = social_path / "actions"
    actions_path.mkdir(parents=True)
    profile = _signed_record(
        {
            "handle": "bob.social",
            "publicKey": bob.public_key(),
            "repoURL": "https://github.com/bob/bob-social.git",
        },
        bob,
    )
    (social_path / "profile.json").write_text(
        json.dumps(profile), encoding="utf-8"
    )

    valid_action = _signed_record(
        {
            "id": "post-alice.social-001",
            "type": "post",
            "author": alice.public_key(),
            "content": "Relayed post",
            "created": "2026-10-01T00:00:00Z",
        },
        alice,
    )
    invalid_action = dict(valid_action)
    invalid_action["content"] = "Tampered post"
    (actions_path / "valid.json").write_text(
        json.dumps(valid_action), encoding="utf-8"
    )
    (actions_path / "invalid.json").write_text(
        json.dumps(invalid_action), encoding="utf-8"
    )
    (actions_path / "malformed.json").write_text("{", encoding="utf-8")
    (actions_path / "notes.txt").write_text("not an action", encoding="utf-8")
    remote_repo.git.add(A=True)
    remote_repo.index.commit("Publish remote profile and actions")

    user_repo.create_remote("bob.social", str(remote_path))
    Replicator(str(user_path)).run()

    local_actions = user_path / "social" / "actions"
    assert json.loads((local_actions / "valid.json").read_text()) == valid_action
    assert not (local_actions / "invalid.json").exists()
    assert not (local_actions / "malformed.json").exists()
    assert not (local_actions / "notes.txt").exists()
    assert user_repo.git.show("origin/main:social/actions/valid.json")
    output = capsys.readouterr().out
    assert "Rejected invalid action social/actions/invalid.json" in output
    assert "Rejected unreadable action social/actions/malformed.json" in output
    assert "Replicated 1 verified actions from bob.social" in output


def test_replicate_reports_origin_push_failure(monkeypatch, capsys):
    origin = Mock()
    origin.push.side_effect = GitCommandError("push", "network unavailable")

    class Remotes:
        def __iter__(self):
            return iter(())

        def __getitem__(self, name):
            assert name == "origin"
            return origin

    repo = Mock()
    repo.git.rev_parse.return_value = "main"
    repo.remotes = Remotes()
    monkeypatch.setattr(replicator_module.git, "Repo", lambda path: repo)

    Replicator("user").run()

    assert "Failed to push main" in capsys.readouterr().out
