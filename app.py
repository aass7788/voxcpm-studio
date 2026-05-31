import os
import uuid
import asyncio
import logging
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import soundfile as sf
import schedule
import threading

from tts_engine import get_engine
from models import init_db, save_record, get_history, get_record, delete_record, cleanup_old_records

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

MODEL_ID = os.environ.get("VOXCPM_MODEL_ID", "openbmb/VoxCPM2")
DEVICE = os.environ.get("VOXCPM_DEVICE", "auto")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="VoxCPM Studio", version="1.0.0")

engine = get_engine(model_id=MODEL_ID, device=DEVICE)


@app.on_event("startup")
def startup():
    init_db()
    logger.info(f"VoxCPM Studio starting, model={MODEL_ID}, device={DEVICE}")

    def _schedule():
        schedule.every().day.at("03:00").do(cleanup_old_records, hours=24)
        while True:
            schedule.run_pending()
            import time
            time.sleep(60)

    t = threading.Thread(target=_schedule, daemon=True)
    t.start()


@app.get("/", response_class=HTMLResponse)
def index():
    path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(path):
        return HTMLResponse(open(path, encoding="utf-8").read())
    return HTMLResponse("<h1>VoxCPM Studio</h1>")


@app.post("/api/tts/generate")
async def api_generate(
    text: str = Form(...),
    control: str = Form(""),
    cfg_value: float = Form(2.0),
    timesteps: int = Form(10),
    normalize: bool = Form(False),
):
    text = text.strip()
    if not text:
        raise HTTPException(400, "请输入文本")
    if len(text) > 2000:
        raise HTTPException(400, "文本过长，最多2000字")
    if not (0.5 <= cfg_value <= 5.0):
        raise HTTPException(400, "CFG 范围 0.5-5.0")
    if not (1 <= timesteps <= 50):
        raise HTTPException(400, "步数范围 1-50")

    result = await engine.generate(
        text=text, control=control,
        cfg_value=cfg_value, timesteps=timesteps, normalize=normalize,
    )
    rid = uuid.uuid4().hex[:12]
    params = str({"cfg": cfg_value, "timesteps": timesteps, "normalize": normalize, "control": control})
    save_record(rid, "generate", text, result["path"], duration=result["duration"], params=params)
    return {"id": rid, "audio_url": f"/api/tts/audio/{rid}", "duration": result["duration"]}


@app.post("/api/tts/clone")
async def api_clone(
    text: str = Form(...),
    audio: UploadFile = File(...),
    prompt_text: str = Form(""),
    denoise: bool = Form(True),
    cfg_value: float = Form(2.0),
    timesteps: int = Form(10),
    normalize: bool = Form(False),
):
    text = text.strip()
    if not text:
        raise HTTPException(400, "请输入文本")
    if len(text) > 2000:
        raise HTTPException(400, "文本过长，最多2000字")

    ref_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}.wav")
    content = await audio.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "音频文件不超过10MB")
    with open(ref_path, "wb") as f:
        f.write(content)

    result = await engine.clone(
        text=text, reference_audio=ref_path, prompt_text=prompt_text,
        denoise=denoise, cfg_value=cfg_value, timesteps=timesteps, normalize=normalize,
    )
    rid = uuid.uuid4().hex[:12]
    params = str({"cfg": cfg_value, "timesteps": timesteps, "denoise": denoise})
    save_record(rid, "clone", text, result["path"], duration=result["duration"],
                reference_audio=ref_path, params=params)
    return {"id": rid, "audio_url": f"/api/tts/audio/{rid}", "duration": result["duration"]}


@app.get("/api/tts/presets")
def api_presets():
    return {
        "presets": [
            {"id": "zh_female_warm", "name": "中文女声 - 温柔", "lang": "zh", "gender": "female"},
            {"id": "zh_male_calm", "name": "中文男声 - 沉稳", "lang": "zh", "gender": "male"},
            {"id": "en_female_natural", "name": "English Female - Natural", "lang": "en", "gender": "female"},
            {"id": "en_male_deep", "name": "English Male - Deep", "lang": "en", "gender": "male"},
            {"id": "ja_female_soft", "name": "日本語女性 - 柔らかい", "lang": "ja", "gender": "female"},
            {"id": "ko_female_clear", "name": "한국어 여성 - 맑음", "lang": "ko", "gender": "female"},
        ]
    }


@app.get("/api/tts/history")
def api_history(page: int = 1, per_page: int = 20):
    return get_history(page=page, per_page=per_page)


@app.delete("/api/tts/history/{rid}")
def api_delete_history(rid: str):
    rec = get_record(rid)
    if not rec:
        raise HTTPException(404, "记录不存在")
    if os.path.exists(rec["output_audio"]):
        os.remove(rec["output_audio"])
    delete_record(rid)
    return {"ok": True}


@app.get("/api/tts/audio/{rid}")
def api_audio(rid: str):
    rec = get_record(rid)
    if not rec:
        raise HTTPException(404, "记录不存在")
    path = rec["output_audio"]
    if not os.path.exists(path):
        raise HTTPException(404, "音频文件已过期")
    return FileResponse(path, media_type="audio/wav")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
