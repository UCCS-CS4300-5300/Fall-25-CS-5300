@echo off
cd /d "%~dp0"
python manage.py test
coverage run --source=. manage.py test
coverage report --include="*merge_stats_models.py,*token_usage_models.py,*views.py"
