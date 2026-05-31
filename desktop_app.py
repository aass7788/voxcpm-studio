"""VoxCPM Studio — 桌面应用入口"""
import os
import sys
import threading
import time
import socket

import webview
import uvicorn

from models import init_db
from tts_engine import get_engine

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
HOST = "127.0.0.1"
PORT = 15000


def find_free_port():
    for p in range(PORT, PORT + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((HOST, p)) != 0:
                return p
    return PORT


def run_server(port):
    sys.argv = [sys.argv[0]]
    uvicorn.run("app:app", host=HOST, port=port, log_level="warning")


def main():
    os.makedirs("data", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    init_db()

    port = find_free_port()

    t = threading.Thread(target=run_server, args=(port,), daemon=True)
    t.start()

    # 预热模型（后台加载，不阻塞窗口）
    print("Loading VoxCPM model in background...")
    threading.Thread(target=lambda: get_engine(), daemon=True).start()

    # 等待服务器就绪
    for _ in range(30):
        try:
            s = socket.create_connection((HOST, port), timeout=0.5)
            s.close()
            break
        except Exception:
            time.sleep(0.3)

    url = f"http://{HOST}:{port}"
    print(f"VoxCPM Studio 启动: {url}")

    webview.create_window(
        "VoxCPM Studio — AI 配音工坊",
        url,
        width=420,
        height=820,
        min_size=(380, 600),
        text_select=True,
    )
    webview.start()


if __name__ == "__main__":
    main()
