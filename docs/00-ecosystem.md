# 0. Ecosystem Overview

[← Contents](README.md)

This repository is one part of **Vylo** (internal code name **Column**). Vylo is a sports-focused social mobile app. It has a news feed from
publishers, video and audio posts from users, comments and replies, and follows for authors and categories. It also has a DFS module
called **Vylo Props**: over/under picks on player stats, lineups, balances, promo codes and Creator Cash.

## Services

| Service | Repository | Role | Stack |
|---|---|---|---|
| **Content API** | `content-api` | Mobile app backend: auth, profiles, follows, user posts, comments, media upload | Django 3.2, DRF, Celery, PostgreSQL, S3 |
| **Admin API** | `column-admin-api` | Admin backend: content moderation, news publishing, AI moderation (Hive), scrapers, odds, Vylo Props mirror | Django 3.2, DRF, Celery, PostgreSQL, S3 |
| **Vylo Admin** | `column-admin` | Admin web SPA on top of the Admin API | React 18, TypeScript, Vite, TanStack Query |
| Feed service* | — | Builds user feeds | — |
| Events / Scoring service* | — | Events, post scores, push notifications | — |
| vylo-bets* | — | Vylo Props engine: props, lineups, balances, payments | — |
| VyloGPT* | — | AI predictions for sports events | — |

`*` These services live in other repositories. What we know about them comes only from the task names and queues that the three repositories above send to.

## High-level architecture

The services do not call each other over HTTP. They exchange events through **RabbitMQ using Celery**
(`app.send_task('<task name>', queue='<queue>')`). Each service has its own PostgreSQL database and keeps a local copy of the
entities it needs (profiles, categories, posts). Tasks keep those copies in sync.

```mermaid
flowchart LR
    Mobile["📱 Mobile app<br/>(iOS / Android)"] -->|REST + JWT| Content["Content API"]
    AdminUI["🖥 Vylo Admin"] -->|REST + JWT| Admin["Admin API"]

    Content <-->|Celery / RabbitMQ| MQ[(RabbitMQ)]
    Admin <-->|Celery / RabbitMQ| MQ
    MQ <--> Feed["Feed service*"]
    MQ <--> Events["Events / Scoring service*"]
    MQ <--> Bets["vylo-bets*"]
    MQ <--> GPT["VyloGPT*"]

    Content --> S3[(AWS S3 + CDN)]
    Admin --> S3
    Admin --> Hive["Hive AI moderation"]
    Admin --> Odds["The Odds API / OpticOdds"]
    Admin --> Ensemble["EnsembleData<br/>(Instagram / TikTok)"]
    Content --> OneSignal["OneSignal push"]
    Content --> Firebase["Firebase Dynamic Links"]
```

## Main RabbitMQ queues

| Queue | Consumer | Purpose |
|---|---|---|
| `app` | Content API | Import news, categories and profiles from the admin into the app |
| `post_sync_column` | Content API (dedicated worker) | Post synchronization into Content API |
| `admin` | Admin API | Regular admin tasks: reports, scores, comments, Vylo Props sync |
| `post_sync_admin` | Admin API (dedicated worker) | Receives new user posts from Content API for moderation |
| `feed`, `post_sync_feed` | Feed service | Feed building |
| `events`, `post_sync_events` | Events service | Events, scoring, push notifications |
| `lineup_priority` | vylo-bets | Lineup data requests for posts |
| `vylo-bets`, `admin_to_main_tasks` | vylo-bets | Sends admin changes (balance, picks, restrictions) back to vylo-bets |
| `vylogpt` | VyloGPT | Prediction generation for sports events |

## End-to-end: lifecycle of a user post

```mermaid
sequenceDiagram
    participant App as Mobile app
    participant C as Content API
    participant S3 as S3
    participant A as Admin API
    participant H as Hive AI
    participant F as Feed / Events

    App->>C: GET /api_v2/generate_presigned_url/
    C-->>App: presigned URLs (content + thumbnail)
    App->>S3: PUT video/audio
    App->>C: PUT /api_v2/news_update/{id}/ (title, category, status)
    C->>A: column.tasks.move2approve (post_sync_admin)
    A->>A: CollectedNews (INBOUND)
    A->>H: /api/v2/task/sync
    H-->>A: classes + scores
    alt content is clean
        A->>A: status PUBLISHED
        A->>F: move2feed / move2events
        A->>C: move2content (update in the app)
    else violation
        A->>A: status AIREPORTED → manual review in Vylo Admin
    end
```

## Environments

| Branch | Environment |
|---|---|
| `develop` | Dev |
| `staging` / `aws-staging` | Staging |
| `master` | Production |

## Shared local infrastructure

The backends expect PostgreSQL and RabbitMQ on an external Docker network called `backend`. A minimal compose file for local development:

```yaml
# docker-compose.infra.yaml — local development only
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: <user>
      POSTGRES_PASSWORD: <password>
    ports: ["5432:5432"]
    networks: [backend]
  rabbitmq:
    image: rabbitmq:3-management
    environment:
      RABBITMQ_DEFAULT_USER: <user>
      RABBITMQ_DEFAULT_PASS: <password>
      RABBITMQ_DEFAULT_VHOST: <vhost>
    ports: ["5672:5672", "15672:15672"]   # AMQP, management UI
    networks: [backend]
networks:
  backend:
    external: true
```

```sh
docker network create backend
docker compose -f docker-compose.infra.yaml up -d
```
