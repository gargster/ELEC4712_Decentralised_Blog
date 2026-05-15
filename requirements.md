# Requirements for the proposed decentralised social media protocol
The following are functional requirements arranged by its type, justifed by what we observed in the analysis of existing protocols from alternatives.md:

## Identity Requirements
FR-01: The identity must be user-level, portable and not  coupled to a single hosting provider
### Justification (What we observed):
- We saw that the fundamental issues with ActivityPub was that identity was tied to servers (user loses identity if server shuts down) so identity must not depend on a single host.
- Similarly octototown was dependent on GitHub for its full identity and Git-as-Transport was tied to the server domain, which made identity non-portable.
- Social4git improved by allowing idenitty to move between Git providers 
- Nostr shows that portable identity is possible through cryptographic keys (identity owned by the user)
- AT protocol can supplement portable identity system using human-readable domain handles 

## Hosting Requirements
FR-02: The protocol must be fully static-hostable, server-less, not locked into a single provider (provider-agnostic)
## Justification:
- ActivityPub shows the high infrastructure cost and centralisation drawback of server-based hosting. 
- Octotown reinforces the danger of depending on a single provider (GitHub)
- The sAT protcol reassures the fact that static hosting is fully possible as it runs entirly on static files (/satellite/directory).
- Git-based protocols like Gitweets show how storing posts in Git repository can be viable as these can be hosted on any Git provider (which include static hostable ones)

## Replication Requirements
FR-03: Replication must be pull-based, supporting incremenetal updates - return only new posts since client's last known state.
## Justification:
- Activity shows that push fan-out (where updates are pushed to each follower) create load and scaling issues as push delivery becomes expensive as number of followers grow - reinforcing need for a pull-based model.
- Protcols like Gitweets show how instead of relying on servers to push updates, updates can be synchronised by client pulling data when needed.
- Git-as-Trasnport reinforces need for increment updates as transferring entire git husotry was highlighted as making replication slow

## Data Model Requirements
FR-04: The posts must be store in structured format such JSON objects
## Justification 
- It was shown in Gitweets that commit messages are not suitable to represent posts entirely as they may be long, structurered or contain media rich content. 
- Gitsocial reinforces this limitation of commit-based posts not scaling well for social content even with attached metadata.
- sAT protocol which represents posts as encrypted JSON envelopes shows that JSON + static hosting is a viable architecture (as it supports many social actions).
- Git-as-Transort shows a minimal git-based worfkflow with JSON files as posts and can easily support future extension.

## Storage Layout Requirements
FR-05: Each user's social data must be isolated from unrelated activity by utilising a dedicated directory or repository structure.
## Justificaton
- sAT shows the advantages of abstracting out all social activity in a single directory (through /satellite/ defined directory) making it simple to static host (hosts can just serve files from the directory)
- The limitations of group-level storage is shown in Octotown (per group repositories) which requires client to repeatedly scan the entire issues tracker.
- Git-as-Transport shows the simplicity of using a per-user dedicated subdirectory, supporting incremenetal replication as client can track the last syncrhonised file/post. 

## Security Requirements 
FR-06: The protocol must provide integrity and authencity through cryptographic signatures while giving an option for encryption.
## Justification
- We have found git-based protocols like social4git and gitsocial have provided integrity through git's existing hashing of commits - so it is acheivable to provide through existing infrastructure.
- However in such protocols anyone with access to the repository can create posts s followers cannot verify that posts was created by the claimed author thus signining is required to prove authencity.
- None of the git-based protocols discovered achieve confidenitiality, but sAT proves that encrypted static-hostable content is feasible so a option to encrypt private posts becomes a requirement.

## Disovery Requirements
FR-07: The protocol must include a decentralised, static-hostable discovery mechanism.
## Justification
- None of the explored protocols has a decenentralised static-hostable discovery mechanism. Git-based mechanisms like Gitweets and Social4Git require users to know each other's repository URLs.
- Octotown couples discovery to GitHUb's follow system while creates centralisation and dependency and ActivityPub has heavy server-based discovery which is not static hostable.

## Usability Requirements
FR-08: The protocol must abstract the underlying git operations for following, posting, syncing behind a client interface
## Justification
- We have seen that simple models like Gitweets expose Git directly to the user, forcing users to understand git commands like git fetch which is too technical for a proper social protocol.
- Social4git and gitsocial abstract it further with simple command like social4git sync but still require users to run commands on a command line interface. This is not user-friendly so we should leave the intiation of replication to the client. 

## Interoperability Requirements
FR-09: The protocol must reuse existing infrastructure (Git, HTTPS, static hosting) and define a standard format which any Git-based social client can use across  Git-supported static hosts.
## Justification
- Git infrastructure has been found to be explored and reliable to some extent as all explored git-based prototype use Git hosting, remotes and replication. So the protocol should reuse this infrastructure.
- However their is no consistency between how each prototype store posts, which show the need for one consistent standard format.
- Thus we want to provide a single format which existing and future Git-based social clients can follows- functioning on any Git-supported static host without servers.
