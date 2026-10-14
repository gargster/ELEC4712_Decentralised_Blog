from git import Repo

from src.publishing.git_publisher import GitPublisher


def _configure(repo):
    with repo.config_writer() as config:
        config.set_value("user", "name", "Git Publisher Test")
        config.set_value("user", "email", "git-publisher@example.com")


def test_git_publisher_commits_and_pushes_action_and_all_changes(tmp_path):
    user_path = tmp_path / "alice-social"
    user_repo = Repo.init(user_path)
    user_repo.git.checkout("-b", "main")
    _configure(user_repo)
    (user_path / "README.md").write_text("test", encoding="utf-8")
    user_repo.git.add(A=True)
    user_repo.index.commit("Initialize user repository")

    origin_path = tmp_path / "origin.git"
    Repo.init(origin_path, bare=True)
    user_repo.create_remote("origin", str(origin_path))
    user_repo.git.push("--set-upstream", "origin", "main")

    publisher = GitPublisher(str(user_path))
    action_path = user_path / "social" / "actions" / "post-001.json"
    action_path.parent.mkdir(parents=True)
    action_path.write_text('{"id": "post-001"}', encoding="utf-8")
    publisher.publish(str(action_path), "Add post-001")

    assert Repo(origin_path).git.show("main:social/actions/post-001.json") == (
        '{"id": "post-001"}'
    )

    extra_path = user_path / "social" / "profile.json"
    extra_path.write_text('{"handle": "alice.social"}', encoding="utf-8")
    publisher.publishAll("Publish all local changes")

    remote = Repo(origin_path)
    assert remote.git.show("main:social/profile.json") == (
        '{"handle": "alice.social"}'
    )


def test_git_publisher_initializes_repo_when_git_directory_is_missing(tmp_path):
    repo_path = tmp_path / "new-user"

    publisher = GitPublisher(str(repo_path))

    assert (repo_path / ".git").is_dir()
    assert publisher.repo.working_tree_dir == str(repo_path)


def test_git_publisher_reports_push_failures_but_keeps_local_commits(tmp_path, capsys):
    repo_path = tmp_path / "local-only"
    repo = Repo.init(repo_path)
    repo.git.checkout("-b", "main")
    _configure(repo)
    tracked_path = repo_path / "README.md"
    tracked_path.write_text("initial", encoding="utf-8")
    repo.git.add(A=True)
    repo.index.commit("Initialize")
    publisher = GitPublisher(str(repo_path))

    tracked_path.write_text("updated", encoding="utf-8")
    publisher.publish(str(tracked_path), "Update file")
    (repo_path / "profile.json").write_text("{}", encoding="utf-8")
    publisher.publishAll("Publish all")

    assert "git push failed" in capsys.readouterr().out
    assert repo.head.commit.message.strip() == "Publish all"
