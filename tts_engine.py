import os
import re
import time
import uuid
import asyncio
import logging
import numpy as np
from typing import Optional

import soundfile as sf
from voxcpm import VoxCPM
from voxcpm.model.utils import resolve_runtime_device

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tts_engine")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


class TTSEngine:
    def __init__(self, model_id: str = "openbmb/VoxCPM2", device: str = "auto"):
        self.model_id = model_id
        self.device = resolve_runtime_device(device, "cuda")
        self._model: Optional[VoxCPM] = None
        self._queue = asyncio.Queue(maxsize=10)
        self._task = asyncio.ensure_future(self._worker())
        logger.info(f"TTSEngine init, device={self.device}")

    @property
    def model(self) -> VoxCPM:
        if self._model is None:
            logger.info(f"Loading model: {self.model_id}")
            self._model = VoxCPM.from_pretrained(
                self.model_id,
                optimize=self.device.startswith("cuda"),
                device=self.device,
            )
            logger.info("Model loaded")
        return self._model

    async def _worker(self):
        while True:
            future, text, kwargs = await self._queue.get()
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, self._generate_sync, text, kwargs
                )
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)

    def _generate_sync(self, text: str, kwargs: dict) -> dict:
        m = self.model
        wav = m.generate(**kwargs)
        sample_rate = m.tts_model.sample_rate
        filename = f"{uuid.uuid4().hex}.wav"
        path = os.path.join(OUTPUT_DIR, filename)
        sf.write(path, wav, sample_rate)
        duration = round(len(wav) / sample_rate, 2)
        return {"path": path, "duration": duration, "sample_rate": sample_rate}

    async def generate(self, text: str, control: str = "", cfg_value: float = 2.0,
                       timesteps: int = 10, normalize: bool = False) -> dict:
        control = re.sub(r"[()（）]", "", (control or "").strip()).strip()
        final_text = f"({control}){text}" if control else text
        kwargs = dict(text=final_text, cfg_value=float(cfg_value),
                      inference_timesteps=int(timesteps), normalize=normalize)
        future = asyncio.Future()
        await self._queue.put((future, text, kwargs))
        return await future

    async def clone(self, text: str, reference_audio: str, prompt_text: str = "",
                    denoise: bool = True, cfg_value: float = 2.0,
                    timesteps: int = 10, normalize: bool = False) -> dict:
        kwargs = dict(text=text, reference_wav_path=reference_audio,
                      cfg_value=float(cfg_value), inference_timesteps=int(timesteps),
                      normalize=normalize, denoise=denoise)
        if prompt_text and prompt_text.strip():
            kwargs["prompt_wav_path"] = reference_audio
            kwargs["prompt_text"] = prompt_text.strip()
        future = asyncio.Future()
        await self._queue.put((future, text, kwargs))
        return await future


_engine: Optional[TTSEngine] = None


def get_engine(model_id: str = "openbmb/VoxCPM2", device: str = "auto") -> TTSEngine:
    global _engine
    if _engine is None:
        _engine = TTSEngine(model_id=model_id, device=device)
    return _engine
