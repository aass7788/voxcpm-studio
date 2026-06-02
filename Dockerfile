FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV PYTHONUNBUFFERED=1 DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-dev python3-pip \
    libsndfile1 ffmpeg curl tini && \
    rm -rf /var/lib/apt/lists/* && \
    python3 -m pip install --upgrade pip

RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -d /app appuser

WORKDIR /app

# 1. PyTorch (CUDA)
RUN python3 -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124

# 2. VoxCPM (仅装包本身，依赖后面统一装)
# setuptools_scm 需要版本号，Docker 里没有 .git 目录
COPY VoxCPM/ ./VoxCPM/
RUN SETUPTOOLS_SCM_PRETEND_VERSION_FOR_VOXCPM=0.1.0 \
    python3 -m pip install --no-deps -e ./VoxCPM/

# 3. 合并安装所有依赖
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt

# 4. 应用代码
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
