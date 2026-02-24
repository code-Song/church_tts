# -*- coding: utf-8 -*-
"""
교회 안내방송 TTS - Streamlit UI
- 샘플 목소리로 TTS (학습 없이 선택)
- WAV 파일 업로드로 내 목소리 학습
- 마이크 녹음으로 내 목소리 학습
- 안내방송 생성 (샘플 또는 내 목소리)
비상업적 사용.
"""
from __future__ import annotations

import os

# OpenMP 중복 로드 방지 (Windows에서 libiomp5md.dll 충돌 시)
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import tempfile
from pathlib import Path

import streamlit as st

import voice_db
from tts_engine import (
    BARK_VOICE_PRESETS,
    ensure_wav_seconds,
    get_bark_pipeline,
    get_xtts_model,
    synthesize_bark,
    synthesize_xtts,
)

st.set_page_config(
    page_title="교회 안내방송 TTS",
    page_icon="⛪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 세션 상태 초기화 + 로컬 DB에서 저장된 목소리 복원
if "my_voice_path" not in st.session_state:
    st.session_state.my_voice_path = None
if "my_voice_from_mic" not in st.session_state:
    st.session_state.my_voice_from_mic = None
# 앱 시작 시 SQLite에 저장된 목소리가 있으면 복원 (다시 녹음/업로드 불필요)
if "voice_loaded_from_db" not in st.session_state:
    st.session_state.voice_loaded_from_db = False
if not st.session_state.voice_loaded_from_db:
    path, source = voice_db.get_voice_path_and_source()
    if path is not None and path.exists():
        st.session_state.my_voice_path = str(path)
        st.session_state.my_voice_from_mic = str(path) if source == "mic" else None
    st.session_state.voice_loaded_from_db = True


def _save_uploaded_or_recorded_audio(source, key_suffix: str) -> str | None:
    """업로드/녹음 오디오를 임시 WAV 파일로 저장하고 경로 반환."""
    if source is None:
        return None
    data = source.read() if hasattr(source, "read") else source.getvalue() if hasattr(source, "getvalue") else source
    if not data:
        return None
    path = Path(tempfile.gettempdir()) / f"church_tts_voice_{key_suffix}.wav"
    path.write_bytes(data)
    return str(path)


def _load_bark():
    if "bark_pipeline" not in st.session_state:
        with st.spinner("Bark 모델 로딩 중..."):
            proc, model, dev = get_bark_pipeline()
            st.session_state.bark_processor = proc
            st.session_state.bark_model = model
            st.session_state.bark_device = dev
    return (
        st.session_state.bark_processor,
        st.session_state.bark_model,
        st.session_state.bark_device,
    )


def _load_xtts():
    if "xtts_model" not in st.session_state:
        with st.spinner("XTTS 모델 로딩 중... (최초 1회 다운로드)..."):
            tts, dev = get_xtts_model()
            st.session_state.xtts_model = tts
            st.session_state.xtts_device = dev
    return st.session_state.xtts_model, st.session_state.xtts_device


# ----- UI -----
st.title("⛪ 교회 안내방송 TTS")
st.caption("비상업적 사용 | 내 목소리 학습 또는 샘플 목소리로 안내방송을 만들어 보세요.")

tab1, tab2, tab3, tab4 = st.tabs([
    "🎤 샘플 목소리로 들어보기",
    "📁 목소리 학습 (WAV 파일)",
    "🎙️ 목소리 학습 (마이크 녹음)",
    "📢 안내방송 생성",
])

# ----- 탭 1: 샘플 목소리 -----
with tab1:
    st.subheader("학습 없이 비슷한 목소리 선택")
    voice_option = st.selectbox(
        "샘플 목소리",
        options=range(len(BARK_VOICE_PRESETS)),
        format_func=lambda i: BARK_VOICE_PRESETS[i][0],
        key="sample_voice_select",
    )
    sample_text = st.text_area(
        "테스트 문장",
        value="안녕하세요. 오늘 예배에 참석해 주셔서 감사합니다.",
        height=100,
        key="sample_text",
    )
    if st.button("샘플 음성 생성", key="btn_sample"):
        if not sample_text.strip():
            st.warning("문장을 입력해 주세요.")
        else:
            try:
                processor, model, device = _load_bark()
                preset_name = BARK_VOICE_PRESETS[voice_option][1]
                wav_bytes = synthesize_bark(sample_text.strip(), preset_name, processor, model, device)
                st.audio(wav_bytes, format="audio/wav")
                st.download_button("다운로드 (WAV)", data=wav_bytes, file_name="sample_voice.wav", mime="audio/wav", key="dl_sample")
            except Exception as e:
                st.error(f"생성 실패: {e}")

# ----- 탭 2: 목소리 학습 (WAV) -----
with tab2:
    st.subheader("WAV 파일로 내 목소리 등록")
    st.info("6~15초 정도의 깨끗한 음성(한국어)을 업로드하면, 그 목소리로 안내방송을 만들 수 있습니다.")
    uploaded = st.file_uploader("WAV 파일 선택", type=["wav", "wave"], key="wav_upload")
    if uploaded is not None:
        path = _save_uploaded_or_recorded_audio(uploaded, "upload")
        if path:
            voice_bytes = Path(path).read_bytes()
            voice_db.save_voice(voice_bytes, "upload")
            st.session_state.my_voice_path = str(voice_db.CURRENT_VOICE_PATH)
            st.session_state.my_voice_from_mic = None
            st.success("목소리 파일이 등록되었습니다. 로컬에 저장되어 다음에 다시 올릴 필요 없습니다.")
            st.audio(path, format="audio/wav")
    if st.session_state.my_voice_path and not st.session_state.my_voice_from_mic and os.path.exists(st.session_state.my_voice_path):
        st.caption("현재 등록된 목소리: WAV 파일 (로컬 DB에 저장됨)")
        if st.button("등록된 목소리 삭제", key="clear_upload"):
            voice_db.clear_voice()
            st.session_state.my_voice_path = None
            st.session_state.my_voice_from_mic = None
            st.rerun()

# ----- 탭 3: 목소리 학습 (마이크) -----
with tab3:
    st.subheader("마이크로 바로 녹음해서 목소리 등록")
    st.info("마이크 버튼을 누른 뒤, 6~15초 정도 한국어로 말해 주세요. 주변 소리가 적을수록 좋습니다.")
    rec = st.audio_input("녹음", key="mic_rec")
    if rec is not None:
        path = _save_uploaded_or_recorded_audio(rec, "mic")
        if path:
            voice_bytes = Path(path).read_bytes()
            voice_db.save_voice(voice_bytes, "mic")
            st.session_state.my_voice_from_mic = str(voice_db.CURRENT_VOICE_PATH)
            st.session_state.my_voice_path = str(voice_db.CURRENT_VOICE_PATH)
            st.success("녹음이 등록되었습니다. 로컬에 저장되어 다음에 다시 녹음할 필요 없습니다.")
            st.audio(path, format="audio/wav")
    if st.session_state.my_voice_from_mic and os.path.exists(st.session_state.my_voice_from_mic):
        st.caption("현재 등록된 목소리: 마이크 녹음 (로컬 DB에 저장됨)")
        if st.button("등록된 목소리 삭제", key="clear_mic"):
            voice_db.clear_voice()
            st.session_state.my_voice_path = None
            st.session_state.my_voice_from_mic = None
            st.rerun()

# ----- 탭 4: 안내방송 생성 -----
with tab4:
    st.subheader("안내방송 음성 생성")
    ann_text = st.text_area("안내 문구", value="오늘 주일 예배에 참석해 주신 여러분 감사합니다. 예배가 곧 시작됩니다.", height=120, key="ann_text")

    voice_sources = ["샘플 1 (차분한 남성)", "샘플 2 (밝은 여성)", "샘플 3 (안내 방송 스타일)", "샘플 4 (따뜻한 톤)"]
    if st.session_state.my_voice_path or st.session_state.my_voice_from_mic:
        voice_sources.append("내 목소리 (등록된 음성)")

    voice_choice = st.selectbox("사용할 목소리", options=voice_sources, key="ann_voice")

    if st.button("안내방송 생성", key="btn_ann"):
        if not ann_text.strip():
            st.warning("안내 문구를 입력해 주세요.")
        elif voice_choice == "내 목소리 (등록된 음성)":
            ref_path = st.session_state.my_voice_path or st.session_state.my_voice_from_mic
            if not ref_path or not os.path.exists(ref_path):
                st.error("등록된 목소리가 없습니다. '목소리 학습' 탭에서 WAV 또는 마이크 녹음을 등록해 주세요.")
            else:
                try:
                    ref_path = ensure_wav_seconds(ref_path)
                    if ref_path is None:
                        st.error("음성이 너무 짧습니다. 1초 이상 녹음 또는 업로드해 주세요.")
                    else:
                        tts, device = _load_xtts()
                        wav_bytes = synthesize_xtts(ann_text.strip(), ref_path, language="ko", tts=tts, device=device)
                        st.audio(wav_bytes, format="audio/wav")
                        st.download_button("다운로드 (WAV)", data=wav_bytes, file_name="announcement.wav", mime="audio/wav", key="dl_ann")
                except Exception as e:
                    err_msg = str(e)
                    if "torchcodec" in err_msg.lower() or "coqui's codec" in err_msg.lower():
                        st.error(
                            "PyTorch 2.9+ 환경에서는 오디오 처리에 torchcodec이 필요해 오류가 날 수 있습니다. "
                            "해결: 터미널에서 torch/torchaudio를 2.8 이하로 설치한 뒤 앱을 다시 실행하세요 — "
                            "pip install \"torch>=2.0.0,<2.9.0\" \"torchaudio>=2.0.0,<2.9.0\""
                        )
                    else:
                        st.error(f"생성 실패: {e}")
        else:
            idx = voice_sources.index(voice_choice)
            try:
                processor, model, device = _load_bark()
                preset_name = BARK_VOICE_PRESETS[idx][1]
                wav_bytes = synthesize_bark(ann_text.strip(), preset_name, processor, model, device)
                st.audio(wav_bytes, format="audio/wav")
                st.download_button("다운로드 (WAV)", data=wav_bytes, file_name="announcement.wav", mime="audio/wav", key="dl_ann2")
            except Exception as e:
                err_msg = str(e)
                if "torchcodec" in err_msg.lower() or "coqui's codec" in err_msg.lower():
                    st.error(
                        "PyTorch 2.9+에서는 torchcodec 오류가 날 수 있습니다. "
                        "pip install \"torch>=2.0.0,<2.9.0\" \"torchaudio>=2.0.0,<2.9.0\" 실행 후 앱을 다시 실행하세요."
                    )
                else:
                    st.error(f"생성 실패: {e}")

st.sidebar.markdown("### 사용 방법")
st.sidebar.markdown("""
1. **샘플 목소리**: 학습 없이 4가지 샘플 중 하나를 골라 들어보기
2. **WAV 파일**: 본인 음성 6~15초 WAV 업로드 후 '내 목소리'로 사용
3. **마이크 녹음**: 마이크로 직접 녹음해 등록
4. **안내방송 생성**: 문구 입력 후 샘플 또는 내 목소리로 생성

**비상업적 사용**에만 이용해 주세요.
""")
