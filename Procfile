web: python src/manage.py migrate --noinput && python src/manage.py collectstatic --noinput && waitress-serve --port=$PORT config.wsgi:application
worker: celery -A config worker -l info
