# Alternative Decentralised Social Protocols
## ActivityPub
## Posting Workflow
### Brief Description:
The following sequence diagram shows how Alice's followers recieve the posts she makes. First of all, Alice creates a Post within here client (e.g. Mastodon app) which then constructs this as a Create activity. The client then sends this to Alice's server by making an HTTP POST to her outbox endpoint. The server validates this activity and stores it Alice's outbox. Following this, Alice's server iterates through all her followers and pushes this same Create activity to each follower's server by POSTing it to their inbox endpoints. The follower's server then all validate the messages and update their timeline. Last of all, the follower's clients get notfied or manually fetch the updated timelines from their server and Alice's post is rendered to their feeds.
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
### Brief Description:
The sequence diagram shows how Alice starts following Bob. First, Alice specifies Bob's handle with key word Follow on her client. Alice's Client sends this as a Follow activity to her server by HTTP POSTing it to her outbox. This Follow activty is then forwarded to Bob's Server by POSTing to Bob's Inbox endpoint. Bob's server then validates the request, and if accepted adds Alice to his followers list. This server then sends a Accept activity to Alice's Server through POSTing to its inbox. The server then validates, stores the Accept activity and marks Bob as followed. Now, whenever Bob posts, Bob's server will push that post to ALice's server, which will then appear in her timeline.  

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
### Brief Description:
The following sequence diagram shows Alice's followers receieve the posts which Alice posts. Firstly once Alice makes her post, Alice's Client Creates a signed event of kind 1 and publishes it to one or more relays. These relays validate the event and store it, then it forwards the event to all of Alice's 'followers' (clients that have subscribed to Alice's public key). The follower's client then build the follower's feed with Alice's post. 

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
### Brief Description:
The following sequence diagram demonstrates how following works in Nostr, which is handled entirely on the client side. Once Bob decides to Follow Alice, Bob's client creates a signed contacts event (kind 3) which lists Alice's public key. This event is then forwarded to multiple relays, later Bob's client sends a REQ subscription message to the relays. This simply tells the relays to send events associated with a target public key. Finally, the relays send Alice's past events and streams her future events. 

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
## Secure Scuttlebutt (SSB)
## Posting Workflow
### Brief Description:
The sequence diagram shows the posting workflow in SSB. Once Alice writes a new post, Alice's client creates a message object containing the post content. It asssigns the object the next identifying sequence number in her feed and computes the hash of the previous message, adehering to the feeds linked list data structure. The client then signs this entire message using Alice's private key and appendsit to Alice's local append-only feed. Since SSB is offline-first, when Alice posts, nothing is sent to anyone immediately and followers like Bob will only recieve this post later when the devices connect and gossip replication occurs. 

```mermaid
sequenceDiagram
    participant Alice
    participant AliceClient
    participant AliceFeed as Alices_Local_Feed

    Alice->>AliceClient: Write new post
    AliceClient->>AliceClient: Create message object (content)
    AliceClient->>AliceClient: Assign next sequence number (seq = last_seq + 1)
    AliceClient->>AliceClient: Compute hash of previous message (prev = hash(previous_message))
    AliceClient->>AliceClient: Sign message with private key (signature = sign(content + seq + prev))
    AliceClient->>AliceFeed: Append signed message to local feed

    Note over AliceFeed: Post is stored ONLY in Alice's local feed.<br>SSB does NOT push posts to followers when posting.<br>Bob receives this post later during gossip replication.
```
## Following + Replication Workflow
### Brief Description:
This sequence diagram shows how Bob follows Alice by adding her feed ID to his local follow list but does not notfy Alice. Later, when Bob's device connects with Alice's device (e.g. through wifi, pub server) gossip replication begins. This process involves Bob's client asking the Alice's client, what her latest sequence number is. Alice's client responds with the latest (highest) sequence number, so Bob's client then requests any missing messages from before. Once Alice's Client sends the missing signed messages, Bob verifies each signature using Alice's public key. These verfied messages are then appended to Bob's local copy of Alice's feed. Overall, this is a pull-based process and only happens when peers connect. 

