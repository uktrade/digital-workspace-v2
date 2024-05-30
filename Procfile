web: cd src && python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py update_index_async && opentelemetry-instrument waitress-serve --port=$PORT --threads=6 config.wsgi:application
beat: cd src && celery -A config.celery beat -l INFO
worker: cd src && celery -A config.celery worker -l INFO
