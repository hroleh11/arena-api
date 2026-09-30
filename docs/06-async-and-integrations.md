# 6. Async Tasks & Integrations

[← Contents](README.md)

## How inter-service messaging works

- All services share **one RabbitMQ broker** and one Celery exchange (`celery`).
- A sender does not import the task code. It calls `app.send_task('<name>', args=[...], queue='<queue>')`.
- The receiver registers a task with the **same explicit name** and listens on that queue.
- Payloads are dicts built with "export" serializers. Serializer: `pickle` (`CELERY_TASK_SERIALIZER`); accepted content: `json`, `pickle`.
- Results are stored in the DB (`django-celery-results`, `CELERY_RESULT_BACKEND = 'django-db'`).

## Outbound: what Content API sends

Triggered by Django signals in `api/signals.py` and `api_v2/signals/`.

| Trigger | Task | Queue | Consumer |
|---|---|---|---|
| `ColumnNews` saved with status Published/Approved | `column.tasks.move2approve` | `post_sync_admin` | Admin API (moderation) |
| same | `column.tasks.system_events` | `post_sync_events` | Events |
| `ColumnNews` deleted | `column.task.delete_from_admin` | `post_sync_admin` | Admin API |
| `ColumnNews` with `lineup_global_id` and no `lineup_data` | `vylo_bets.tasks.fetch_lineup_data_request` (via `api.tasks.fetch_lineup_data`) | `lineup_priority` | vylo-bets |
| `Profile` saved (not `_is_external`) | `column.tasks.profile2admin` / `column.tasks.profile2events` | `post_sync_admin` / `post_sync_events` | Admin / Events |
| New `User` | `column.tasks.onesignal_create_user` | `app` | self |
| `User.is_active` changed | `column.tasks.deactivate_profile` | `post_sync_admin` | Admin |
| `User.last_login` changed | `column.tasks.update_profile_login_info` | `post_sync_admin` | Admin |
| Publisher follow added/removed | `column.tasks.profile_add_subscription` / `profile_remove_subscription` | `post_sync_events` | Events |
| Category follows changed | `column.tasks.onesignal_categories_subscription` | `post_sync_column` | self (OneSignal tags) |
| `NewsReport` created | `column.tasks.move2report` | `post_sync_admin` | Admin |
| `ReportedProfiles` created | `column.tasks.move_reported_profile2admin` | `post_sync_admin` | Admin |
| `BlockedProfiles` created / deleted | `column.tasks.move_blocked_profile2feed` / delete | `post_sync_feed` | Feed |
| `ShareIntroEvents` | `column.tasks.update_share` | `post_sync_feed` | Feed |
| `CreatorSocialAssociation` saved / deleted | `column.tasks.create_creator_social` / `delete_creator_social` | `post_sync_admin` | Admin |
| v1 comment created / deleted | `column.tasks.add_comment`, `update_responses_counter`, `system_events`, `delete_comment` | admin / events | Admin / Events |
| v2 comment saved | `v2comments2feed`, `add_comment`, `comments2events` | `post_sync_feed`, `post_sync_admin`, `post_sync_events` | Feed / Admin / Events |
| v2 comment deleted | `delete_comment`, `v2delete_comment` | admin / feed / events | all |
| Avatar changed | `column.tasks.update_profile_image` | — | Admin / Feed |

## Inbound: tasks Content API executes

Defined in `column/tasks.py`, `api/tasks.py`, `api_v2/tasks/news.py`.

| Task | Queue | What it does |
|---|---|---|
| `column.tasks.move2content` | `post_sync_column` / `app` | Upsert a post from the admin (see the name clash note in [section 8](08-decisions-and-tech-debt.md)) |
| `column.tasks.curator_news_to_content` | `app` | Upsert a `CuratorNews` (3 retries) |
| `column.tasks.delete_curator_news` | `app` | Soft-delete a curated post and its media |
| `column.tasks.move_category2column` | `app` | Upsert a category |
| `column.tasks.delete_category2content` | `app` | Delete a category |
| `column.tasks.profile2app` | `app` | Upsert a profile from the admin (approval, creator flags, etc.) |
| `column.tasks.update_or_create_event` | `app` | Upsert a sports event |
| `column.task.delete_from_app` / `delete_from_app_list` | `app` | Mark post(s) Deleted |
| `column.task.report_news` | `app` | Mark a post Declined (report upheld) |
| `column.task.delete_profile_app` | `app` | Hard-delete a profile with its reports, blocks, posts, media and user |
| `column.tasks.update_share` | `app` | Save a share event |
| `column.tasks.update_creator_social` / `delete_creator_social` | `app` | Sync creator socials |
| `column.tasks.auto_follow2app` / `auto_follow_delete` | `app` | Manage the auto-follow list |
| `column.tasks.update_events_counters` | `app` | Update post event counters |
| `column.tasks.onesignal_*` | `app` | Create a OneSignal user, update tags |
| `api.tasks.receive_lineup_data` | `app` | Store the lineup snapshot on a post |
| `column.tasks.move_news2beta` | `app` | Legacy beta invites |

## Periodic jobs (cron)

Configured in `CRONJOBS` in `column/settings.py`, registered with `python manage.py crontab add` at container start.

| Schedule | Function | Purpose |
|---|---|---|
| hourly (`*/60`) | `api.cron.delete_expired_codes` | Delete password reset codes older than 30 min |
| Mondays 00:00 | `api.cron.delete_draft_news` | Delete drafts older than 7 days |
| every minute | `api.cron.create_personal_link` | Generate a Firebase Dynamic Link for profiles without one |

## External integrations

| Service | Where | Purpose |
|---|---|---|
| **AWS S3 + CDN** | `django-storages`, `api_v2/storages.py`, `boto3` | Media storage; presigned PUT URLs for direct client uploads. Separate buckets for images, raw video, optimized video, and audio. |
| **OneSignal** | `api/one_signal/` | Push notifications: user creation (`external_id` = profile `global_id`), category tags, segments (`segments.py`) |
| **Firebase Dynamic Links** | `api/shortcust.py` | Short personal profile links that open the app store if the app is not installed |
| **Google / Facebook / Apple** | `social-auth` + `api/pipeline.py` | Social login with partial registration |
| **SMTP** | djoser + `api/email.py` | Password reset, account activation, creator invite emails |
