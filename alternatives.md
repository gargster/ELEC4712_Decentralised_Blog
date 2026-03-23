# Alternative Decentralised Social Protocols
## ActivityPub
## Posting Workflow
```mermaid
sequenceDiagram
    participant Alice
    participant AliceClient as AliceClient
    participant AliceServer as AliceServer
    participant FollowerServers as FollowerServers
    participant FollowerClients as FollowerClients

    Alice->>AliceClient: Create Post
    AliceClient->>AliceClient: Construct Create activity (JSON-LD)
    AliceClient->>AliceServer: POST /outbox (Create activity)
    AliceServer->>AliceServer: Validate activity & store in Outbox
    AliceServer->>FollowerServers: POST /inbox (Create activity)
    FollowerServers->>FollowerServers: Validate signature & store
    FollowerServers->>FollowerClients: Notify clients
```
## Following Workflow
```mermaid
sequenceDiagram
    participant Alice
    participant AliceClient as AliceClient
    participant AliceServer as AliceServer
    participant BobServer as BobServer

    Alice->>AliceClient: Follow @bob@server
    AliceClient->>AliceClient: Construct Follow activity (JSON-LD)
    AliceClient->>AliceServer: POST /outbox (Follow activity)
    AliceServer->>BobServer: POST /inbox (Follow activity)
    BobServer->>BobServer: Validate request & update followers list
    BobServer->>AliceServer: POST /inbox (Accept activity)
    AliceServer->>AliceServer: Store Accept & mark Bob as followed
```
## Nostr
## Posting Workflow
```mermaid
sequenceDiagram
    participant Alice
    participant AliceClient as AliceClient
    participant Relays as Relays
    participant FollowerClients as FollowerClients

    Alice->>AliceClient: Create Note
    AliceClient->>AliceClient: Create event (kind 1) & sign with private key
    AliceClient->>Relays: EVENT message
    Relays->>Relays: Validate signature & store event
    Relays->>FollowerClients: Forward EVENT message
    FollowerClients->>FollowerClients: Receive event & update feed
```
## Following Workflow
```mermaid
sequenceDiagram
    participant Bob
    participant BobClient as BobClient
    participant Relays as Relays
    participant AliceClient as AliceClient

    Bob->>BobClient: Follow Alice
    BobClient->>BobClient: Create event (kind 3) & sign (update contact list)
    BobClient->>Relays: EVENT message
    Relays->>Relays: Validate signature & store event
    BobClient->>Relays: REQ (subscribe to Alice)
    Relays->>BobClient: Send past & stream future events
```
## Git Based Attempts
## social4git
## Posting Workflow
```mermaid
sequenceDiagram
    participant Alice
    participant AliceClient as AliceClient
    participant AlicePublicRepo as AlicePublicRepo
    participant FollowerClient as FollowerClient
    participant FollowerPrivateRepo as FollowerPrivateRepo

    Alice->>AliceClient: social4git post -m "Hello!"
    AliceClient->>AliceClient: Create post + metadata files
    AliceClient->>AliceClient: git add && git commit
    AliceClient->>AlicePublicRepo: git push

    FollowerClient->>AlicePublicRepo: git fetch
    FollowerClient->>FollowerClient: Extract post files
    FollowerClient->>FollowerClient: git add && git commit
    FollowerClient->>FollowerPrivateRepo: git push
```
## Following Workflow
```mermaid
sequenceDiagram
    participant Bob
    participant BobClient as BobClient
    participant BobPrivateRepo as BobPrivateRepo
    participant AlicePublicRepo as AlicePublicRepo

    Bob->>BobClient: social4git follow --handle <AliceRepoURL>
    BobClient->>BobClient: Add AliceRepoURL to following list
    BobClient->>BobClient: git add && git commit
    BobClient->>BobPrivateRepo: git push

    Bob->>BobClient: social4git sync
    BobClient->>AlicePublicRepo: git fetch
    BobClient->>BobClient: Extract Alice's posts
    BobClient->>BobClient: git add && git commit
    BobClient->>BobPrivateRepo: git push
```
