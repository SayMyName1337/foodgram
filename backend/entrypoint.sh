#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py load_json /app/data/ingredients.json

exec gunicorn --bind 0.0.0.0:8000 foodgram_backend.wsgi
