#!/bin/sh
# Start Gunicorn for production
exec gunicorn api.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --log-level info
  