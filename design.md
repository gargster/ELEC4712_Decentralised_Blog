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

### Follow List 
Design Principle:
Each user mantains a local list of account they follow. This defines the scope of replication and feed construction.
Why it matters:
- Nostr only tracks "who you follow" (no server-side follower list)
- GitSocial introduced follow lists to make feed generation scalable
- Without a follow list, replication would mean fetching everyone's repos - impossible at scale
Client Responsibilities (step-by-step)
1. User decides to follow someone
- Provides a handle (e.g. alice.social)
2. Client fetches target's profile.json
- Reads publicKey and repoURL
- Verifies signature to ensure authencity 
3. Client updates local following.json
- Adds entry with handle, public key, repo URL, and timestamp
4. Client starts replication
- Uses repo URL from following.json
- Runs git fetch periodically to sync new actions 
Data Structure (following.json schema)
{
  "following": [
    {
      "handle": "alice.social",
      "publicKey": "ed25519:def456...",
      "repoURL": "https://gitlab.com/alice/social.git",
      "added": "2026-06-30T17:46:00Z"
    },
    {
      "handle": "bharat.social",
      "publicKey": "ed25519:abc123...",
      "repoURL": "https://github.com/bharat/social.git",
      "added": "2026-06-30T17:45:00Z"
    }
  ]
}
When signing is needed
- profile.json -> signed by the author when published
- following.json -> local config, not signed (as it is private to the client)

Implementation Notes
- Storage: following.json is kept in the client's local repor or app data
- Verification: profile.json signatues checked with crypto libraries
- Replication: GitPython/isomorphic git fetch repos listed in following.json

## Extension 
### Discovery 
Design Principle:
Discovery maps a human-readable handle (like bharat.social) to the actual Git repository URL and public key. It works at two levels:
- Per-user: each account publishes its own profile.json
- Global directory: a static discovery.json that is automatically updated when new accounts are created.

Why it matters:
- Public keys are portable but not user-friendly
- Handles make identity easier to share
- Discovery acts as the bridge: handle -> profile.json -> repo URL + public key
Exisisting protocols showed gaps:
- ActivityPub -> WebFinger (server-based)
- AT Protocol -> DIDs + DNS mapping (infrastructure-heavy)
- Nostr -> no built-in discovery (relays only)
- Git prototypes -> no discovery, you had to know repo URLs
The surveryed protocols flagged the gap of: no decentralised static-hostable discovery layer.
Automatic directory publishing fills that gap without servers: every client contributes its handle to a shared static file.

