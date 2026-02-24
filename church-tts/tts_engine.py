# -*- coding: utf-8 -*-
"""
TTS 엔진: 샘플 목소리(Bark) + 목소리 클로닝(XTTS)
비상업적 사용 전제.
"""
from __future__ import annotations

import io
import os
import tempfile
from typing import Optional

# coqui-tts 호환: 최신 transformers에서 제거/이동된 API 대응 (TTS 로드 전에 실행)
def _patch_transformers():
    import transformers.utils.import_utils as _iu
    if not hasattr(_iu, "is_torch_greater_or_equal"):
        import torch as _torch
        def _parse_version(v):
            parts = []
            for x in str(v).replace("-", ".").split(".")[:3]:
                try:
                    parts.append(int(x))
                except ValueError:
                    parts.append(0)
            return tuple(parts + [0] * (3 - len(parts)))
        def is_torch_greater_or_equal(version_str, accept_dev=False):
            current = _parse_version(getattr(_torch, "__version__", "0.0.0"))
            target = _parse_version(version_str)
            return current >= target
        _iu.is_torch_greater_or_equal = is_torch_greater_or_equal
    if not hasattr(_iu, "is_torchcodec_available"):
        def is_torchcodec_available():
            return False
        _iu.is_torchcodec_available = is_torchcodec_available

    import transformers.pytorch_utils as _ptu
    if not hasattr(_ptu, "isin_mps_friendly"):
        import torch as _torch
        def isin_mps_friendly(elements, test_elements):
            return _torch.isin(elements, test_elements)
        _ptu.isin_mps_friendly = isin_mps_friendly

_patch_transformers()

import numpy as np
import soundfile as sf
import torch


# ----- 샘플 목소리 (Bark) -----
# Bark는 다국어 지원. 한국어 문장도 생성 가능. preset은 음색만 결정.
BARK_VOICE_PRESETS = [
    ("샘플 1 (차분한 남성)", "v2/en_speaker_0"),
    ("샘플 2 (밝은 여성)", "v2/en_speaker_1"),
    ("샘플 3 (안내 방송 스타일)", "v2/en_speaker_6"),
    ("샘플 4 (따뜻한 톤)", "v2/en_speaker_9"),
]


def get_bark_pipeline():
    from transformers import AutoProcessor, BarkModel
    device = "cuda" if torch.cuda.is_available() else "cpu"
    processor = AutoProcessor.from_pretrained("suno/bark")
    model = BarkModel.from_pretrained("suno/bark").to(device)
    return processor, model, device


def synthesize_bark(text: str, voice_preset: str, processor, model, device: str) -> bytes:
    """Bark로 TTS 생성, WAV bytes 반환."""
    inputs = processor(text=text, voice_preset=voice_preset, return_tensors="pt").to(device)
    with torch.no_grad():
        out = model.generate(**inputs)
    if isinstance(out, dict):
        arr = out.get("audio_values", out.get("waveform", out))  # fallback
    else:
        arr = out
    arr = arr.cpu().numpy() if torch.is_tensor(arr) else np.asarray(arr)
    arr = arr.squeeze()
    if arr.dtype != np.float32:
        arr = arr.astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, arr, 24000, format="WAV")
    buf.seek(0)
    return buf.read()


# ----- 목소리 클로닝 (XTTS) -----
def get_xtts_model():
    from TTS.api import TTS
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    return tts, device


def synthesize_xtts(
    text: str,
    speaker_wav_path: str,
    language: str = "ko",
    tts=None,
    device: str = "cpu",
) -> bytes:
    """XTTS로 목소리 클로닝 TTS, WAV bytes 반환."""
    if tts is None:
        tts, device = get_xtts_model()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        out_path = f.name
    try:
        tts.tts_to_file(
            text=text,
            file_path=out_path,
            speaker_wav=speaker_wav_path,
            language=language,
        )
        with open(out_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(out_path):
            os.unlink(out_path)


def ensure_wav_seconds(wav_path: str, min_seconds: float = 5.0, max_seconds: float = 15.0) -> Optional[str]:
    """
    WAV 길이 확인. XTTS는 6초 전후 참조를 권장.
    너무 짧으면 그대로, 너무 길면 앞부분만 잘라서 임시 파일로 저장 후 경로 반환.
    """
    data, sr = sf.read(wav_path)
    if len(data.shape) > 1:
        data = data.mean(axis=1)
    duration = len(data) / sr
    if duration < 1.0:
        return None
    if duration > max_seconds:
        n = int(sr * max_seconds)
        data = data[:n]
    path_out = wav_path
    if duration > max_seconds:
        fd, path_out = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        sf.write(path_out, data, sr)
    return path_out