```mermaid
sequenceDiagram
    participant Bob
    participant BobClient
    participant BobFollowList as Bobs_Follow_List
    participant AliceClient
    participant AliceFeed as Alices_Local_Feed
    participant BobFeed as Bobs_Copy_of_Alices_Feed

    Bob->>BobClient: Follow Alice (add Alice's feed ID)
    BobClient->>BobFollowList: Store Alice's feed ID

    Note over BobClient: Replication occurs via gossip when devices connect

    BobClient->>AliceClient: Gossip: "What is your latest sequence number?"
    AliceClient->>BobClient: "My latest sequence number is N"

    BobClient->>AliceClient: Request missing messages
    AliceClient->>BobClient: Send missing signed messages

    BobClient->>BobClient: Verify signatures using Alice's public key
    BobClient->>BobFeed: Append verified messages to Bob's local copy

    Note over BobFeed: Bob receives Alice's posts only during gossip replication.<br>SSB pulls missing messages when devices connect.<br>No real-time delivery or push notifications.
```
## sAT Protocol (s@)
## Posting Workflow
### Brief Description:
The following diagram shows how posting works in s@ which is entirely static site based and all encryption & processing happens on the browser, not on a server. Once Alice writes a new post on her browser, the browser constructs a plaintext JSON object of the post and it's meta data. A fresh symmetric key is newly generated for this post, and used to encrypt the whole JSON post. This encrypyted post is then named according to its id and uploaded to the posts subfolder within Alice's static site. Alice's browser then updates the index.json file (which is a file listing all post IDs in order) to include the new post's id. Finally, this updated index.json is uploaded to Alice's static site so that her followers can later discover the new post.

```mermaid
sequenceDiagram
    participant Alice
    participant AliceBrowser as AliceBrowser
    participant AliceSite as AliceStaticSite
    participant PostsDir as alice.com/satellite/posts/
    participant IndexFile as alice.com/satellite/index.json

    Alice->>AliceBrowser: Write new post ("Hello!")
    AliceBrowser->>AliceBrowser: Create JSON object (id, author, timestamp, text)
    AliceBrowser->>AliceBrowser: Generate new symmetric content key
    AliceBrowser->>AliceBrowser: Encrypt JSON post with symmetric content key
    AliceBrowser->>PostsDir: Upload encrypted post file (id.json)
    AliceBrowser->>IndexFile: Append post ID to index.json (plaintext)
    AliceBrowser->>AliceSite: Upload updated index.json

    Note over AliceSite: alice.com/satellite/posts/ is a folder on Alice's static site<br>containing encrypted post files named by their IDs.<br>alice.com/satellite/index.json is a plaintext list of those IDs.
```
## Following + Replication Workflow
### Brief Description:
The following diagram shows how Bob follows Alice, and later syncronizes to recieve her posts. First of all, Bob intiates a follow action in his browser, specififying Alice's domain name which is then added to Bob's local json follow list by his browser. Bob's Browser then sends a follow request to Alice's static site which then forwards this request to Alice's Browser. Alice's browser then encrypts the symmetric content key (used to decrypt her posts) for Bob specifically using his public key. This encrypted package, known as the key envelope for Bob is then uploaded Alice's Static Site by Alice's Browser. Later, when Bob synchronises Bob's Browser fetches the key envelope and decrypts it with his private key, discovering the symmetric content key. Next, the index.json on Alice's Static Site is fetched by Bob's Browser which lists all Alice's post IDs in plaintext. Each of the IDs in the list corresponds to an encrypted post file within Alice's Static Site (under posts subdirectory). All of these posts are fetched and decrypted by Bob locally using the symmetric content key thus building Bob's feed.

