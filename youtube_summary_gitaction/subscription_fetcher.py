# -*- coding: utf-8 -*-
"""구독 채널 목록 조회 (OAuth 또는 로컬 파일)."""
from __future__ import annotations
from pathlib import Path
from typing import List
from config import YOUTUBE_CHANNELS_FILE, YOUTUBE_CHANNEL_IDS, YOUTUBE_CREDENTIALS_PATH, YOUTUBE_TOKEN_PATH


def _read_channel_ids_from_file() -> List[str]:
    if not YOUTUBE_CHANNELS_FILE.exists():
        return []
    ids: List[str] = []
    for line in YOUTUBE_CHANNELS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            ids.append(line)
    return ids


def get_channel_ids() -> List[str]:
    if YOUTUBE_CHANNEL_IDS:
        return YOUTUBE_CHANNEL_IDS
    file_ids = _read_channel_ids_from_file()
    if file_ids:
        return file_ids
    return fetch_subscriptions_via_oauth()


def fetch_subscriptions_via_oauth() -> List[str]:
    if not YOUTUBE_CREDENTIALS_PATH.exists():
        return []
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError as e:
        print(f"[오류] OAuth 패키지 없음: {e}")
        return []

    SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
    creds = None

    if YOUTUBE_TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(YOUTUBE_TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(YOUTUBE_TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
        else:
            print("[오류] YouTube OAuth 토큰이 없습니다. YOUTUBE_TOKEN_JSON Secret을 확인하세요.")
            return []

    youtube = build("youtube", "v3", credentials=creds)
    channel_ids: List[str] = []
    request = youtube.subscriptions().list(part="snippet", mine=True, maxResults=50)
    while request:
        resp = request.execute()
        for item in resp.get("items", []):
            ch_id = item.get("snippet", {}).get("resourceId", {}).get("channelId")
            if ch_id:
                channel_ids.append(ch_id)
        request = youtube.subscriptions().list_next(request, resp)
    return channel_ids
