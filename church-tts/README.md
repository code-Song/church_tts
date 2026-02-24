# ⛪ 교회 안내방송 TTS

내 목소리를 학습시켜 안내방송을 만들거나, 학습 없이 샘플 목소리로 바로 사용할 수 있는 웹 앱입니다.  
**비상업적 사용**을 전제로 합니다.

## 기능

- **샘플 목소리**: 학습 없이 4가지 샘플 목소리 중 하나를 선택해 TTS 생성
- **목소리 학습 (WAV)**: WAV 파일을 업로드해 내 목소리로 등록
- **목소리 학습 (마이크)**: 마이크로 직접 녹음해 내 목소리로 등록
- **안내방송 생성**: 입력한 문구를 선택한 목소리(샘플 또는 내 목소리)로 음성 생성 및 다운로드

## 로컬 실행

```bash
cd church-tts
pip install -r requirements.txt
streamlit run app.py
```

### XTTS 모델 미리 받기 (선택, 첫 실행 시간 단축)

XTTS는 첫 로딩 시 대용량을 다운로드해 시간이 오래 걸립니다. **한 번만** 아래를 실행해 두면, 이후에는 `models/xtts_v2`에서 바로 로드됩니다.

```bash
cd church-tts
python download_xtts.py
```

- 다운로드 크기: 약 2GB  
- 저장 위치: `church-tts/models/xtts_v2`  
- 이 폴더를 Git 저장소에 포함해 두면, 다른 PC나 팀원도 별도 다운로드 없이 사용할 수 있습니다. (용량이 크므로 Git LFS 사용을 권장합니다.)

**PyTorch 2.9 이상**에서는 오디오 IO에 torchcodec이 필요해 coqui-tts와 호환 문제가 있을 수 있습니다. 이 프로젝트는 **torch & torchaudio 2.8 이하**를 권장합니다. 이미 2.9 이상을 설치했다면 아래처럼 다운그레이드한 뒤 앱을 실행하세요:

```bash
pip install "torch>=2.0.0,<2.9.0" "torchaudio>=2.0.0,<2.9.0"
```

브라우저에서 `http://localhost:8501` 로 접속합니다.

## Hugging Face Space 배포

1. [Hugging Face](https://huggingface.co) 에서 새 **Space** 생성
2. **SDK** 선택: **Streamlit**
3. 이 저장소의 파일 업로드:
   - `app.py`
   - `tts_engine.py`
   - `requirements.txt`
   - `README.md` (선택)
4. Space 설정에서 **Hardware**를 **CPU** 또는 **T4 GPU**로 설정 (GPU 권장: XTTS/Bark 로딩이 빠름)
5. 저장 후 자동으로 빌드 및 실행

### Space용 권장 설정

- **SDK**: Streamlit
- **Python**: 3.10
- **Hardware**: CPU 기본, 여유 있으면 T4 GPU

## 로컬 저장 (목소리 DB)

- 등록한 목소리(WAV 업로드 또는 마이크 녹음)는 **로컬 SQLite**에 저장됩니다.
- 저장 위치: `church-tts/voice_db.sqlite`, `church-tts/voice_cache/current.wav`
- 앱을 다시 실행해도 **다시 녹음·업로드하지 않아도** 이전에 등록한 목소리를 그대로 사용할 수 있습니다.
- "등록된 목소리 삭제" 버튼으로 저장된 목소리를 지울 수 있습니다.

## 사용 시 유의사항

- **내 목소리** 등록 시: 6~15초 정도의 **한국어** 음성(주변 소리 적은 환경)을 권장합니다.
- WAV 파일은 **모노, 16kHz 이상**이면 좋습니다. 마이크 녹음은 Streamlit 기본 설정(16kHz 등)을 따릅니다.
- 비상업적 목적으로만 사용해 주세요.

## 라이선스 / 비상업적 사용

- 본 앱은 교회·비영리 목적의 **비상업적 사용**을 전제로 합니다.
- 사용하는 TTS 모델(Bark, XTTS)의 각 라이선스(Coqui Public Model License 등)를 준수해 주세요.
