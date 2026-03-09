# -*- coding: utf-8 -*-
"""
GitHub Actions용 메인 스크립트.
한 번 실행 → 새 영상 요약 → 텔레그램 스트리밍 전송 → 종료.
"""
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from storage import is_seen, mark_seen
from summarizer import get_transcript, summarize_with_gemini_stream
from youtube_fetcher import VideoInfo, get_new_videos

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def send_telegram(bot, chat_id: str, text: str):
    """텔레그램 메시지 전송 (4096자 제한 처리)."""
    for i in range(0, len(text), 4096):
        await bot.send_message(chat_id=chat_id, text=text[i:i + 4096])


async def run():
    if not TELEGRAM_BOT_TOKEN:
        print("[오류] TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
        sys.exit(1)
    if not TELEGRAM_CHAT_ID:
        print("[오류] TELEGRAM_CHAT_ID가 설정되지 않았습니다.")
        sys.exit(1)

    from telegram import Bot
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    # 봇 연결 확인
    me = await bot.get_me()
    logger.info("봇 연결됨: @%s", me.username)

    # 새 영상 조회
    try:
        videos = get_new_videos()
    except ValueError as e:
        await send_telegram(bot, TELEGRAM_CHAT_ID, f"❌ 오류: {e}")
        sys.exit(1)

    new_ones = [v for v in videos if not is_seen(v.video_id)]

    if not new_ones:
        await send_telegram(bot, TELEGRAM_CHAT_ID, "🆕 오늘 새 영상이 없습니다.")
        logger.info("새 영상 없음")
        return

    await send_telegram(bot, TELEGRAM_CHAT_ID, f"🔍 새 영상 {len(new_ones)}개를 요약합니다...")
    logger.info("새 영상 %d개 요약 시작", len(new_ones))

    for idx, video in enumerate(new_ones, 1):
        logger.info("[%d/%d] %s", idx, len(new_ones), video.title)

        # 시작 메시지 전송
        header = (
            f"📺 [{idx}/{len(new_ones)}] {video.channel_title}\n"
            f"제목: {video.title}\n"
            f"{video.url}\n\n"
            f"📝 요약 중..."
        )
        sent = await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=header)
        msg_id = sent.message_id

        transcript = get_transcript(video.video_id)

        # 자막 없는 경우
        if not transcript:
            await bot.edit_message_text(
                chat_id=TELEGRAM_CHAT_ID,
                message_id=msg_id,
                text=(
                    f"📺 [{idx}/{len(new_ones)}] {video.channel_title}\n"
                    f"제목: {video.title}\n"
                    f"{video.url}\n\n"
                    f"⚠️ 자막 없음 - 요약 불가"
                ),
            )
            mark_seen(video.video_id, video.channel_id, video.channel_title, video.title)
            continue

        # 스트리밍 요약
        accumulated = ""
        last_sent_len = 0

        async def on_chunk(part: str, _msg_id=msg_id, _idx=idx, _video=video):
            nonlocal accumulated, last_sent_len
            accumulated += part
            new_chars = len(accumulated) - last_sent_len
            ends_sentence = accumulated and accumulated[-1] in (".", "!", "?", "\n")
            if new_chars >= 80 or ends_sentence:
                preview = (
                    f"📺 [{_idx}/{len(new_ones)}] {_video.channel_title}\n"
                    f"제목: {_video.title}\n"
                    f"{_video.url}\n\n"
                    f"📝 요약 중...\n{accumulated}▌"
                )
                try:
                    await bot.edit_message_text(
                        chat_id=TELEGRAM_CHAT_ID,
                        message_id=_msg_id,
                        text=preview[:4096],
                    )
                    last_sent_len = len(accumulated)
                except Exception:
                    pass

        try:
            summary = await summarize_with_gemini_stream(transcript, video.title, on_chunk)
            mark_seen(video.video_id, video.channel_id, video.channel_title, video.title)
        except Exception as e:
            logger.exception("요약 실패: %s", video.video_id)
            summary = f"(요약 실패: {e})"
            mark_seen(video.video_id, video.channel_id, video.channel_title, video.title)

        # 최종 완성 메시지
        final_text = (
            f"📺 [{idx}/{len(new_ones)}] {video.channel_title}\n"
            f"제목: {video.title}\n"
            f"{video.url}\n\n"
            f"✅ 요약 완료:\n{summary}"
        )
        try:
            await bot.edit_message_text(
                chat_id=TELEGRAM_CHAT_ID,
                message_id=msg_id,
                text=final_text[:4096],
            )
        except Exception:
            await send_telegram(bot, TELEGRAM_CHAT_ID, final_text)

    await send_telegram(bot, TELEGRAM_CHAT_ID, f"✅ 전체 {len(new_ones)}개 요약 완료!")
    logger.info("요약 완료")


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
