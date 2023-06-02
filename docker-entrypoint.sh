#!/bin/bash
set -e
if [[ "$APPLY_MIGRATIONS" = "true" ]]; then
    echo "Applying database migrations..."
    ./manage.py migrate --noinput
fi


if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
    echo "Creating superuser if it does not exists."
    python manage.py ensure_adminuser --username $DJANGO_SUPERUSER_USERNAME \
        --email $DJANGO_SUPERUSER_EMAIL \
        --password $DJANGO_SUPERUSER_PASSWORD
fi

if [ "$1" = 'start_django_development_server' ]; then
    # Start django develpoment server
    echo "Starting development server."
    ./manage.py runserver 0.0.0.0:8000
elif [ "$1" = 'import_questions' ]; then
    echo "Importing questions..."
    ./manage.py import_questions
elif [ "$1" = 'start_production_server' ]; then
    echo "Starting production server..."
    exec uwsgi --ini deploy/docker_uwsgi.ini
fi

