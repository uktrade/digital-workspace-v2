web: cd src && python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py update_index_async && opentelemetry-instrument granian --interface wsgi config.wsgi:application --workers 2 --host 0.0.0.0 --port=$PORT 
beat: cd src && celery -A config.celery beat -l INFO
worker: cd src && celery -A config.celery worker -l INFO
