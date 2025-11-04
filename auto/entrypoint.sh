#!/bin/bash
set -e

python manage.py migrate --check
status=$?
if [[ $status != 0 ]]; then
    python manage.py migrate --noinput
fi

python manage.py collectstatic --noinput

exec "$@"
