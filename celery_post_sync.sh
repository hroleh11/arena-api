#!/bin/bash

# Спеціалізований Celery воркер для синхронізації постів - column-api

echo "🚀 Starting POST_SYNC worker for column-api in Docker..."

# Створюємо директорію для логів
mkdir -p /usr/src/app/logs

# Запускаємо Celery воркер тільки для черги post_sync_column
exec celery -A column worker \
    -Q post_sync_column \
    --loglevel=info \
    --concurrency=4
