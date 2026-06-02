FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV PYTHONUNBUFFERED=1 DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-dev python3-pip \
    libsndfile1 ffmpeg curl tini && \
    rm -rf /var/lib/apt/lists/* && \
    python3 -m pip install --upgrade pip

# 非 root 用户
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -d /app appuser

WORKDIR /app

# 构建工具
RUN python3 -m pip install setuptools setuptools_scm wheel

# PyTorch (CUDA)
RUN python3 -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124

# VoxCPM — 用 sed 替换动态版本为静态，避开 setuptools_scm 需要 git 的问题
COPY VoxCPM/ ./VoxCPM/
RUN sed -i 's/dynamic = \["version"\]/version = "0.1.0"/' ./VoxCPM/pyproject.toml && \
    python3 -m pip install --no-deps -e ./VoxCPM/

# 应用依赖
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt

# 应用代码
COPY *.py ./
COPY static/ ./static/
COPY entrypoint.sh ./

RUN mkdir -p data output uploads && \
    chown -R appuser:appuser /app && \
    chmod +x entrypoint.sh

USER appuser
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python3 -c "from urllib.request import urlopen; urlopen('http://localhost:5000/')" || exit 1

ENTRYPOINT ["/usr/bin/tini", "--", "./entrypoint.sh"]
