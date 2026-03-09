# -*- coding: utf-8 -*-
"""설정: GitHub Secrets(환경변수)에서 로드."""
import os
import json
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

BASE_DIR = Path(__file__).parent

# YouTube Data API v3
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
YOUTUBE_CHANNEL_IDS = [
    x.strip()
    for x in os.environ.get("YOUTUBE_CHANNEL_IDS", "").split(",")
    if x.strip()
]

YOUTUBE_CREDENTIALS_PATH = BASE_DIR / "youtube_credentials.json"
YOUTUBE_TOKEN_PATH = BASE_DIR / "youtube_token.json"
YOUTUBE_CHANNELS_FILE = BASE_DIR / "channels.txt"

# GitHub Secrets에 저장된 파일 내용을 복원
def _restore_secret_file(env_var: str, target_path: Path):
    content = os.environ.get(env_var, "")
    if content and not target_path.exists():
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")

_restore_secret_file("YOUTUBE_TOKEN_JSON", YOUTUBE_TOKEN_PATH)
_restore_secret_file("YOUTUBE_CHANNELS_TXT", YOUTUBE_CHANNELS_FILE)

# Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# 새 영상 조회 범위
DAYS_TO_CHECK = int(os.environ.get("DAYS_TO_CHECK", "1"))
