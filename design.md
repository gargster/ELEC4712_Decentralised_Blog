# Design Document
The following document specifies the architecture and workflows of the proposed Git-based static-hostable social protocol. It builds ontop of the design_principles.md by translating principles into concrete components, data structures and processes. This ensures that the design is grounded in insights from surveyed protocols and has notes on implementation feasilibility and areas of code reuse.

## Layered Architecture
These are the layers of the design arranged in concise bullet points which indicate the natural implementation sequence, with must haves down to advanced features.
- Core Layer (must-have): Identity, Social Actions, Replication, Storage Format
- Extension Layer (optional improvements): Discovery, Feed Indexing, Media Handling
- Redesigned Layer (advanced features): Moderation, Confidentialiy, Threading

## Core Components
### Identity
Design Principle:
Each user has a permanent cryptographic identity that is portable across hosts.
Why portable?
- The identity is defined by a public key
- This key does not depend on any server or provider
- As long as the public key stays the same, the user's idenity remains valid regardless if they move their repository to GitHub, GitLab or static host.
Human-readable handles:
- To make identity easier to use, a hanle (like bharat.social) is mapped to the public key
- This mapping is stored in profile.json.
Client Responsibilities (step-by-step):
1. When a new account is created, the client generates an Ed25519 key pair (public/private)
2. The public key is written into /social/profile.json
3. The private key is stored securely by the client 
4. Whenever a post, reply, follow, or moderation list is created, the client signs the JSON object using the private key.
5. Followers verify signatures using the public key in profile.json
Survey Source:
Inspired by Nostr (portable key identity) and AT Protocol (DNS-mapped handles)
Data Structure (profile.json schema):
{
  "publicKey": "ed25519:abc123...",
  "handle": "bharat.social",
  "displayName": "Bharat",
  "bio": "Student at USYD",
  "created": "2026-06-28T19:57:00Z"
}
When signing is needed:
- Every time the client creates a new JSON object (post, reply, like, follow, blocklist)
- The client automatically attaches a signature field to prove authencity.

### Social Actions
Design Principle:
All user activities (Social actions) are represented as typed JSON objects. This makes them predictable, portable, and easy for clients to process.
Action Types (what they represent)
1. Post -> a new message or article authored by the user
2. Reply -> a response to an existing post, linked via inReplyTo
3. Like -> an edorsement of an existing post, linked via target
4. Follow -> a request to subscribe to another user's feed, linked via target
Why structured actions matter:
- ActivityPub showed that a fixed vocabulary (Create, Like, Follow) makes feeds interoperable.
- Nostr used event kinds to simplify client logic
- sAT stored acions as JSON objects, proving that they are easy to replicate and extend
- This ensures that every action has a clear schema and can be cryptographically verified.
Client Responsibilities (step-by-step):
1. When a user performs an action, the client creates a JSON object with the required fields
2. The client signs the JSON using the private key -> adds a signature field
3. The client saves the file in /social/actions/<id>.json
4. The client commits and pushes the file to the Git repository
5. Follower's client fetch new commits and verify signatures using the author's public key.
Survey Source:
Inspired by ActivtiyPub (typed activities), Nostr (event kinds), and sAT (JSON objects)
JSON Schemas for Each Action:
Post
{
  "id": "post-001",
  "type": "post",
  "author": "ed25519:abc123...",
  "content": "Hello world!",
  "created": "2026-06-28T20:05:00Z",
  "signature": "base64sig..."
}
Reply
{
  "id": "post-002",
  "type": "reply",
  "author": "ed25519:abc123...",
  "content": "Replying to post-001",
  "inReplyTo": "post-001",
  "created": "2026-06-28T20:06:00Z",
  "signature": "base64sig..."
}
Like
{
  "id": "like-001",
  "type": "like",
  "author": "ed25519:abc123...",
  "target": "post-001",
  "created": "2026-06-28T20:07:00Z",
  "signature": "base64sig..."
}
Follow
{
  "id": "follow-001",
  "type": "follow",
  "author": "ed25519:abc123...",
  "target": "ed25519:def456...",
  "created": "2026-06-28T20:08:00Z",
  "signature": "base64sig..."
}
When signing is needed:
- Every time a new action (post, reply, like, follow) is created
- The client automatically signs the JSON before saving
- Followers verify the signature using the public key in profile.json
Implementation Note:
Crypto libraries (e.g libsodium, tweetnacl) provide ready-made functions:
- sign(message, privateKey) -> client produces signature
- verify(message, signature, publickey) -> follower's client check authencity
- Thus ensuring only the true author can create valid actions and anyone can verify them.

### Replication
Design Principle:
Replication is pull-based and incremental. Followers fetch only new commits since their last synchronisation, instead of dowloading eveything again.

Why pull-based replication matters:
- Push models (like ActivityPub) overload servers because they must deliver every post to every follower
- Git's pull model (used in GitSocial, Social4Git, Gittweets) is efficient: authors push once, followers fetch when they want.
- Thus the identity is portable and hosting is flexible as anyone can host their repo, and followers can synchronise at their own pace.

Client Responsibilities (step-by-step)
1. Author's client:
- Commits new JSON files (posts, replies, likes, follows) into /social/actions/
- Pushes repo to Git host (GitHub, GitLab, or static host)
2. Follower's client (periodic fetch):
- Runs git fetch at a chosen interval (e.g. every few minutes, or when the user opens the app).
- The interval can be configured - some clients may fetch every 5 minutes, others only when the user refreshes
3. Incremental sync:
- Git automatically compares the local commit group graph with the remote 
- Only new commits (those not already in the local repo) are downloaded
- This avoids re-downloading old posts
4. Parsing new commits:
- For each new commit, the client checks which files were added in /social/actions/
- It opens each new JSON file and reads the actio object
5. Signature verification:
- The client verifies each acttion's signature using the author's public key from profile.json
- If valid, the action is accepts; if invalid, it is ignored
6. Feed update:
- The client inserts the new action into the local feed database (could be a simple JSON file, SQLite, or just cached in memory)
- Posts are displayed in chronological order
- Replies are linked to their parent via inReplyTo
- Likes and follows are shown as metadata on the target post or profile

Data Structures in Replication
Commit graph (Git DAG):
commit abc123
  /social/actions/post-001.json
commit def456
  /social/actions/post-002.json
commit ghi789
  /social/actions/reply-001.json
Action JSON (example post):
{
  "id": "post-001",
  "type": "post",
  "author": "ed25519:abc123...",
  "content": "Hello world!",
  "created": "2026-06-28T20:05:00Z",
  "signature": "base64sig..."
}
When signing is needed
- Signing happens at the action level: every JSON file is signed by the author's client before commit
- Replications itself doesn't require signing - Git ensures commit integrity
- Followers verify signatures inside each JSON file after replication

Implementation Note
- Use GitPython (Python) or isomorphic-git (JavaScript) to automate fetch and parse.
- Use cryptography libaries for signature verification 
Typical workflow:
- git fetch origin -> get new commits
- Parse /social/actions/*.json
- Run verify(message, signature, publicKey) for each action
- Update feed database with verified actions



