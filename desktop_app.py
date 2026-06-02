"""VoxCPM Studio — 桌面应用入口"""
import os
import sys

# PyInstaller bundle DLL paths
if getattr(sys, 'frozen', False):
    _base = os.path.dirname(sys.executable)
    _internal = os.path.join(_base, '_internal')
    if os.path.isdir(_internal):
        os.add_dll_directory(_internal)
        os.add_dll_directory(os.path.join(_internal, 'torch', 'lib'))
        # Also add system CUDA path if present
        cuda_path = os.environ.get('CUDA_PATH') or 'C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.4'
        if os.path.isdir(os.path.join(cuda_path, 'bin')):
            os.add_dll_directory(os.path.join(cuda_path, 'bin'))
    sys.path.insert(0, _internal)

import threading
import time
import socket

import webview
import uvicorn
import requests

from models import init_db
from app import app as fastapi_app

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
    uvicorn.run(fastapi_app, host=HOST, port=port, log_level="warning")


def main():
    os.makedirs("data", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    init_db()

    port = find_free_port()

    t = threading.Thread(target=run_server, args=(port,), daemon=True)
    t.start()

    # 等待服务器就绪（引擎已懒加载，app 导入很快，最多等 30 秒）
    for _ in range(100):
        try:
            s = socket.create_connection((HOST, port), timeout=0.5)
            s.close()
            break
        except Exception:
            time.sleep(0.3)
    else:
        print("WARNING: Server did not start, but continuing anyway...")
    print(f"VoxCPM Studio 启动: http://{HOST}:{port}")

    class Api:
        def save_file(self, url, filename):
            result = webview.windows[0].create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=filename,
                file_types=("WAV 音频 (*.wav)",),
            )
            path = result[0] if isinstance(result, tuple) else result
            if path:
                r = requests.get(url)
                with open(path, "wb") as f:
                    f.write(r.content)
                print(f"Saved: {path}")

    url = f"http://{HOST}:{port}"

    window = webview.create_window(
        "VoxCPM Studio — AI 配音工坊",
        url,
        width=420,
        height=820,
        min_size=(380, 600),
        text_select=True,
        js_api=Api(),
    )
    webview.start()


if __name__ == "__main__":
    main()