```mermaid
sequenceDiagram
    participant Bob
    participant BobBrowser as BobBrowser
    participant BobFollowList as follow-list.json
    participant AliceBrowser as AliceBrowser
    participant AliceSite as AliceStaticSite
    participant IndexFile as alice.com/satellite/index.json
    participant AlicePosts as alice.com/satellite/posts/

    Bob->>BobBrowser: sAT follow alice.com
    BobBrowser->>BobFollowList: Add "alice.com" to follow-list.json

    BobBrowser->>AliceSite: Send follow request
    AliceSite->>AliceBrowser: Deliver follow request

    AliceBrowser->>AliceBrowser: Encrypt symmetric content key for Bob
    AliceBrowser->>KeyEnvelope: Create key-envelope-for-bob.json
    AliceBrowser->>AliceSite: Upload key envelope for Bob

    Note over KeyEnvelope: Key envelope contains the symmetric content key<br>encrypted with Bob's public key.

    Bob->>BobBrowser: sAT sync
    BobBrowser->>AliceSite: Fetch key-envelope-for-bob.json
    AliceSite->>BobBrowser: Return encrypted content key
    BobBrowser->>BobBrowser: Decrypt key envelope using Bob's private key<br>(recover symmetric content key)

    BobBrowser->>AliceSite: Fetch index.json
    AliceSite->>IndexFile: Return plaintext list of post IDs
    BobBrowser->>BobBrowser: Read IDs (e.g. ["123","122","121"])

    BobBrowser->>AlicePosts: Fetch encrypted post files (for each ID)
    AlicePosts->>BobBrowser: Return encrypted posts
    BobBrowser->>BobBrowser: Decrypt posts using symmetric content key
    BobBrowser->>BobBrowser: Build/update Bob's feed view

    Note over BobBrowser: Followers fetch index.json to discover post IDs,<br>then fetch each encrypted post file from /satellite/posts/<id>.json<br>and decrypt it locally using the recovered symmetric content key.
```
## AT Protocol
## Posting Workflow
### Brief Description:

```mermaid
sequenceDiagram
    participant Alice as Alice (User)
    participant AlicePDS as Alice's PDS (Stores Alice's Repo)
    participant Relay as Relay/BGS (Global Update Collector)
    participant DID as DID Service (Public Key Lookup)
    participant AppView  as AppView (Global Index + Feeds)

    Alice->>AlicePDS: Create new post ("Hello world")

    AlicePDS->>AlicePDS: Create post record (type: app.bsky.feed.post)
    AlicePDS->>AlicePDS: Sign record with Alice's private key
    AlicePDS->>AlicePDS: Write signed record into Alice's repo

    AlicePDS->>Relay: Announce repo update<br>("Alice has a new record at Path X")

    Relay->>Relay: Add update to firehose stream<br>(firehose = continuous stream of all repo events)
    Relay->>AppView: Deliver firehose event<br>(event = one update from a user's repo)

    AppView->>DID: Fetch Alice's DID Document<br>(get public key)
    DID->>AppView: Return public key 

    AppView->>AppView: Verify signature on post<br>(using Alice's public key)
    AppView->>AppView: Index post<br>("Post by Alice at time T")

    Note over AppView: Followers do NOT fetch Alice's repo.<br>AppView verifies, indexes, and serves posts<br>to followers like Bob when they request their feed.
```
## Following + Replication Workflow
### Brief Description:

```mermaid
sequenceDiagram
    participant Bob as Bob (User)
    participant BobPDS as Bob's PDS (Stores Bob's Repo)
    participant Relay as Relay/BGS (Global Update Collector)
    participant DID as DID Service (Public Key Lookup)
    participant AppView as AppView (Global Index + Feeds)

    Bob->>BobPDS: Click "Follow Alice"
    BobPDS->>BobPDS: Create follow record<br>(type: app.bsky.graph.follow)
    BobPDS->>BobPDS: Sign follow record with Bob's private key
    BobPDS->>BobPDS: Write signed follow record into Bob's repo

    BobPDS->>Relay: Announce repo update<br>("Bob now follows Alice")
    Relay->>Relay: Add update to firehose stream<br>(firehose = continuous stream of all repo events)
    Relay->>AppView: Deliver firehose event<br>(event = one update from a user's repo)

    AppView->>DID: Fetch Bob's DID Document<br>(get Bob's public key)
    DID->>AppView: Return public key
    AppView->>AppView: Verify signature on follow record<br>(using Bob's public key)

    AppView->>AppView: Update social graph<br>("Bob follows Alice")
    Bob->>AppView: Request home timeline

    AppView->>AppView: Look up Bob's follow graph<br>(find users Bob follows e.g. Alice)
    AppView->>AppView: Retrieve indexed posts<br>(posts previously indexed from Alice)
    AppView->>AppView: Build Bob's feed<br>(combine posts from all followed users)

    
    Note over AppView: Updating the social graph does not deliver posts to Bob. Bob only sees Alice's posts when he requests his home timeline and AppView uses the follow graph and indexed posts to build his feed.
    

    AppView->>Bob: Return posts from followed users<br>(includes Alice's posts)

```

