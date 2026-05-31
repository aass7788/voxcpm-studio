#!/bin/sh
set -e

python -c "from models import init_db; init_db()"

exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-5000} --workers 1 --timeout-keep-alive 300
