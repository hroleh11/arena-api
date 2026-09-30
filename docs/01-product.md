# 1. Product Overview

[← Contents](README.md)

## What Vylo is

Vylo is a sports-focused social mobile app. The feed has two kinds of content:

- **Publisher news**: articles from publisher accounts (newsstands), created or imported in the admin backend. RSS/site scrapers for ESPN, NYT, The Guardian and others exist there but are currently disabled.
- **User and creator posts**: short videos or audio clips with a title and a category (NBA, NFL, MMA, Soccer, etc.).

Social features are built around this content: follows, comments, and video replies to other posts. The app also links to the DFS module
**Vylo Props** (over/under predictions on player stats) through lineups.

## Roles

| Role | How it's defined | Capabilities |
|---|---|---|
| **User** | `Profile` with `is_source=False` | Browse the feed, follow, post, comment, report, block |
| **Creator** | `Profile.is_creator=True` | Everything a user can do. Can also connect social accounts (Instagram/TikTok/YouTube), and the admin imports content from them. Gets an invite email with a password. |
| **Publisher (Newsstand)** | `Profile.is_source=True` | News source, created and managed from the admin |
| **Curator** | Profile stored as JSON inside `CuratorNews` | Author of curated posts (text/photo/video + props), created in the admin |

Vylo Props access flags: `have_access_to_vylo_props`, `dfs_pre_auth_completed`, `creator_cash`.

## Key features

### Sign-up and login
- Email + password (with password confirmation). Usernames are checked through the `is_valid_username` endpoint.
- Social login with **Google, Facebook, Apple**.
- **Draft user**: before full registration, the email can be confirmed with a code sent by email (3 attempts).
- Password reset with a 6-digit code (3 attempts, 30-minute lifetime).
- `signup_code` stores the code a user signed up with (referral or marketing flows, `UNIVERSAL_CODES`).
- New users automatically follow the accounts on the **Auto Follow** list, which is managed in the admin.

### Profile
- Photo, bio, website, gender, birthday, timezone.
- Personal link (Firebase Dynamic Link) and a profile QR code.
- Post, follower and following counters.
- Public web profile: `profile/web/<username>`.
- Account deletion.

### Follows
- Follow publishers or users (`publishers_subscription`) and categories (`categories_subscription`).
- Category follow changes are synced to OneSignal tags for targeted push notifications.

### User posts
1. The client requests a presigned URL and receives the ID of a draft post.
2. It uploads the video (`mp4`) or audio (`mp3`) and a thumbnail directly to S3.
3. It updates the post (title, category, status "published") and can attach a Vylo Props **lineup**.
4. The post goes to moderation in the admin (Hive AI + human review). Once approved, it shows up in the feed.

Drafts that are never published are deleted automatically after 7 days.

### Replies and comments
- A post can reply to a news item, a sports event or a comment (`response_to` + `response_type`).
- Comments form a tree that is at most 1 level deep (v2, MPTT).

### Community safety
- Report a post (`news_report`) or a user (`profile/report/`). Reasons: off-topic, IP infringement, hate, nudity, spam, other, abusive user.
- Block users.

### Other
- Trending search queries (`search_trending`).
- `env_var` returns the current Android app version, used to force updates.
- `join_link` returns an invite link.
