#!/bin/bash

set -euxo pipefail

proc_type="${PROCESS_TYPE:-web}"

if [ "$proc_type" == "web" ]; then
    echo "starting web server..."
    python manage.py migrate --noinput && python manage.py collectstatic --noinput && waitress-serve --port=$PORT config.wsgi:application
else
    echo "starting celery server..."
    celery -A config worker -l info
fi
