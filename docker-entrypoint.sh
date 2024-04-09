#!/bin/bash
set -e

if [ -n "$DATABASE_HOST" ]; then
  until nc -z -v -w30 "$DATABASE_HOST" 5432
  do
    _log "Waiting for postgres database connection..."
    sleep 1
  done
  _log "Database is up!"
fi

if [[ "$APPLY_MIGRATIONS" = "true" ]]; then
    echo "Applying database migrations..."
    ./manage.py migrate --noinput
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

