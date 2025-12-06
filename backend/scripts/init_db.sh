#!/bin/bash
# Initialize database and run migrations

echo "Creating initial migration..."
alembic revision --autogenerate -m "Initial migration"

echo "Applying migrations..."
alembic upgrade head

echo "Database initialized successfully!"