## Git Based Attempts
## social4git
## Posting Workflow
### Brief Description:
The following sequence diagrams shows how posting operates in social4Git, which is a Git-based pull-replication model. When Alice makes a post, her client creates the post file and metadata file which are both commited and pushed to her public repository. Followers recieve the posts only upon manually running social4git sync, which fetches updates from Alice's public repository and copies the new post into their own private repository. 

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
### Brief Description:
The following sequence diagram shows Bob attempts to follow Alice in social4git. Once Bob specifies Alice's Repository URL, Bob's client adds the URL to a local following list and uploads it to Bob's private repository which means the following action is completed on Bob's side without approval from Alice. After some time, when Bob wants to retrieve Alice's posts, he runs social4git sync, so his client then runs git fetch to extract any of Alice's new posts and copies them into Bob's private repository.

Following simply means adding a repository URL to a local following list stored in the follower's private repository as shown by the inte
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
## gitsocial
## Posting Workflow
### Brief Description:
The following sequence diagram shows how posting works in GitSocial. As opposed to social4git, gitsocial has a single Git repository per user which has a dedicated branch called gitsocial for all social activity. When Alice makes a post, Alice's client represents the post as a Git commit on this gitsocial branch. This commit contains the post text along with the GitMsg metadata which indicates whether it is a post, comment, repost, or quote. In order to publish the post, this commit is pushed to Alice's repsoitory, making it available for followers. Since gitsocial is a pull-based replication model, her do not recieve these posts immediately, but the posts become visible when the follower later fetches the gitsocial branch during sync.

```mermaid
sequenceDiagram
    participant Alice
    participant AliceClient as AliceClient
    participant AlicePublicRepo as AlicePublicRepo
    participant AliceGitSocialBranch as AliceGitSocialBranch

    Alice->>AliceClient: gitsocial post "Hello!"
    AliceClient->>AliceClient: Create commit message (post text)
    AliceClient->>AliceClient: Attach GitMsg metadata (type = post/comment/repost/quote)
    AliceClient->>AliceGitSocialBranch: git commit -m "Hello"! (on gitsocial branch)
    AliceGitSocialBranch->>AlicePublicRepo: git push origin gitsocial (publish branch)

    Note over AliceGitSocialBranch: Posts are commits on the gitsocial branch.<br>Pushing makes them available for followers to fetch later.
```
## Following + Replication Workflow
### Brief Description:
The following sequence diagram shows the following and replication workflow. For Bob to folllow Alice this means Bob needs to add Alice's repository URL to a follow-list JSON file stored inside Bob's repository. The steps required for updating this file are usual git steps involving modifying the file, git adding, commiting and then pushing to Bob's Repository. Compared to other conventional protocols, this follow action is local as Alice does not need to approve anything. Later when Bob runs sync, his client reads the follow list to determine which repositores to fetch from. For each of the followed users, the client fetches the gitsocial branch from their repository and the returned commits are stored in Bob's repository. Lastly, to build or update Bob's feed view with Alice's commits (or whoever he follows), Bob's Client interprets GitMsg metadata.

