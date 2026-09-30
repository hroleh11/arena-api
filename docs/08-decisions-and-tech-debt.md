# 8. Technical Decisions & Tech Debt

[← Contents](README.md)

## Key decisions

### Event-driven sync over RabbitMQ instead of HTTP between services
**Decision.** Services exchange data only through Celery tasks addressed by name. Each service keeps its own copy of the entities it needs.
**Why.** Services stay loosely coupled: the app keeps working when the admin is down, and messages queue up until consumers return.
**Trade-off.** Eventual consistency. The task names and payloads form an implicit contract with no schema or versioning. Sync loops must be
prevented by hand (`_is_external`, `_skip_signal`, `_synced_from_new_architecture` flags).

### `global_id` UUID as the cross-service identifier
Every synced entity has a UUID, so records can be matched across databases without shared sequences.

### Direct-to-S3 uploads with presigned URLs
The API creates a draft post and media record, then returns presigned `PUT` URLs. The client uploads straight to S3.
**Why.** Large video files never pass through gunicorn, which keeps API workers free and avoids request timeouts.
**Follow-up.** Unused drafts are cleaned up weekly by cron.

### Dedicated post-sync queues and workers
Post sync runs on its own queue (`post_sync_column`) and worker, separate from the general `app` queue. Bulk imports (categories,
profiles) can't delay the arrival of new posts.

### Polymorphic v2 content model
`django-polymorphic` + GenericForeignKey media replaced the single `ColumnNews` table. Each post type (publisher, user, curator)
declares its allowed media types, and `global_id` uniqueness is enforced across all child tables in `save()`.

### MPTT comments limited to depth 1
`django-mptt` gives efficient tree queries. `Comments.clean()` limits the depth to one level, matching the mobile UI (comment + replies).

### Business logic in serializers and signals
There is no service layer. It keeps the code short, but side effects (sending tasks) are implicit and fire on every `save()`.

## Known issues and tech debt

| # | Issue | Where | Impact / suggestion |
|---|---|---|---|
| 1 | **Duplicate Celery task name** `column.tasks.move2content`, defined in both `column/tasks.py` (v1, `ColumnNews`) and `api_v2/tasks/news.py` (v2) | tasks | Only one handler is registered. Which one wins depends on import order. Rename one of them and update the sender in the Admin API. |
| 2 | Function `onesignal_categories_subscription` is defined twice in `column/tasks.py` | tasks | The second definition (task `onesignal_create_user`) shadows the first at module level. Rename it. |
| 3 | v1 and v2 content models coexist | `api`, `api_v2` | Duplicate logic and signals. Plan a migration away from `ColumnNews`/`MediaLinks`. |
| 4 | Legacy endpoints marked `TODO delete` (`my_columnnews*`, `columnnews_*`, v1 subscriptions) | `api/urls.py` | Remove once mobile clients stop using them. |
| 5 | Dead beta-invite code (`beta_auth`, `BetaUsers`, `BetaRefCode`) | `api` | Endpoints are commented out. Remove the code and tables. |
| 6 | `entrypoint.sh` runs `makemigrations` in production | Docker | Can generate unreviewed migrations on the server. Run only `migrate`. |
| 7 | gunicorn runs with `--reload` | `entrypoint.sh` | Development flag in production. |
| 8 | `delete_profile` task returns a DRF `Response` and deletes `profile.reports` twice | `column/tasks.py` | Harmless but confusing. Clean up. |
| 9 | Heavy use of `print` instead of `logging` | tasks, signals | Hard to filter logs in production. |
| 10 | `SOCIAL_AUTH_ALLOWED_REDIRECT_URIS` hard-codes dev domains | `settings.py` | Move to env. |
| 11 | `pickle` task serializer | Celery settings | Unsafe if the broker is ever exposed. Prefer JSON. |
| 12 | Very long-lived JWT (10-day access) | `SIMPLE_JWT` | Consider a shorter access lifetime. |
| 13 | Low test coverage, and tests run on SQLite while prod uses PostgreSQL | tests | Add tests for sync tasks. Consider testing on PostgreSQL. |
| 14 | `Dockerfile` / `Dockerfile.celery` are near-duplicates | Docker | Use one image with different commands. |
