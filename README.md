# VoxCPM Studio — AI 多语言配音工坊

文本输入、选声音，一键生成多语言语音。

## 环境要求

| 项目 | 最低要求 |
|------|---------|
| Python | 3.10+ |
| GPU | NVIDIA 显卡，建议 8GB+ 显存 |
| CUDA | 12.4 |
| 系统 | Windows 10+ / Linux (Ubuntu 22.04) |

## 快速开始（新电脑）

### 1. 安装基础工具

- **Python 3.10+**：https://www.python.org/downloads/ （安装时勾选 "Add Python to PATH"）
- **Git**：https://git-scm.com/download/win
- **CUDA 12.4**（NVIDIA 显卡）：https://developer.nvidia.com/cuda-12-4-download-archive
  - 没 NVIDIA 显卡可以跳过，会自动用 CPU 推理（慢很多）

### 2. 克隆项目

```bash
git clone --recursive https://github.com/aass7788/voxcpm-studio.git
cd voxcpm-studio
```

> 注意：必须加 `--recursive`，VoxCPM 是 git 子模块。

### 3. 安装

```bash
# 修复 setuptools_scm 版本检测（子模块没有 git 元数据）
sed -i 's/dynamic = \["version"\]/version = "0.1.0"/' VoxCPM/pyproject.toml

# GPU 版（推荐）
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124

# CPU 版（无 NVIDIA 显卡时用）
# pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

pip install -e VoxCPM/
pip install -r requirements.txt
```

### 4. 启动

**桌面应用（Windows）：**

```bash
python desktop_app.py
```

打开一个独立窗口，开箱即用。

**Web 服务（Linux 服务器）：**

```bash
uvicorn app:app --host 0.0.0.0 --port 5000
```

浏览器打开 `http://localhost:5000`。

**Docker 部署（需要 GPU 服务器）：**

```bash
docker compose up -d
```

## 打包为 exe（Windows）

```bash
pyinstaller voxcpm_studio.spec --distpath ./dist --workpath ./build --noconfirm
```

输出在 `dist/VoxCPM_Studio/`，整个文件夹复制给别人就能用。

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/tts/generate` | 文本转语音 |
| POST | `/api/tts/clone` | 声音克隆（需上传参考音频） |
| GET | `/api/tts/presets` | 预设音色列表 |
| GET | `/api/tts/history` | 合成历史 |
| GET | `/api/tts/audio/{id}` | 播放/下载音频 |
| DELETE | `/api/tts/history/{id}` | 删除记录 |

## 项目结构

```
voxcpm-studio/
├── app.py              # FastAPI 服务端
├── desktop_app.py      # 桌面应用入口（pywebview）
├── tts_engine.py       # VoxCPM 引擎封装
├── models.py           # SQLite 数据库
├── static/             # 前端 (Vue 3 SPA)
├── VoxCPM/             # VoxCPM 模型（git 子模块）
├── voxcpm_studio.spec  # PyInstaller 打包配置
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
