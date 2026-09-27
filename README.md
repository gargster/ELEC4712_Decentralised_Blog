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
