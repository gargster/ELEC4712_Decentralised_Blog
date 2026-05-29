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
- AT Protocol shows that human-readable user handles can map to keys.
The only identity model which is portable across hosts is based on cryptographic keys and AT Protocol can be layered on top of key-based identity.

### Pull-Based, Incremental Replication 
Design Principle:
The protocol will use pull-based replication, where clients fetch only new social data since their last known state.

Survey Evidence:
- ActivityPub highlights the scalability issues in push-based fan-out.
- Git-as-Transport demonstrates inefficiency of full history transfers 
- Git-based prototypes (GitSocial, Social4Git, Gitweets) all rely on Git's pull model: posting = push commit, replication = fetch commits.
Using Git's existing pull model, where only new commits are transferred inherently supports incremental replication.

### Dedicated User Directory (Clear Separation of Social Data)
The protocol will store all social data inside a dedicated directory within the user's Git repository (e.g. /social/). This directory will the user's action objects, identity information (e.g public key and user handle) and the static profile file.

Survey Evidence:
- sAT isolated all social data in a dedicated /satellite/ directory.
- Many Git-based prototypes (GitSocial, Social4Git, Gitweets) organise social data using a dedicated subdirectory, supporitng incremental replication.
Using a dedicated directory is common and effective across Git-based systems, but unlike prior prototypes where identity is bound to repo URL, we seaprate identity from hosting location so directory can be hosted on any Git provider or static host (provider agnostic).

### JSON as the Storage Format (Encoding Layer)
The protocol will use JSON as the storage and encoding format for all social data, including the structured representations of action types defined in 1.1, the static profile file, identity information, and supporing metadata.

Survey Evidence:
- Gitweets shows tgat commit messages are unsuitable for structured posts.
- Simiarly GitSocial shows the limitations of embedding posts inside commit messages.
- sAT and Git-as-Transport both store posts as JSON files, showing 


## Extendable Elements
## Rejected Elements
## Redesigned Elements