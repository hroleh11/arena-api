# 7. Setup, Configuration, Deployment

[← Contents](README.md)

## Requirements

- Python 3.9
- PostgreSQL 13+ (the local compose uses 16)
- RabbitMQ 3
- An AWS account with S3 buckets (for media features)

## Local setup

```sh
# 1. Infra: PostgreSQL + RabbitMQ (compose example in 00-ecosystem.md)
docker network create backend
docker compose -f docker-compose.infra.yaml up -d

# 2. Python env
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # = requirements/develop.txt

# 3. Config
#    create .environment in the project root (read by django-environ)

# 4. DB + run
python manage.py migrate
python manage.py runserver

# 5. Workers (separate terminals)
celery -A column worker -Q app
celery -A column worker -Q post_sync_column --concurrency=4
```

## Environment variables (`.environment`)

| Group | Variables |
|---|---|
| Django | `DJANGO_DEBUG`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `LANGUAGE_CODE`, `TIME_ZONE`, `CORS_ALLOWED_ORIGINS` |
| PostgreSQL | `POSTGRESQL_DATABASE`, `POSTGRESQL_USER`, `POSTGRESQL_PASSWORD`, `POSTGRESQL_HOST`, `POSTGRESQL_PORT` |
| RabbitMQ | `RABBITMQ_URL` (`amqp://user:pass@host:5672/vhost`) |
| Email | `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_PORT`, `DEFAULT_FROM_EMAIL` |
| S3 | `AWS_S3_ACCESS_KEY_ID`, `AWS_S3_SECRET_ACCESS_KEY`, `AWS_S3_REGION_NAME`, `AWS_STORAGE_BUCKET_NAME`, `AWS_NEWS_STORAGE_BUCKET_NAME`, `AWS_VIDEO_UPLOAD_BUCKET`, `AWS_AUDIO_UPLOAD_BUCKET`, `AWS_VIDEO_UPLOAD_BUCKET_OPTIMIZED`, `AWS_AUDIO_UPLOAD_BUCKET_OPTIMIZED`, `AWS_QUERYSTRING_AUTH`, `AWS_S3_SECURE_URLS` |
| CDN | `AWS_S3_CUSTOM_DOMAIN`, `AWS_S3_AUDIOVIDEO_CUSTOM_DOMAIN` |
| Social auth | `SOCIAL_AUTH_FACEBOOK_KEY/SECRET`, `SOCIAL_AUTH_GOOGLE_OAUTH2_KEY/SECRET`, `SOCIAL_AUTH_APPLE_ID_CLIENT/TEAM/KEY/SECRET` |
| Mobile | `APPLE_ID_APP_STORE`, `APPLE_URL_APP_STORE`, `ANDROID_APP_VERSION`, `ANDROID_URL_GOOGLE_STORE`, `ANDROID_PACKAGE_NAME` |
| Links | `EXTERNAL_IDS_DOMAIN`, `FIREBASE_WEB_API_KEY`, `FIREBASE_URL_PREFIX`, `VYLO_URL`, `JOIN_LINK`, `PROJECT_NAME` |
| OneSignal | `ONE_SIGNAL_APP_ID`, `ONE_SIGNAL_APP_KEY`, `ONE_SIGNAL_USER_KEY` |
| Misc | `UNIVERSAL_CODES` (list), `PLATFORMS` (list) |

> `UNIVERSAL_CODES`, `PLATFORMS` and `ONE_SIGNAL_*` have **no defaults**. The app will not start without them.

## Docker

`docker-compose.yaml` runs three services on the external `backend` network, all reading `.environment`:

| Service | Dockerfile | Entry point |
|---|---|---|
| `web` (`:8000`) | `Dockerfile` | `entrypoint.sh`: makemigrations, migrate, collectstatic, crontab add, gunicorn (3 workers) |
| `celery` | `Dockerfile.celery` | `celery.sh` (queue `app`) |
| `celery_post_sync_column` | `Dockerfile.post_sync` | `celery_post_sync.sh` (queue `post_sync_column`, logs in `./logs`) |

All images: `python:3.9-slim`, venv in `/opt/venv`, run as non-root user `app`.

## CI/CD

`bitbucket-pipelines.yml` SSHes into the target host on push and runs `make deploy-api` there:

| Branch | Target |
|---|---|
| `develop` | `$COLUMN_DEV_HOST` |
| `staging` | `$COLUMN_STAGING_HOST` |
| `master` | `$COLUMN_PRD_HOST` |

The `Makefile` with `deploy-api` lives on the servers, not in this repo.

## Tests

```sh
pytest                       # uses DJANGO_SETTINGS_MODULE=column.settings (pytest.ini)
```

When run under pytest, the DB switches to in-memory SQLite automatically (`'pytest' in sys.argv[0]`).
- `api/tests/`: Django `APITestCase` (auth, categories, news, profile).
- `api_v2/tests/`: pytest + `factory_boy` factories (`api_v2/tests/factory/`).

Swagger UI is available at `/swagger/` once the server runs.
