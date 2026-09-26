## Post

```mermaid
sequenceDiagram
    participant Author as Author User
    participant Client as Author Client
    participant Repo as Author Git Repository
    participant Follower as Follower Client

    Author->>Client: post "Hello world"

    Client->>Client: Create Post action
    Client->>Client: Set id, type, author, content, created
    Client->>Client: Sign action with author's private key

    Client->>Repo: Save signed action under social/actions/
    Client->>Repo: Commit action
    Client->>Repo: Push repository

    Note over Repo: Repository now contains a signed post action
    Note over Repo,Follower: Later, during replication

    Follower->>Repo: Fetch remote repository
    Repo-->>Follower: Return updated remote branch

    Follower->>Follower: Read candidate action from remote branch
    Follower->>Follower: Verify action signature using action.author
    Follower->>Follower: Accept valid action
    Follower->>Follower: Write valid action to local social/actions/

    Note over Follower: The feed later reads accepted local actions
```

## Like

```mermaid
sequenceDiagram
    participant Author as Author User
    participant Client as Author Client
    participant Repo as Author Git Repository
    participant Follower as Follower Client

    Author->>Client: like alice.social post-alice.social-001

    Client->>Client: Create Like action
    Client->>Client: Set id, type, author, target, targetHandle
    Client->>Client: Sign action with author's private key

    Client->>Repo: Save signed action under social/actions/
    Client->>Repo: Commit action
    Client->>Repo: Push repository

    Note over Repo: Repository now contains a signed like action
    Note over Repo,Follower: Later, during replication

    Follower->>Repo: Fetch remote repository
    Repo-->>Follower: Return updated remote branch

    Follower->>Follower: Read candidate like action
    Follower->>Follower: Verify action signature using action.author
    Follower->>Follower: Accept valid action
    Follower->>Follower: Write valid action to local social/actions/

    Follower->>Follower: Resolve target against local actions
    Follower->>Follower: Associate like with the referenced post
```

## Reply

```mermaid
sequenceDiagram
    participant Author as Author User
    participant Client as Author Client
    participant Repo as Author Git Repository
    participant Follower as Follower Client

    Author->>Client: reply alice.social post-alice.social-001 "I agree"

    Client->>Client: Create Reply action
    Client->>Client: Set id, type, author, content, created
    Client->>Client: Set inReplyTo and targetHandle
    Client->>Client: Sign action with author's private key

    Client->>Repo: Save signed action under social/actions/
    Client->>Repo: Commit action
    Client->>Repo: Push repository

    Note over Repo: Repository now contains a signed reply action
    Note over Repo,Follower: Later, during replication

    Follower->>Repo: Fetch remote repository
    Repo-->>Follower: Return updated remote branch

    Follower->>Follower: Read candidate reply action
    Follower->>Follower: Verify action signature using action.author
    Follower->>Follower: Accept valid action
    Follower->>Follower: Write valid action to local social/actions/

    Follower->>Follower: Resolve inReplyTo against local actions
    Follower->>Follower: Group reply under the referenced post
```

## Follow

```mermaid
sequenceDiagram
    participant User as Follower User
    participant Client as Follower Client
    participant Repo as Follower Repository
    participant Alice as Alice Repository

    User->>Client: follow alice.social repositoryURL

    Client->>Repo: Add Alice's repository as a Git remote

    Client->>Alice: Fetch Alice's repository
    Alice-->>Client: Return Alice's remote branch

    Client->>Client: Read social/profile.json from fetched branch
    Client->>Client: Verify Alice's profile signature
    Client->>Client: Extract Alice's public key

    Client->>Client: Create Follow action
    Client->>Client: Set target to Alice's public key
    Client->>Client: Sign action with follower's private key

    Client->>Repo: Save signed Follow action under social/actions/
    Client->>Repo: Commit Follow action
    Client->>Repo: Push repository

    Note over Repo,Alice: No Alice actions are copied during follow.
    Note over Client,Alice: Alice's actions are fetched and verified later
    Note over Client,Alice: through the replication workflow.
```

## Replication and Action Acceptance

The replication layer validates actions before accepting them into the local
action store. The feed operates above this layer by reading accepted local
actions, indexing their relationships, and rendering the result.

```mermaid
sequenceDiagram
    participant Client as Follower Client
    participant Remote as Followed Repository
    participant Local as Local Repository
    participant Feed as Feed Layer

    Client->>Remote: git fetch remote main
    Remote-->>Client: Return updated remote branch

    Client->>Client: Read remote social/profile.json
    Client->>Client: Verify remote profile signature

    loop For each action in remote social/actions/
        Client->>Client: Read candidate action
        Client->>Client: Verify action signature using action.author

        alt Signature is valid
            Client->>Local: Write action to local social/actions/
            Client->>Local: Commit verified action
        else Signature is invalid or action is malformed
            Client->>Client: Reject action
            Note over Client: Do not write action locally
        end
    end

    Client->>Local: Push replicated verified actions to origin

    Feed->>Local: Read local social/actions/
    Local-->>Feed: Return accepted actions
    Feed->>Feed: Index posts, likes, replies, and follows
    Feed->>Feed: Resolve local action references
    Feed-->>Client: Render feed
```

## Multi-hop Propagation

Actions are verified using the public key in each action's `author` field.
They are not required to match the profile key of the repository currently
relaying them. This allows valid signed actions to propagate through multiple
repositories.

```mermaid
sequenceDiagram
    participant Alice as Alice Client
    participant AliceRepo as Alice Repository
    participant Bob as Bob Client
    participant BobRepo as Bob Repository
    participant Carol as Carol Client
    participant CarolRepo as Carol Repository

    Alice->>Alice: Create and sign post
    Alice->>AliceRepo: Publish signed post

    Bob->>AliceRepo: Fetch Alice's repository
    AliceRepo-->>Bob: Return Alice's signed post
    Bob->>Bob: Verify post using action.author
    Bob->>BobRepo: Store verified post

    Carol->>BobRepo: Fetch Bob's repository
    BobRepo-->>Carol: Return Alice's signed post
    Carol->>Carol: Verify post using action.author
    Carol->>CarolRepo: Store verified post

    Note over Alice,Carol: Valid signed actions can propagate through multiple repositories
```

## Protocol Validation Summary

Each social action is signed by its author before being committed to the
author's Git repository. During replication, the receiving client verifies the
remote profile and then validates each candidate action using the public key
specified by the action's `author` field. Only valid actions are written to
the local `social/actions/` directory. Invalid or malformed actions are
rejected before local acceptance.

Because verification is based on the action's own author key rather than the
repository currently relaying the action, valid actions can propagate through
multiple repositories. The feed operates above this protocol layer by reading
accepted local actions, indexing posts, likes, replies, and follows, resolving
local references, and rendering the resulting feed.

The current prototype re-reads and verifies the available action files from
each remote on every replication run. This preserves the validation invariant
but can be optimized in future work by tracking the last processed Git commit
or action identifiers and processing only newly observed actions.
