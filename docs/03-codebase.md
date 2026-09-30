# 3. Codebase Structure

[← Contents](README.md)

## Project tree

```
arena-api/
├── column/                 # Django project (settings, urls, celery, inbound cross-service tasks)
│   ├── settings.py         # all configuration, reads .environment via django-environ
│   ├── urls.py             # root routing, Swagger/ReDoc, JWT, social auth
│   ├── celery.py           # Celery app 'column', autodiscover_tasks()
│   ├── tasks.py            # tasks invoked BY OTHER services (imports from the admin)
│   └── password_validation.py  # custom password validators
│
├── api/                    # v1: core app (profiles, v1 posts, auth)
│   ├── models/             # categories, news, posts, profiles, sportsbook, others
│   ├── serializers/        # auth, profile, news, comments, upload, tasks (import), signals (export)
│   ├── views/              # auth, profile, news, comments, upload, categories, publishers, search, creators
│   ├── versioned/v2/       # /api/v2/*: newer versions of some endpoints on top of v1 models
│   ├── one_signal/         # OneSignal REST client (UserAPI, SegmentAPI) + UserBuilder
│   ├── templates/          # HTML emails (password reset, activation, creator invite)
│   ├── signals.py          # post_save/m2m_changed → send_task to other services
│   ├── tasks.py            # lineup data exchange with vylo-bets
│   ├── cron.py             # periodic jobs (django-crontab)
│   ├── pipeline.py         # social-auth pipeline steps (partial registration)
│   ├── email.py            # email classes (djoser / templated-mail)
│   ├── validators.py       # username / email / name
│   ├── permissions.py      # IsNewsOwner
│   ├── pagination.py       # cursor paginations with different orderings
│   ├── shortcust.py        # generate_deep_link(): Firebase Dynamic Links
│   └── tests/              # APITestCase for auth, categories, news, profile
│
├── api_v2/                 # v2: polymorphic posts, GenericFK media, MPTT comments
│   ├── models/             # news (Publisher/User/CuratorNews), media, comments, reports, others
│   ├── serializers/        # importing/ (from admin), export/ (to other services), news, comments
│   ├── views/              # presigned upload, post update, comments
│   ├── signals/            # v2 comment and post sync
│   ├── tasks/              # PublisherNews/UserNews/CuratorNews import
│   ├── storages.py         # an S3 bucket per media type
│   └── tests/              # pytest + factory_boy
│
├── segments.py             # one-off script: creates OneSignal segments from the category tree
├── requirements/           # base / develop / prod
├── Dockerfile*             # web / celery / post_sync
├── docker-compose.yaml
├── entrypoint.sh, celery.sh, celery_post_sync.sh
└── bitbucket-pipelines.yml
```

## Django apps

| App | Responsibility |
|---|---|
| `column` | Project config and **inbound** Celery tasks from other services (admin → app) |
| `api` | Users, profiles, follows, auth, v1 posts (`ColumnNews`), reports, blocks, creators, sports events |
| `api_v2` | New content model: `PublisherNews`, `UserNews`, `CuratorNews`, media, comment tree, reports |

## Where to find things

| Task | File |
|---|---|
| Add an endpoint | `api/urls.py` / `api_v2/urls.py` + the matching `views/*.py` |
| Change the profile payload | `api/serializers/profile.py`, `api/versioned/v2/serializers.py` |
| Registration / JWT claims logic | `api/serializers/auth.py`, `api/views/auth.py` |
| What is sent to the admin when a model changes | `api/signals.py`, `api_v2/signals/*.py` |
| How data from the admin is processed | `column/tasks.py`, `api_v2/tasks/news.py`, serializers `api/serializers/tasks.py`, `api_v2/serializers/importing/` |
| S3 key layout | `api_v2/models/media.py` (`*_name` functions), `api/views/upload.py` |
| Periodic jobs | `api/cron.py` + `CRONJOBS` in `column/settings.py` |
| Password validation | `column/password_validation.py` + `AUTH_PASSWORD_VALIDATORS` |
| Error messages | `api/errors.py` |

## Conventions

- **`global_id` (UUID)** is the public identifier in URLs and inter-service messages. `id` is internal only.
- **Celery task names are set explicitly** (`name="column.tasks.xxx"`) because other services call them by string name through
  `send_task`. Renaming a task breaks the contract between services.
- **The `_is_external` flag** on a model instance means "saved from another service's data". Signals must not send such data back,
  which prevents sync loops.
- **`_synced_from_new_architecture`** is the same kind of flag for `ColumnNews` rows created during v2 sync.
- Inter-service serializers are kept separate: `serializers/tasks.py` and `serializers/importing/` handle inbound data,
  `serializers/signals.py` and `serializers/export/` handle outbound data.
