# -*- coding: utf-8 -*-
"""
등록된 목소리(WAV)를 로컬 SQLite에 저장/조회.
앱 재시작 후에도 다시 녹음·업로드 없이 사용 가능.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Literal

# 앱 기준 디렉터리 (app.py가 있는 곳)
APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "voice_db.sqlite"
VOICE_CACHE_DIR = APP_DIR / "voice_cache"
CURRENT_VOICE_PATH = VOICE_CACHE_DIR / "current.wav"

SourceType = Literal["upload", "mic"]


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """테이블이 없으면 생성."""
    VOICE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_voice (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                source_type TEXT NOT NULL,
                audio_blob BLOB NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


def save_voice(audio_bytes: bytes, source_type: SourceType) -> None:
    """목소리 WAV 데이터를 DB에 저장 (기존 건 덮어씀)."""
    import datetime
    init_db()
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO saved_voice (id, source_type, audio_blob, created_at)
            VALUES (1, ?, ?, ?)
            """,
            (source_type, audio_bytes, datetime.datetime.utcnow().isoformat()),
        )
        conn.commit()
    # 동기화: 캐시 파일도 갱신 (XTTS가 파일 경로를 쓰므로)
    VOICE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CURRENT_VOICE_PATH.write_bytes(audio_bytes)


def get_voice() -> tuple[bytes, SourceType] | None:
    """저장된 목소리가 있으면 (audio_bytes, source_type) 반환, 없으면 None."""
    init_db()
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT source_type, audio_blob FROM saved_voice WHERE id = 1"
        ).fetchone()
    if row is None or not row["audio_blob"]:
        return None
    return (bytes(row["audio_blob"]), row["source_type"])


def get_voice_path_and_source() -> tuple[Path | None, SourceType | None]:
    """
    저장된 목소리가 있으면 (캐시 파일 경로, source_type) 반환.
    없으면 (None, None). 캐시 파일이 없으면 DB에서 복원해 쓴다.
    """
    data = get_voice()
    if data is None:
        return None, None
    audio_bytes, source_type = data
    VOICE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CURRENT_VOICE_PATH.write_bytes(audio_bytes)
    return CURRENT_VOICE_PATH, source_type


def clear_voice() -> None:
    """저장된 목소리 삭제."""
    init_db()
    with _get_conn() as conn:
        conn.execute("DELETE FROM saved_voice WHERE id = 1")
        conn.commit()
    if CURRENT_VOICE_PATH.exists():
        try:
            CURRENT_VOICE_PATH.unlink()
        except OSError:
            pass
