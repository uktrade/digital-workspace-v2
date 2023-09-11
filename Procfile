web: cd src && python manage.py migrate --noinput && python manage.py collectstatic --noinput && waitress-serve --port=$PORT config.wsgi:application
beat: cd src && celery -A config.celery beat -l INFO
worker: cd src && celery -A config.celery worker -l INFO
