#!/bin/bash

echo "Starting Gunicorn..."
exec gunicorn auto.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --access-logfile - \
    --error-logfile - \
    --log-level info