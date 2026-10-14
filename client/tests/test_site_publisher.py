import io
import json

from git import Repo
import pytest

from src.config import CANONICAL_REPO_NAME, DIRECTORY_JSON_URL
from src.identity.keypair import KeyPair
from src.identity.signer import Signer
from src.publishing import site_publisher
from src.publishing.publish_manager import PublishManager
from src.publishing.site_publisher import SitePublisher


def configure_repo(repo):
    with repo.config_writer() as config:
        config.set_value("user", "name", "Site Publisher Test")
        config.set_value("user", "email", "site-publisher-test@example.com")


def sign_object(data, private_key):
    data["signature"] = Signer(private_key).sign_json(data)
    return data


def test_publish_site_creates_branch_with_verified_feed(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    user_repo_path = project_root / "alice-social"
    template_path = project_root / CANONICAL_REPO_NAME / "site-template"
    bare_origin_path = tmp_path / "alice-origin.git"
    template_path.mkdir(parents=True)
    user_repo_path.mkdir(parents=True)

    (template_path / "index.html").write_text(
        '<script src="./app.js" defer></script>', encoding="utf-8"
    )
    (template_path / "style.css").write_text("body {}", encoding="utf-8")
    (template_path / "app.js").write_text(
        'fetch("./feed.json");', encoding="utf-8"
    )

    keypair = KeyPair()
    public_key = keypair.public_key()
    profile = sign_object(
        {
            "publicKey": public_key,
            "handle": "alice.social",
            "repoURL": "https://github.com/example/alice-social.git",
            "displayName": "Alice",
            "bio": "Test profile",
            "created": "2026-09-30T00:00:00Z",
        },
        keypair.private_key(),
    )

    actions_path = user_repo_path / "social" / "actions"
    actions_path.mkdir(parents=True)
    valid_action = sign_object(
        {
            "id": "post-alice.social-001",
            "type": "post",
            "author": public_key,
            "created": "2026-09-30T00:01:00Z",
            "content": "Signed and accepted",
        },
        keypair.private_key(),
    )
    invalid_action = dict(valid_action)
    invalid_action["id"] = "post-alice.social-invalid"
    invalid_action["content"] = "Tampered content"

    (user_repo_path / "social" / "profile.json").write_text(
        json.dumps(profile), encoding="utf-8"
    )
    (actions_path / "valid.json").write_text(
        json.dumps(valid_action), encoding="utf-8"
    )
    (actions_path / "invalid.json").write_text(
        json.dumps(invalid_action), encoding="utf-8"
    )

    Repo.init(bare_origin_path, bare=True)
    repo = Repo.init(user_repo_path)
    repo.git.checkout("-b", "main")
    configure_repo(repo)
    repo.git.add(A=True)
    repo.index.commit("Initialize user repository")
    repo.create_remote("origin", str(bare_origin_path))
    repo.git.push("--set-upstream", "origin", "main")
    (bare_origin_path / "HEAD").write_text(
        "ref: refs/heads/main\n", encoding="utf-8"
    )

    monkeypatch.setattr(
        site_publisher.urllib.request,
        "urlopen",
        lambda url, timeout: io.BytesIO(b"{}"),
    )
    registered_sites = []
    monkeypatch.setattr(
        site_publisher.PublishManager,
        "update_site_url",
        lambda self, handle, repo_url, key, site_url: registered_sites.append(
            (handle, repo_url, key, site_url)
        ),
    )
    SitePublisher(str(project_root), str(user_repo_path)).publish()

    assert registered_sites == [
        (
            "alice.social",
            "https://github.com/example/alice-social.git",
            public_key,
            "https://example.github.io/alice-social/",
        )
    ]
    assert repo.active_branch.name == "main"
    assert repo.git.show("gh-pages:index.html") == (
        '<script src="./app.js" defer></script>'
    )
    feed = json.loads(repo.git.show("gh-pages:feed.json"))
    assert feed["profile"]["handle"] == "alice.social"
    assert feed["profiles"][public_key] == "Alice"
    assert [action["id"] for action in feed["actions"]] == [
        "post-alice.social-001"
    ]
    assert repo.git.show("origin/gh-pages:feed.json") == repo.git.show(
        "gh-pages:feed.json"
    )

    second_action = sign_object(
        {
            "id": "post-alice.social-002",
            "type": "post",
            "author": public_key,
            "created": "2026-09-30T00:02:00Z",
            "content": "A later accepted post",
        },
        keypair.private_key(),
    )
    (actions_path / "second.json").write_text(
        json.dumps(second_action), encoding="utf-8"
    )
    repo.git.add("social/actions/second.json")
    repo.index.commit("Add second post")

    SitePublisher(str(project_root), str(user_repo_path)).publish()

    updated_feed = json.loads(repo.git.show("gh-pages:feed.json"))
    assert sorted(action["id"] for action in updated_feed["actions"]) == [
        "post-alice.social-001",
        "post-alice.social-002",
    ]
    assert repo.git.show("origin/gh-pages:feed.json") == repo.git.show(
        "gh-pages:feed.json"
    )
    assert repo.active_branch.name == "main"
    assert len(registered_sites) == 2


def test_profile_names_are_discovered_from_verified_directory_profiles(
    tmp_path, monkeypatch
):
    user_repo_path = tmp_path / "alice-social"
    user_repo_path.mkdir()
    Repo.init(user_repo_path)

    own_keypair = KeyPair()
    own_profile = {
        "publicKey": own_keypair.public_key(),
        "handle": "alice.social",
        "displayName": "Alice",
    }

    canonical_keypair = KeyPair()
    canonical_profile = sign_object(
        {
            "publicKey": canonical_keypair.public_key(),
            "handle": "canonical.social",
            "repoURL": "https://github.com/example/canonical-social.git",
            "displayName": "Canonical",
            "bio": "Genesis",
            "created": "2026-09-30T00:00:00Z",
        },
        canonical_keypair.private_key(),
    )
    directory = {
        "canonical.social": {
            "repoURL": "https://github.com/example/canonical-social.git",
            "publicKey": canonical_profile["publicKey"],
        }
    }
    requested_urls = []

    def open_url(url, timeout):
        requested_urls.append(url)
        payload = (
            directory
            if url == DIRECTORY_JSON_URL
            else canonical_profile
        )
        return io.BytesIO(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr(site_publisher.urllib.request, "urlopen", open_url)

    publisher = SitePublisher(str(tmp_path), str(user_repo_path))
    profiles = publisher._load_profile_names(own_profile)

    assert profiles[own_profile["publicKey"]] == "Alice"
    assert profiles[canonical_profile["publicKey"]] == "Canonical"
    assert requested_urls == [
        DIRECTORY_JSON_URL,
        "https://raw.githubusercontent.com/example/canonical-social/main/"
        "social/profile.json",
    ]


def test_profile_name_is_not_used_when_directory_key_does_not_match(
    tmp_path, monkeypatch
):
    user_repo_path = tmp_path / "alice-social"
    user_repo_path.mkdir()
    Repo.init(user_repo_path)

    own_keypair = KeyPair()
    own_profile = {
        "publicKey": own_keypair.public_key(),
        "handle": "alice.social",
        "displayName": "Alice",
    }
    canonical_keypair = KeyPair()
    canonical_profile = sign_object(
        {
            "publicKey": canonical_keypair.public_key(),
            "handle": "canonical.social",
            "repoURL": "https://github.com/example/canonical-social.git",
            "displayName": "Canonical",
            "bio": "Genesis",
            "created": "2026-09-30T00:00:00Z",
        },
        canonical_keypair.private_key(),
    )
    directory = {
        "canonical.social": {
            "repoURL": "https://github.com/example/canonical-social.git",
            "publicKey": "ed25519:registered-different-key",
        }
    }

    def open_url(url, timeout):
        payload = directory if url == DIRECTORY_JSON_URL else canonical_profile
        return io.BytesIO(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr(site_publisher.urllib.request, "urlopen", open_url)

    publisher = SitePublisher(str(tmp_path), str(user_repo_path))
    profiles = publisher._load_profile_names(own_profile)

    assert profiles == {own_profile["publicKey"]: "Alice"}


def test_github_pages_url_for_project_and_user_sites():
    assert PublishManager.github_pages_url(
        "https://github.com/alice/alice-social.git"
    ) == "https://alice.github.io/alice-social/"
    assert PublishManager.github_pages_url(
        "https://github.com/alice/alice.github.io"
    ) == "https://alice.github.io/"
    assert PublishManager.github_pages_url(
        "https://gitlab.com/alice/alice-social.git"
    ) is None


def test_site_publisher_rejects_missing_template_and_dirty_repository(tmp_path):
    repo_path = tmp_path / "alice-social"
    repo_path.mkdir()
    repo = Repo.init(repo_path)
    repo.git.checkout("-b", "main")
    configure_repo(repo)
    repo_path.joinpath("tracked.txt").write_text("tracked", encoding="utf-8")
    repo.git.add(A=True)
    repo.index.commit("Initialize")
    (repo_path / "untracked.txt").write_text("uncommitted", encoding="utf-8")

    publisher = SitePublisher(str(tmp_path), str(repo_path))
    with pytest.raises(FileNotFoundError, match="Site template not found"):
        publisher._validate_template()

    with pytest.raises(RuntimeError, match="local changes"):
        publisher._prepare_branch()


def test_site_publisher_validates_template_files_and_repository_setup(tmp_path):
    repo_path = tmp_path / "alice-social"
    repo_path.mkdir()
    repo = Repo.init(repo_path)
    repo.git.checkout("-b", "main")
    configure_repo(repo)
    (repo_path / "tracked.txt").write_text("tracked", encoding="utf-8")
    repo.git.add(A=True)
    repo.index.commit("Initialize")

    publisher = SitePublisher(str(tmp_path), str(repo_path))
    publisher.template_path = str(tmp_path / "template")
    (tmp_path / "template").mkdir()
    (tmp_path / "template" / "index.html").write_text("", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="app.js, style.css"):
        publisher._validate_template()

    with pytest.raises(RuntimeError, match="needs an origin remote"):
        publisher._prepare_branch()


def test_profile_url_rejects_unsupported_or_malformed_urls():
    for invalid_url in (
        None,
        "",
        "not a url",
        "http://github.com/alice/repo",
        "https://github.com/alice/repo/extra",
        "https://github.com/alice/repo?branch=main",
        "https://github.com/alice/repo#profile",
    ):
        assert SitePublisher._profile_url(invalid_url) is None


def test_directory_profile_discovery_skips_bad_entries_and_handles_unavailable_directory(
    tmp_path, monkeypatch, capsys
):
    repo_path = tmp_path / "alice-social"
    repo_path.mkdir()
    Repo.init(repo_path)
    publisher = SitePublisher(str(tmp_path), str(repo_path))
    own = {"publicKey": "alice-key", "handle": "alice.social"}

    monkeypatch.setattr(
        site_publisher.urllib.request,
        "urlopen",
        lambda url, timeout: io.BytesIO(
            json.dumps(
                {
                    "bad-entry": "not an object",
                    "no-repo": {"repoURL": "https://gitlab.com/a/b"},
                }
            ).encode("utf-8")
        ),
    )
    assert publisher._load_profile_names(own) == {"alice-key": "alice.social"}
    output = capsys.readouterr().out
    assert "Skipping invalid directory entry" in output
    assert "Could not locate a GitHub profile" in output

    monkeypatch.setattr(
        site_publisher.urllib.request,
        "urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("offline")),
    )
    assert publisher._load_profile_names(own) == {"alice-key": "alice.social"}
    assert "Could not load discovery directory" in capsys.readouterr().out
