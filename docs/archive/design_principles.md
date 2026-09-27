# Design Principles Derived from the Survey
This document summarises insights from the explored prototocols which can inform the design of the proposed Git-based, static-hostable protocol. Each principle is grounded in the functional requirements (requirements.md) and justified by the obervations from the protocols covered in alternatives.md.

## Reusable Elements
The following concepts have been shown to work well in existing protocols and can be adopted directly with minimal modification.
### Structured Social Actions (Activity Types / Event Kinds)
Design Principle: 
The protocol will represent social actions (e.g. "post", "reply", "follow", "like") using a small, predefined set of action types, each with a clearly defined structure.

Survey Evidence:
- ActivityPub shows how structured social activties provided a rich social vocabulary.
- Nostr similarly used different types for different social actions.
- sAT represents social actions using JSON objects.
This shows that mutliple well-established protocols agree on typed, structured action objects which contributes to interoperability and consistency in feed rendering.

Summary:
Thus, the protocol will define a standard set of action types, each with a corresponding structured representation, and clients will generate these objects automatically when users perform social actions.

### Cryptographic Identity (User-Owned Public Key)
Design Principle:
The protocol will use a public-key-based indentity model, where each user's identity is defined by an Ed25519 public key, optionally mapped to a human-readable handle (e.g. "Bharat.social") in a static profile file. The user's private key is responsible for signing social actions. 

Survey Evidence:
- Nostr shows portable identity is achievable through cryptographic keys.
- AT Protocol shows that human-readable user handles can be mapped to keys.
The only identity model which is portable across hosts is based on cryptographic keys and handles can be layered on top of key-based identity.

### Pull-Based, Incremental Replication 
Design Principle:
The protocol will use pull-based replication, where clients fetch only new social data since their last known state.

Survey Evidence:
- ActivityPub highlights the scalability issues in push-based fan-out.
- Git-as-Transport demonstrates inefficiency of full history transfers 
- Git-based prototypes (GitSocial, Social4Git, Gitweets) all rely on Git's pull model: posting = push commit, replication = fetch commits.
Using Git's existing pull model, where only new commits are transferred inherently supports incremental replication.

### Dedicated User Directory (Clear Separation of Social Data)
The protocol will store all social data inside a dedicated directory within the user's Git repository (e.g. /social/). This directory will have the user's action objects, identity information (e.g public key and user handle) and the static profile file.

Survey Evidence:
- sAT isolated all social data in a dedicated /satellite/ directory.
- Many Git-based prototypes (GitSocial, Social4Git, Gitweets) organise social data using a dedicated subdirectory, supporitng incremental replication.
Using a dedicated directory is common and effective across Git-based systems, but unlike prior prototypes where identity is bound to repo URL, we seaprate identity from hosting location so directory can be hosted on any Git provider or static host (provider agnostic).

### JSON as the Storage Format (Encoding Layer)
The protocol will use JSON as the storage and encoding format for all social data, including the structured representations of action types defined in 1.1, the static profile file, identity information, and supporing metadata.

Survey Evidence:
- Gitweets shows that commit messages are unsuitable for structured posts.
- Simiarly GitSocial shows the limitations of embedding posts inside commit messages.
- sAT and Git-as-Transport both store posts as JSON files, showing that JSON is a flexible and extendsible enciding format for social data.
These together indicate that JSON provides a consistent and extensible encoding layer which supports structured fields, media, references and any future extensions.

## Extendable Elements
The following concepts appear in existing protocols but require adaptation or additional design work before they can be incorporated into the proposed protocol.

### Decentralised Discovery
Design Principle:
The protocol may support decentralised discovery mechanisms which allow clients to locate user profiles and content across different hosting providers without relying on a central server.

Survey Evidence:
- ActivityPub introduces dicovery but is server-mediated via WebFinger making it unsuitable for static hosting. 
- AT Protocol uses a DID Service for a DNS-based global handle registry, which introduces centralisation.
- Nostr uses a less centralised method of dicovery using relay servers but this requires always-online infrastructure.
These established protocols show that dicovery is essential but is not compatible with static hosting currently and needs to be extended.

