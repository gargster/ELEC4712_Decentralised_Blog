# Git-Native Decentralised Social Protocol

This repository contains a Python command-line prototype of a Git-native
decentralised social protocol. Users publish signed social actions in their
own Git repositories. Clients follow repositories, replicate actions, verify
action signatures before accepting them locally, and construct a feed from
accepted actions.

The prototype supports profiles, posts, replies, likes, follows, publishing,
replication, and feed display. Git is used for repository storage and
distribution; the client handles protocol operations.

## Project documentation

- [Latest design](./latest_design.md) describes the current protocol model and
  workflows.
- [Alternative protocols](./alternatives.md) compares related decentralised
  social systems.
- [Archived design notes](./docs/archive/) contains earlier design,
  principles, and requirements documents retained for reference. These files
  are historical and may not describe the current prototype.

## Prerequisites

- Python 3
- Git, available on `PATH`
- Access to the configured canonical and social-directory Git repositories
  for account creation and publishing

The client uses GitPython and PyNaCl. From the repository root, install them
with:

```powershell
python -m pip install GitPython PyNaCl
```

## Run the client

From the repository root:

```powershell
cd client
python app.py
```

The command prints available operations. Example commands:

```powershell
python app.py profile create --handle alice.social --name Alice --bio "Hello"
python app.py post "Hello, social network"
python app.py follow bob.social https://github.com/bob/bob-social.git
python app.py replicate
python app.py feed
python app.py feed --followers-only
python app.py publish --url https://github.com/alice/alice-social.git
python app.py publish-site
```

Replies and likes require a target handle and action ID:

```powershell
python app.py reply bob.social post-bob.social-001 "I agree"
python app.py like bob.social post-bob.social-001
```

Creating a regular account clones the configured canonical repository
template. Account creation generates key material and a user repository, but
the client selects its active account through `client/identity.json`. To use a
new account, set `activeIdentity` to the handle's local identity name and
`repoPath` to its repository directory. For example, for `alice.social`:

```json
{
  "activeIdentity": "alice",
  "repoPath": "alice-social"
}
```

Keep the private key in the client state directory; never publish it or
include it in a user repository. Publishing pushes the selected user's
repository and registers its handle in the configured social directory.
Account creation and publishing depend on access to those repositories.

Each social-directory entry records the handle's repository URL and public
key. Following a user and resolving display names checks the signed profile
against both values. Publishing refuses to replace a key already registered
for a handle; legitimate key changes need a separate recovery process. This
helps detect a repository recreated with a different key, but means users
trust the directory maintainer for handle-to-key registration. Existing
entries need a verified key added by the maintainer before they can be followed
or updated. After `publish-site` publishes a user's site, it adds that site's
GitHub Pages URL to the directory entry so the handle can link to it. Accounts
without a published site, such as the canonical template repository, have no
site link.

## Maintaining the canonical template

Normal account creation clones the canonical repository configured in
`client/src/config.py`. To maintain or customize the shared site template,
clone that canonical repository, edit the files under `site-template/`, then
commit and push the changes to its `main` branch. New accounts receive the
template version in the canonical repository when they are created.

`publish-site` reads the template from the project's local
`canonical-social/site-template/` checkout. Update that checkout from the
canonical repository when you want site publishing to use the latest
template. Existing user repositories do not need to be changed for this
publisher-side template update.

## Publish a GitHub Pages site

The protocol data and the website are published to separate branches of the
user's GitHub repository:

- `main` contains the signed profile and social actions.
- `gh-pages` contains the static site files and generated `feed.json`.

After creating and publishing the user repository, enable GitHub Pages once:

1. Open the user repository's **Settings → Pages**.
2. Under the build and deployment source, choose **Deploy from a branch**.
3. Select branch **`gh-pages`** and folder **`/ (root)`**, then save.

To publish or refresh the website, select the intended active identity in
`client/identity.json`, make sure its repository has no uncommitted changes,
and run this from the `client` directory:

```powershell
python app.py publish-site
```

The command prepares the site as follows:

1. Reads and verifies the selected user's `social/profile.json`.
2. Reads JSON files in that repository's local `social/actions/` directory
   and includes only actions with valid signatures. This includes actions
   already replicated into the repository; the command does not run
   replication itself.
3. Builds `feed.json` with the verified profile, accepted actions, and a
   public-key-to-display-name map. For author names, it reads the public
   social directory and verifies profiles fetched from listed GitHub
   repositories. If a profile cannot be found or verified, the site displays
   the author's public key instead.
4. Fetches the user's GitHub repository, creates `gh-pages` if needed (or
   updates it from the remote branch), copies the site template and generated
   `feed.json` to that branch, commits the result, and pushes `gh-pages`.
5. GitHub Pages serves the contents of `gh-pages` at the repository's Pages
   URL.

Publishing an action to `main` does **not** update the website automatically.
After creating new actions or replicating actions from other users, run
`publish-site` again to regenerate `feed.json` and push the updated site.

## Repository layout

```text
client/                 Python command-line client and local identity state
*-social/               User repositories created while running the client
latest_design.md        Current protocol design and workflows
alternatives.md         Comparison of related protocols
docs/archive/           Earlier design notes retained for reference
```

User repositories, local state, and cloned discovery data are runtime data;
they are not part of the source documentation.

## Tests

From the repository root:

```powershell
cd client
python -m pytest
```
