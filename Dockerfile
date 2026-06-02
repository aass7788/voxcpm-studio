FROM nvidia/cuda:12.4-runtime-ubuntu22.04

ENV PYTHONUNBUFFERED=1 DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 python3.12-venv python3.12-dev python3-pip \
    libsndfile1 ffmpeg curl tini && \
    rm -rf /var/lib/apt/lists/* && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 && \
    python -m pip install --upgrade pip

RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -d /app appuser

WORKDIR /app

# Install PyTorch for CUDA
RUN pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124

# Install voxcpm from local source
COPY VoxCPM/ ./VoxCPM/
RUN pip install -e ./VoxCPM/

# Install app dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy app code
COPY *.py ./
COPY static/ ./static/
COPY entrypoint.sh ./

RUN mkdir -p data output uploads && \
    chown -R appuser:appuser /app && \
    chmod +x entrypoint.sh

USER appuser
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "from urllib.request import urlopen; urlopen('http://localhost:5000/')" || exit 1

ENTRYPOINT ["/usr/bin/tini", "--", "./entrypoint.sh"]