```mermaid
sequenceDiagram
    participant Bob
    participant BobClient as BobClient
    participant BobPublicRepo as BobPublicRepo
    participant BobFollowList as BobFollowList
    participant AlicePublicRepo as AlicePublicRepo
    participant AliceGitSocialBranch as AliceGitSocialBranch

    Bob->>BobClient: gitsocial follow <AliceRepoURL>
    BobClient->>BobFollowList: Update follow.list.json 
    BobClient->>BobPublicRepo: git add follow-list.json && git commit -m "Update follow list"
    BobClient->>BobPublicRepo: git push (publish updated follow list)

    Note over BobFollowList: Follow list is a JSON file storing repository URLs to fetch from.

    Bob->>BobClient: gitsocial sync
    BobClient->>BobFollowList: Read follow-list.json (get list of repos to fetch)

    BobClient->>AlicePublicRepo: git fetch <AliceRepoURL> gitsocial
    AlicePublicRepo->>AliceGitSocialBranch: Resolve gitsocial branch
    AliceGitSocialBranch->>BobClient: Return new commits from gitsocial branch

    BobClient->>BobPublicRepo: Store fetched commits locally
    BobClient->>BobClient: Read GitMsg metadata (e.g. post/comment/repost/quote)<br>and build/update Bob's feed view

    Note over BobPublicRepo: Bob receives Alice's posts here during fetch.<br>Feed is constructed by reading commits from followed repos.<br>Replication is pull-based and not real-time.
```
## Octotown
## Posting Workflow
### Brief Description:
The following sequence diagram shows how posting works in Octotown, which unlike other Git-based protocols, reuses GitHub's existing Issues system. Each user has a repository named .social which contains all posts represented as GitHub Issues. When Alice writes a post in the Octotown client, the client constructs a REST API request to the GitHubIssuesAPI, including the post content in the JSON body to the .social endpoint of Alice. Upon recieving the request, GitHub creates a new issue inside the .social repository, which now becomes the published post which followers can later fetch and interact with. 

```mermaid
sequenceDiagram
    participant Alice
    participant AliceClient as AliceClient
    participant GitHubIssuesAPI as GitHubIssuesAPI
    participant AliceSocialRepo as AliceSocialRepo (.social)

    Alice->>AliceClient: Write new post "Hello!"
    AliceClient->>AliceClient: Prepare REST request<br>POST /repos/Alice/.social/issues<br>Body = { "title": "Hello!", "body": "My first post" }
    AliceClient->>GitHubIssuesAPI: Send POST request (create Issue)
    GitHubIssuesAPI->>AliceSocialRepo: Create new Issue (store post)
    Note over AliceSocialRepo: The .social repo is a normal GitHub repository.<br>Posts are stored as Issues, not files or commits.
```
## Following + Replication Workflow
### Brief Description:
The following sequence diagram shows how following works in Octotown, which entirely functions on GitHub's in-built follow system. First of all, Bob has to follow Alice's GitHub profile which then updates GitHub's own follow list of Bob. Next, when Bob opens the Ocototown client to view his feed, his client begins replication by querying GitHub's Follow API to retrive the list of GitHub accounts Bob follows, which should include Alice. Since this list contains only user identities, the client has to determine which of these users participate in social actions through Octotown by checking whether they have a .social repository. For each of the followed users, the client checks if their repository has a .social repository, which would rturn true for Alice meaning she is a octotown user. After confriming this, Bob's client fetches posts, utilising GitHub's list issues for repository operation. Consequently this build's Bob's feed with all issues (posts) stored in the .social repository of the users he follows, including Alice.

```mermaid
sequenceDiagram
    participant Bob
    participant BobClient as BobClient (Octotown UI)
    participant GitHubFollowAPI as GitHubFollowAPI
    participant GitHubIssuesAPI as GitHubIssuesAPI
    participant AliceSocialRepo as AliceSocialRepo (.social)

    Bob->>GitHubFollowAPI: Click "Follow" on Alice's GitHub profile
    GitHubFollowAPI->>GitHubFollowAPI: Update Bob's follow list

    Bob->>BobClient: Open Octotown client (view feed)
    BobClient->>GitHubFollowAPI: GET /users/Bob/following (fetch users who Bob follows)
    GitHubFollowAPI->>BobClient: Return followed users (only user accounts, includes Alice)

    BobClient->>AliceSocialRepo: GET /repos/Alice/.social (check if repo exists)
    AliceSocialRepo->>BobClient: .social repo found (Alice is an octotown user)

    BobClient->>GitHubIssuesAPI: GET /repos/Alice/.social/issues
    GitHubIssuesAPI->>BobClient: Return posts (Issues)

    BobClient->>BobClient: Build Bob's feed from fetched posts
    Note over BobClient: Replication is pull-based and only occurs<br>when Bob opens the Octotown client.
```
## Git as Federation Transport
## Posting Workflow
### Brief Description:
The following diagram shows the posting workflow for Git as Federation Transport which is a multiple-users per server based model. A single server (e.g. AliceServer) hosts a community of users, similar to Mastadon. Once a user on the server (Alice) creates a post, the server converts the post into a JSON file which is then commited and stored into the servers's Git Repository. After committing, the server pushes the commit (containing the post) to every other server AliceServer follows (here servers follow other servers as opposed to users following users). The push action does not mean that the other servers have actally receieved the post socially since it only transfer Git Objects. Only when the remote servers later run git fetch during their replication cycle, will they be able to built the feed with the posts.

