from unittest.mock import Mock

from git import Repo

from src.replication import replicator as replicator_module
from src.replication.replicator import Replicator


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
