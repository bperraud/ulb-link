#!/bin/bash

#echo "Waiting for postgres"
#while ! nc -z "$DATABASE_HOST" "$DATABASE_PORT" ; do
#  sleep 0.1
#done

echo "Postgres started"

echo "Making migrations and migrating the database"
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "Collecting statics"
python manage.py collectstatic --noinput

## required for docker to continue
exec "$@"