```mermaid
sequenceDiagram
    participant AliceUser as Alice (User on AliceServer)
    participant AliceServer as AliceServer
    participant AliceRepo as AliceServerRepo (Git Repo)
    participant BobServer as Bobserver (Server AliceServer Follows)
    participant CarolServer as Carolserver (Server AliceServer Follows)

    AliceUser->>AliceServer: Create new post ("Hello!")

    AliceServer->>AliceServer: Generate JSON file for post<br>e.g., users/alice/posts/0012.json

    AliceServer->>AliceRepo: git commit -m "New post by Alice"<br>(commit includes JSON post file)
    AliceRepo->>AliceRepo: Store commit in server's Git History

    AliceServer->>BobServer: git push bob-server main<br>(send new post commit to followed server)
    AliceServer->>CarolServer: git push carol-server main<br>(send new post commit to followed server)
    
    Note over AliceRepo: BobServer and CarolServer do NOT recieve the post here.<br>They only get it later when they run git fetch. 
```
## Following + Replication Workflow
### Brief Description:
The following diagram shows how "following" works in this model, which is server-to-server and not user-to-user. For BobServer to follow AliceServer, BobServer's operator (e.g. admin) adds AliceServer as a Git remote. Once this is configured BobServer periodically runs git fetch to pull new commits from servers it follow which now includes AliceServer. AliceServer responds to BobServer by sending Git packfile which is a bundle of compressed Git objects containing the JSON post file which however is not in a readable form yet. Next, Git on BobServer writes these fetched objects into BobServer's Git repository, while updating its pointer to AliceServer's latest commit. In order to find the JSON post files, BobServer scans the new commits in the repository. The server parses these JSON files and imports them into its own timeline database, upon which the users on BobServer (e.g. Bob, Tom) can see Alice's posts. Overall this model is pull-based, meaning even if AliceServer had pushed to BobServer, BobServer would not show the post unless it later performs a fetch and imports it. This can be seen as a negative as AliceServer's push may effectively be wasted - the server it inteded to send post won't recieve the post until they choose to fetch it.

```mermaid
sequenceDiagram
    participant Admin as Admin (BobServer Operator)
    participant BobServer as BobServer (Application)
    participant BobRepo as BobServerRepo (Git Object Store)
    participant AliceServer as AliceServer (Git Server)

    Admin->>BobServer: Add AliceServer as a remote<br>git remote add alice-server git@alice.social:stegodon.git
    BobServer->>BobServer: Store remote configuration<br>(BobServer now follows AliceServer)

    BobServer->>AliceServer: git fetch alice-server main<br>(periodically fetch new commits)
    AliceServer->>BobServer: Send Git packfile<br>(compressed Git objects: commits, trees, blobs)

    BobServer->>BobRepo: Write fetched commits into repo<br>(Git stores objects and updates Alice’s latest commit pointer)
    BobServer->>BobRepo: Read commits from repo<br>(application scans for JSON post files)

    BobServer->>BobServer: Parse JSON post files from commits<br>(convert Git objects into social posts)
    BobServer->>BobServer: Update timeline database<br>(Bob, Tom, etc. now see Alice’s posts)

     Note over BobRepo: BobRepo never initiates anything.<br>It only stores Git objects written during fetch.<br>BobServer (the application) must actively read and import posts.
```


