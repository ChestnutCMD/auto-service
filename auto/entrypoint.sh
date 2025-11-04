#!/bin/bash

set -e

echo "=== Starting entrypoint script ==="

# Выводим отладочную информацию
echo "Environment variables:"
echo "DB_HOST: $DB_HOST"
echo "DB_PORT: $DB_PORT"
echo "DB_NAME: $DB_NAME"
echo "DB_USER: $DB_USER"

# Ожидание доступности PostgreSQL
echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
while ! nc -z $DB_HOST $DB_PORT; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "PostgreSQL is up - continuing"

# Проверяем подключение к БД
echo "Testing database connection..."
python << EOF
import os
import psycopg2
from psycopg2 import OperationalError

try:
    conn = psycopg2.connect(
        dbname=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        host=os.environ['DB_HOST'],
        port=os.environ['DB_PORT']
    )
    print("✅ Database connection successful!")
    conn.close()
except OperationalError as e:
    print(f"❌ Database connection failed: {e}")
    exit(1)
EOF

# Применение миграций
echo "Applying migrations..."
python manage.py migrate --noinput

# Сбор статики
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "=== Starting Gunicorn ==="
exec "$@"