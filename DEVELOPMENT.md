# VoxCPM Studio — 开发设计文档

## 1. 技术栈

| 层 | 选型 | 原因 |
|----|------|------|
| 语音模型 | VoxCPM 2 | 多语言、声音克隆、API 简洁 |
| 后端 | Python 3.12 + FastAPI | 异步支持好、自动 OpenAPI 文档 |
| 前端 | Vue 3 (CDN) + 内联 SPA | 跟既有项目模式一致、零构建 |
| GPU 推理 | PyTorch CUDA | VoxCPM 依赖 |
| 部署 | Docker + docker-compose | 一键部署 |
| 任务队列 | 内置 asyncio Queue | MVP 阶段不引入 Redis/Celery |
| 存储 | 本地文件系统 + SQLite | 音频文件 + 合成记录 |

## 2. 系统架构

```
Browser (Vue SPA)
    │
    ▼
Nginx :8080 ──► FastAPI :5000 (async)
                     │
                     ├── POST /api/tts/generate    → VoxCPM.generate()
                     ├── POST /api/tts/clone       → VoxCPM.clone()
                     ├── GET  /api/tts/presets     → 预设音色列表
                     ├── GET  /api/tts/history     → 合成历史
                     ├── GET  /api/tts/audio/{id}  → 音频文件下载
                     └── DELETE /api/tts/history/{id} → 删除记录
                              │
                              ▼
                         VoxCPM 2 Model (GPU)
```

## 3. API 设计

### 3.1 文本转语音

```
POST /api/tts/generate
Content-Type: application/json

Request:
{
  "text": "Hello world, this is a test.",
  "preset": "zh_female_01",      // 预设音色 ID，或 null
  "speed": 1.0,                   // 语速 (0.5-2.0)，可选
  "cfg_value": 2.0,               // 引导强度 (1.0-5.0)，可选
  "timesteps": 10                 // 推理步数 (4-30)，可选
}

Response 200:
{
  "id": "abc123",
  "audio_url": "/api/tts/audio/abc123",
  "duration": 3.5,
  "text": "Hello world, this is a test.",
  "preset": "zh_female_01",
  "created_at": "2026-05-31T12:00:00"
}

Response 429 (队列满):
{
  "error": "当前排队人数较多，请稍后重试"
}
```

### 3.2 声音克隆

```
POST /api/tts/clone
Content-Type: multipart/form-data

Fields:
- audio: File (WAV/MP3, <30s, <10MB)
- text: String
- denoise: Boolean (默认 true)

Response 200:
{
  "id": "def456",
  "audio_url": "/api/tts/audio/def456",
  "duration": 4.2,
  "created_at": "..."
}
```

### 3.3 预设音色

```
GET /api/tts/presets

Response:
{
  "presets": [
    {"id": "zh_female_01", "name": "中文女声 - 温柔", "lang": "zh", "gender": "female"},
    {"id": "zh_male_01", "name": "中文男声 - 沉稳", "lang": "zh", "gender": "male"},
    {"id": "en_female_01", "name": "English Female - Natural", "lang": "en", "gender": "female"},
    ...
  ]
}
```

### 3.4 合成历史

```
GET /api/tts/history?page=1&per_page=20

Response:
{
  "items": [
    {
      "id": "abc123",
      "type": "generate" | "clone",
      "text": "...",
      "preset": "zh_female_01",
      "audio_url": "/api/tts/audio/abc123",
      "duration": 3.5,
      "created_at": "..."
    }
  ],
  "total": 45
}
```

## 4. 前端组件树

```
App
├── Header（标题 + 说明）
├── Main
│   ├── ModeSwitch（文本合成 / 声音克隆 Tab）
│   ├── TextInput（文本输入框，字数统计）
│   ├── PresetPicker（预设音色网格）
│   ├── CloneUploader（上传音频 + 预览）
│   ├── AdvancedOptions（可折叠：语速/强度/步数）
│   ├── GenerateButton（生成按钮 + 加载动画）
│   └── AudioPlayer（播放器 + 下载按钮 + 波形）
├── HistoryPanel（侧边栏/底部抽屉）
│   ├── HistoryItem × N（文字预览 + 时长 + 播放/下载/删除）
└── Footer
```

## 5. 数据库设计

SQLite，两张表：

```sql
CREATE TABLE tts_records (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,           -- 'generate' | 'clone'
    text TEXT NOT NULL,
    preset_id TEXT,
    reference_audio TEXT,         -- 克隆用参考音频路径
    output_audio TEXT NOT NULL,   -- 生成音频路径
    duration REAL,
    params TEXT,                   -- JSON: {speed, cfg_value, timesteps}
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE presets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    lang TEXT NOT NULL,
    gender TEXT,
    reference_audio TEXT NOT NULL, -- 预设参考音频路径
    description TEXT
);
```

## 6. 目录结构

```
voxcpm-app/
├── app.py              # FastAPI 入口 + 路由
├── tts_engine.py       # VoxCPM 模型加载 + 推理封装
├── models.py           # SQLite 数据库操作
├── presets/            # 预设参考音频文件
│   ├── zh_female_01.wav
│   └── ...
├── output/             # 生成的音频文件
├── static/             # 前端静态资源
│   ├── index.html      # Vue SPA
│   ├── css/
│   └── js/
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── requirements.txt
├── entrypoint.sh
├── .dockerignore
├── .github/workflows/ci-cd.yml
├── REQUIREMENTS.md     # 需求文档
└── DEVELOPMENT.md      # 本文档
```

## 7. 关键实现细节

### 7.1 GPU 任务队列

```python
# tts_engine.py
import asyncio
from queue import Queue

class TTSEngine:
    def __init__(self):
        self.model = None           # 懒加载
        self._queue = asyncio.Queue(maxsize=10)

    async def generate(self, text, **params):
        # 放入队列，等待 GPU 空闲
        future = asyncio.Future()
        await self._queue.put((future, text, params))
        self._process_queue()
        return await future
```

### 7.2 音频清理

每天凌晨清理超过 24h 的音频文件：

```python
import schedule
schedule.every().day.at("03:00").do(cleanup_old_audio)
```

### 7.3 预设音色 MVP 方案

不使用真实的声音克隆参考音频（那需要为每个 preset 准备高质量录音），而是用 VoxCPM 2 的零样本文本生成能力，通过调整 `cfg_value` 和 seed 来产生不同的声音质感。后续迭代再录制真实参考音频。
