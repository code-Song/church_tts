# -*- coding: utf-8 -*-
"""이미 요약한 영상 ID 저장 (JSON 파일 → git에 커밋해서 영구 보존)."""
import json
import datetime
from pathlib import Path

from config import BASE_DIR

SEEN_PATH = BASE_DIR / "seen_videos.json"


def _load() -> dict:
    if SEEN_PATH.exists():
        try:
            return json.loads(SEEN_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(data: dict):
    SEEN_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def is_seen(video_id: str) -> bool:
    return video_id in _load()


def mark_seen(video_id: str, channel_id: str = "", channel_title: str = "", video_title: str = ""):
    data = _load()
    data[video_id] = {
        "channel_id": channel_id,
        "channel_title": channel_title,
        "video_title": video_title,
        "summarized_at": datetime.datetime.utcnow().isoformat(),
    }
    _save(data)
