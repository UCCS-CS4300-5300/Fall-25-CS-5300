web: cd active_interview_backend && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn active_interview_project.wsgi:application --bind 0.0.0.0:$PORT
