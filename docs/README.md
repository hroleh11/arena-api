# Content API — Documentation

**Content API** (Django project `column`) is the backend of the **Vylo** mobile app. It covers everything an end user sees and does:
sign-up and login, the profile, follows, their own video and audio posts, comments, reports and blocking.

## Contents

| # | Section | What's inside |
|---|---|---|
| 0 | [Ecosystem overview](00-ecosystem.md) | All Vylo services, how they talk to each other, queues, shared infra |
| 1 | [Product overview](01-product.md) | What the app does from a user's point of view, roles, key flows |
| 2 | [Architecture](02-architecture.md) | Place in the ecosystem, application layers, data flows |
| 3 | [Codebase structure](03-codebase.md) | Django apps, modules, where to find things |
| 4 | [Data model](04-data-model.md) | Entities, relations, statuses |
| 5 | [REST API](05-api.md) | Endpoints, auth, pagination, versioning |
| 6 | [Async tasks & integrations](06-async-and-integrations.md) | Celery tasks, signals, queues, external services |
| 7 | [Setup, configuration, deployment](07-setup-and-deployment.md) | Environment variables, Docker, CI/CD, tests |
| 8 | [Technical decisions & tech debt](08-decisions-and-tech-debt.md) | Why things are built this way, known issues |

## At a glance

| | |
|---|---|
| **Language / framework** | Python 3.9, Django 3.2, Django REST Framework 3.12 |
| **Database** | PostgreSQL (in-memory SQLite for tests) |
| **Async** | Celery 5 + RabbitMQ, `django-crontab` for periodic jobs |
| **Auth** | JWT (`djangorestframework-simplejwt`) + `djoser` + `social-auth` (Google, Facebook, Apple) |
| **Files** | AWS S3 (`django-storages`), served through a CDN, uploaded directly by clients via presigned URLs |
| **Push** | OneSignal |
| **API docs** | Swagger `/swagger/`, ReDoc `/redoc/` (drf-yasg) |

## Quick start

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# create .environment — see section 7 for the variable list
python manage.py migrate
python manage.py runserver      # http://127.0.0.1:8000/swagger/
```
