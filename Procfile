web: cd src && python manage.py migrate --noinput && python manage.py collectstatic --noinput && waitress-serve --port=$PORT config.wsgi:application
worker: cd src && celery -A config worker -l info
