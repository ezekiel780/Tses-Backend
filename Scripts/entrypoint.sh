#!/bin/bash
set -e

# Run migrations and collect static files (non-interactive)
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# If an explicit command was provided, run it; otherwise start gunicorn
if [ "$1" != "" ]; then
  exec "$@"
else
  exec /Scripts/gunicorn_start.sh
fi
