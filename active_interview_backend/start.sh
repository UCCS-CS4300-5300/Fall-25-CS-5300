#!/bin/bash

python3 manage.py collectstatic --noinput;
#python3 manage.py makemigrations;
python3 manage.py migrate;

# Seed bias terms if not already loaded (idempotent - won't duplicate)
python3 manage.py seed_bias_terms;

gunicorn active_interview_project.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3