Client Responsibilties (Step-by-step)
1. Account creation (author's client)
- When a new account is created, the client automatically generates profile.json
- This file contains: public key, handle, repo URL, display name, bio
- The client signs profile.json with the private key
- The user uploads profile.json to a well-known location:
  - Example: https://bharat.social/profile.json
  - If hosted on GitHub Pages: https://bharat.github.io/social/profile.json
2. Automatic directory update:
- At account creation, the client also appends the new handle + profile URL to a shared directory.json
- This directory is hosted on a static site (e.g. GitHub Pages)
- Example: https://social.example.org/directory.json
3. Follower browsing:
- User opens the directory (acting as a "yellow pages" of accounts)
- Finds a handle they want to follow (e.g. alice.social)
4. Client fetches profile.json:
- Requests https://alice.social/profile.json
- Reads repoURL + publicKey
- Verifies signature
5. Client updates local following.json:
- Adds entry with handle, repo URL, public key, and timestamp
6. Replication begins:
- Client uses repoURL from following.json
- Runs git fetch to sync posts from that repo

Data Structures
profile.json (per user, authoritative)
{
  "publicKey": "ed25519:abc123...",
  "handle": "bharat.social",
  "repoURL": "https://github.com/bharat/social.git",
  "displayName": "Bharat",
  "bio": "Student at USYD",
  "created": "2026-06-28T19:57:00Z",
  "signature": "base64sig..."
}
directory.json (auto-updated global index)
{
  "directory": [
    {
      "handle": "bharat.social",
      "profileURL": "https://bharat.social/profile.json"
    },
    {
      "handle": "alice.social",
      "profileURL": "https://alice.social/profile.json"
    }
  ]
}
following.json (local file mantained by the client)
{
  "following": [
    {
      "handle": "alice.social",
      "publicKey": "ed25519:def456...",
      "repoURL": "https://gitlab.com/alice/social.git",
      "added": "2026-06-30T17:46:00Z"
    }
  ]
}
When signing is needed
- profile.json -> signed by the author when published
- directory.json -> auto-updated, unsigned (just an index)
- following.json -> local config, not signed (private to the client)
Implementation Note
- Publishing: Client generates and uploads profile.json automatically during account creation 
- Directory: Clients automatically append their handle + profile URL to a shared directory.json
- Fetching: Clients use HTTP GET to retrieve either directory.json (to browse) or profile.json (to follow)
- Verification: Use crypto libraries to verify profile.json signature
- Storage: Append entry to following.json
- Replication: GitPython/isomorphic git fetch repos listed in following.json

### Feed Indexing
Design Principle:
Efficient feed rendering requires an index of recent posts. Instead of scanning all files in /social/actions/, clients can read a lightweight index.json to quickly locate the latest posts.
Why it matters:
- As repositories grow, scanning every file in /social/actions/ becomes slow 
- An index speeds up synchronisation by pointing directly to recent posts
- Keeps replication efficient while mantaining portability
Inspiration from surveyed protocols:
- Git-as-Transport -> proposed indexes to avoiding scanning the entire repo history. This influenced the use of index.json as lightweight pointer to recent actions
- ActivityPub -> uses inbox/outbox collections to quickly access recent posts without crawling all objects, we mirror this efficieny in Git-native way
Git prototype lacked a feed index, forcing clients to scan whole repository. Feed Indexing fills this gap.

Client Responsibilities (step-by-step)
Author's client (posting):
1. Create new action file:
- Generates a JSON file (post, reply, like, follow) inside /social/actions/
- Each file is signed with the author's private key
2. Update index.json:
- Adds the new post ID to the latestPosts array
- Refreshes the updated timestamp
- Keeps only a limited window of recent posts (e.g. last 50 IDs) for efficiency
3. 
Commit and push:
- Commits bot the new action file and the updated index.json
- Pushes to the Git host
Follower's client (fetching):
1. Runs git fetch:
- Synchronises new commits from each followed repo listed in following.json
- This updates the local copy of /social/actions/ and retrieves the latest index.json
2. Read index.json:
- Opens the fetched index.json from each followed repo
- Quickly identifies the latest post IDs without scanning all files
3. Compare with local feed database:
- Checks which post IDs in the remote index.json are missing from the local feed database
- Note: comparison is against the local feed database, not against your own index.json (which only tracks your own posts)
4. Fetch missing posts:
- Retrieves only the missing JSON files from /social/actions/
- Avoids re-scanning or re-downloading old posts
5. Verify signatures:
- Uses the author's public key (from their profile.json) to verify each new action file
- Accepts valid posts and ignores invalid ones
6. Insert into feed database:
- Adds verified posts to the local feed database (JSON file, SQLite, or memory cache)
- Updates chronological ordering
- Links replies to parent posts via inReplyTo
- Displays likes/follows as metadata
How /social/actions/ fits in
- /social/action is the folder in each repo where all signed social actions are stored
- After replication, your local copy of /social/actions contains all posts from followers accumulated since your last sync
- Git ensures incremental sync: only new commits are fetched
- Feed Indexing (index.json) avoids rescanning the entire /social/actions/ directory by pointing directly to the latest posts.

Data Structure 
index.json (per repo, lightweight index)
{
  "latestPosts": ["post-001", "post-002", "post-003"],
  "updated": "2026-06-28T15:24:00Z"
}
Example worflow with index.json:
- Repo has 10,000 posts in /social/actions/
- index.json lists only the last 50 post IDs
- Follower's client fetches those 50, verfies signatures, and updates feed
- No need to rescan all 10,000 files
Why signing is needed
- Actions files -> signed by the author
- index.json -> not signed (convenience file)
- Followers always verify signatures inside the actual action JSON files
Implementation Note
- Publishing: Author's client updates index.json automatically whenever a new post is created
- Fetching: Follower's client reads index.json first, then fetches missing posts
- Verification: Signatures are checked on the post JSON files, not index.json
- Storage: Feed database (local JSON, SQLite, or memory cache) is updated with verified posts
- Efficiency: Index avoids scanning thousands of files, making sync faster

### Media Handling 
Design Principle:
Posts can reference media files (images, audio, video). Large binary files are handled differently than JSON actions by handling via Git LFS or external storage to keep repositories efficient.

Why it matters:
- Social feeds often include rich media
- Git alone doesn't handle large binary files well - repos can bloat quickly
- Media must be referenced cleanly in posts and stored efficiently
Inspired by:
- ActivityPub -> servers host media alongside posts
- Git prototypes -> limited or no media support
- AT Protocol -> supports blob storage references
Gap identified: Git-based social prototypes lacked robust media handling. Adding Git LFS or external storage fills this gap

What is Git LFS?
- Git LFS (Large File Storage) is an extension to Git for handling large binary files 
- Instead of storing the full binary in the repository history, Git LFS stores a small pointer file in the repo
The pointer file contains:
- version -> the LFS spec version (e.g. https://git-lfs.github.com/spec/v1)
- oid sha256 -> a cryptographic hash of the actual binary file
- size -> the size of the binary file in bytes
- The actual binary file (image, video, audio) is stored separately in LFS storage
- When followers fetch, Git LFS automatically downloads the real binary behind the pointer

Example Pointer File (Git LFS)
When the client commits a large media file, Git LFS generates a pointer file like this:

version https://git-lfs.github.com/spec/v1
oid sha256:3b2f1c9d4a7e8f0a9c8e2d6f1234567890abcdef1234567890abcdef12345678
size 2456789
version -> fixed string from the Git LFS specification
oid sha256 -> hash of the actual binary media file (ensures integrity)
size -> exact size of the binary file file in bytes
This pointer file is what gets committed to the repo. The binary itself is stored in LFS storage

Client Responsibilities (step-by-step)
Author's client (posting with media)
1. Create media file:
- User selects an image, audio, or video
- Client saves it in /social/media/
- If the file is large, Git LFS automatically generates a pointer file with version, hash, and size
2. Reference in post JSON:
- Post JSON includes a media field listing file paths
- Example: "media": ["media/photo1.jpg"]
- If Git LFS is used, the path points to the pointer file, but Git LFS resolves it to the actual binary 
3. Commit and push:
- Commits both the post JSON in /social/actions/ and the media file (or LFS pointer)
- Pushes to Git host 
4. Update index.json:
- Adds the new post ID to index.json
- Ensures followers can quickly discover the post and its media reference
Follower's client (fetching media)
1. Run git fetch:
- Synchronises new commits from each followed repository
- Retrieves new post JSON files and any referenced media files (or LFS pointers)
2. Read post JSON:
- Identifies media field entries
- Determines which media files need to be downloaded
3. Dowload media:
- If small files: fetched directly from /social/media/
- If large files: Git LFS automatically downloads the actual binary where the pointer file is encountered
4. Verify post JSON:
- Checks signature of the post JSON
- Ensures media references are valid 
5. Insert into feed database:
- Adds post content and media references
- Displays media inline with the post in the feed

Data Structures 
Post JSON with media references
{
  "id": "post-003",
  "type": "post",
  "author": "ed25519:abc123...",
  "content": "Photo from trip",
  "media": ["media/photo1.jpg"],
  "created": "2026-06-28T20:15:00Z",
  "signature": "base64sig..."
}
Repo layout example
/social/actions/post-003.json
/social/media/photo1.jpg   (small file)
/social/media/photo2.lfs   (pointer file for large file)
/social/index.json

When signing is needed
- Post JSON -> signed by the author
- Media files -> not individually signed (integrity comes from Git commit or LFS pointer)
- Follower verify the post JSON signature; media integrity is ensures by Git/LFS.

## Redeisigned Components
### Moderation
Design Principle:
Moderation is decentralised and portable. Each user can publish signed blocklists and trust lists that define who they block or trust. These lists are crytographically verifiable and can be shared across repositories

Why it matters:
- Moderation is essential for safety and trust in social systems
- Surveyed protocols showed gaps:
  - 




