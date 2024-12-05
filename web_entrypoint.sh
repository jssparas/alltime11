#!/bin/sh
python manage.py migrate
gunicorn -b 0.0.0.0:8000 alltime11.wsgi --workers=4
