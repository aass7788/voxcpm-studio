#!/bin/sh
set -e

echo "VoxCPM Studio — 初始化数据库..."
python3 -c "from models import init_db; init_db()"

echo "VoxCPM Studio — 启动服务 (端口 ${PORT:-5000})..."
exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-5000} --workers 1 --timeout-keep-alive 300