### Feed Indexing and Aggregation
Design Principle:
The protocol may include optional indexing mechanisms to help clients efficiently assemble feeds from multiple users, especially to deal with large repositories (scalability).

Survey Evidence:
- Git-as-Transport proposes index files which are mantained by servers to avoid scanning entire repository histories.
- sAT is more decentralised, using structured directories for posts, which are compatible with static hosting but inefficient for large-scale aggregation.
- ActivityPub uses inbox/outbox indexes, which rely on server-side processing.
These systems show that indexing can be used to effectively improve performance, but needs to be modified to be more appropriate for our system (e.g. static hosting with scalability).

### Content Addressing and Media Handling
Design Principle:
The prototocol may structure posts in a way which allows optional support for referencing or storing media files efficiently in a static hosting environment.

Survey Evidence:
- ActivityPub structures posts as JSON-LD objects but servers are responsible for identity, availability and storage, so richer content like images depends on servers.
- sAT Protocol storing posts as encrypted JSON files alreadys slows feed aggregation, so even heavier media would not be suitable.
- Git-based attempts have benefited from structured DAG replication, but no direct support for richer media (e.g image, video) as some stored directly as commit messages, others with headers. 
So, mechanisms like Git LFS (Large file Storage) could support richer content while being static hosting compatibl - but may not be available across providers. Thus showing how no solution is directly reusable and needs some extensions for our scenario.
## Rejected Elements
The following concepts appear in existing protocols but are totally incompatible with a Git-based, static-hostable design. Thus they are excluded from the proposed protocol.

### Push-Based Fan-Out
Design Principle:
The protocol will not use server-mediated push-fan-out, where each post is immediately pushed to all followers.
Survey Evidence:
- ActivityPub shows performance and scalability bottlenecks due to push-fanout, along with heavy infrastructure costs.
Thus push fan-out is rejected due it centralising discovery, scaling poorly and overall contradicted our static-pull orientated design.

### Inflexible Append-Only Log
Design Principle:
The protocol will not adopt a rigid append-only structure for its feed which would prevent history editing, branching, or merging. 
Survey Evidence:
- Secure Scuttlebutt (SSB) uses append-only logs which grow indefinitely and cannot be reorganised, unllike Git's DAG.
Thus due to the inefficiency of append-only logs at scale and lack of flesbility compared to Git's DAG model, it is rejected.

## Redesigned Elements
The following concepts appear in existing protocols but require significant modfication before they can be incorporatedd. Unlike Extendable Elements which could be adpated with minor additions.

### Moderation and Access Control
Design Principle:
The protocol will support decentralsied moderation and access control without relying on server operators or similar centralised mechanisms.
Survey Evidence:
- ActivityPub places the moderation to each server, resembling centralised control.
- Nostr provides no moderation, leaving users exposed.
To address server-based or absent moderation, the protocol will embed moderation metadata into repositories through means like signed blocklists/trust list. This will allow moderation to be portable, cryptographically verifiable, and independent of providers.

### Confidentiality and Encryption
Design Principle:
The protocol will provide confidentiality private posts, but in a more scalable way than heavy per-post encryption.
Survey Evidence:
- sAT Protocol encrypts each post with a symmetric key and distributes per-follower envelopes thus providing security but is computationally heavy.
- SSB relies on local feeds and gossip replication which provides integrity but not confidentiality
Thus, as opposed to encrypting each post individually, session-based or group-based keys may be used to reduce overhead while still ensuring confidentiality.

### Structured Replies and Threading
Design Principle:
The protocol will support nested replies and threaded conversations as opposed to limited reply models.
Survey Evidence:
- sAT Protocol does not support nested replies, limiting its expressiveness of social activity.
- Activity and Nost both support structured references between posts, but depends on servers or relays
Thus instead of relying on servers or relays, Replies will be represented as Git commits referencing parent posts, forming a DAG of coversastions. 