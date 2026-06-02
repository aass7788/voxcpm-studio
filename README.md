# VoxCPM Studio — AI 多语言配音工坊

文本输入、选声音，一键生成多语言语音。

## 环境要求

| 项目 | 最低要求 |
|------|---------|
| Python | 3.10+ |
| GPU | NVIDIA 显卡，建议 8GB+ 显存 |
| CUDA | 12.4 |
| 系统 | Windows 10+ / Linux (Ubuntu 22.04) |

## 快速开始

### 1. 安装基础工具

- **Python 3.10+**：https://www.python.org/downloads/ （勾选 "Add Python to PATH"）
- **Git**：https://git-scm.com/download/win
- **CUDA 12.4**（NVIDIA 显卡）：https://developer.nvidia.com/cuda-12-4-download-archive

### 2. 克隆

```bash
git clone --recursive https://github.com/aass7788/voxcpm-studio.git
cd voxcpm-studio
```

### 3. 安装

```bash
sed -i 's/dynamic = \["version"\]/version = "0.1.0"/' VoxCPM/pyproject.toml

pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install -e VoxCPM/
pip install -r requirements.txt
```

### 4. 启动

```bash
python desktop_app.py
```
