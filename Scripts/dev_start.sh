#!/bin/sh
# Development start: run Django dev server
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
