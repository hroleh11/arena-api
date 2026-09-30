# Vylo Content API

Backend of the **Vylo** mobile app (iOS / Android). It handles everything an end user sees and does: sign-up and social login,
profiles, follows, video and audio posts uploaded directly to S3, comments and replies, reports, blocks and push notifications.

It is the source of truth for users and their social graph. It receives editorial content and moderation decisions from the Admin API.
It talks to the other Vylo services only through **Celery tasks over RabbitMQ**.

> This repository is the Django project `column` (Content API).

## Tech stack

| | |
|---|---|
| Language / framework | Python 3.9, Django 3.2, Django REST Framework 3.12 |
| Database | PostgreSQL (in-memory SQLite for tests) |
| Async | Celery 5 + RabbitMQ, `django-crontab` |
| Auth | JWT (simplejwt) + djoser + social auth (Google, Facebook, Apple) |
| Storage | AWS S3 + CDN, presigned uploads |
| Integrations | OneSignal, Firebase Dynamic Links |
| API docs | Swagger `/swagger/`, ReDoc `/redoc/` |

## Quick start

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# create .environment — see docs/07-setup-and-deployment.md
python manage.py migrate
python manage.py runserver           # http://127.0.0.1:8000/swagger/

# workers
celery -A column worker -Q app
celery -A column worker -Q post_sync_column --concurrency=4
```

Or with Docker: `docker network create backend && docker compose up -d --build` (API on `:8000`).

## Documentation

| | |
|---|---|
| [0. Ecosystem overview](docs/00-ecosystem.md) | All Vylo services, queues, end-to-end post flow |
| [1. Product overview](docs/01-product.md) | Features from a user's point of view, roles |
| [2. Architecture](docs/02-architecture.md) | Processes, layers, data flows |
| [3. Codebase structure](docs/03-codebase.md) | Django apps and where to find things |
| [4. Data model](docs/04-data-model.md) | Entities, relations, statuses |
| [5. REST API](docs/05-api.md) | Endpoints, auth, pagination, versioning |
| [6. Async tasks & integrations](docs/06-async-and-integrations.md) | Celery tasks, signals, cron, external services |
| [7. Setup, configuration, deployment](docs/07-setup-and-deployment.md) | Env vars, Docker, CI/CD, tests |
| [8. Technical decisions & tech debt](docs/08-decisions-and-tech-debt.md) | Rationale and known issues |
