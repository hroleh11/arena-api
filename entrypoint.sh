#! /bin/bash

python manage.py makemigrations --no-input

python manage.py migrate --no-input

python manage.py collectstatic --noinput

python manage.py crontab add

exec gunicorn column.wsgi:application -w 3 -b 0.0.0.0:8000 --reload