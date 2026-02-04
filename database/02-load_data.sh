#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
sleep 5

# run the load data script
echo "Starting data loading process..."
cd /docker-entrypoint-initdb.d/
python3 load_data.py || echo "Data loading failed but continuing..."
echo "Data loading script completed"
