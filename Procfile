web: cd src && python manage.py migrate --noinput && waitress-serve --port=$PORT config.wsgi:application
celery-beat: cd src && celery -A config.celery beat -l INFO
celery-worker: cd src && celery -A config.celery worker -l INFO
