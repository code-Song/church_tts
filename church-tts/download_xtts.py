# -*- coding: utf-8 -*-
"""
XTTS v2 모델을 Hugging Face에서 한 번만 다운로드해 프로젝트 models/xtts_v2 에 저장합니다.
실행 후 앱은 이 경로에서 로드하므로 매번 다운받지 않습니다.

사용법:
  python download_xtts.py

약 2GB 정도 다운로드됩니다. 완료 후 streamlit run app.py 시 XTTS 로딩이 빠릅니다.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# 프로젝트 루트 (이 스크립트가 있는 폴더)
ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "models" / "xtts_v2"


def main() -> None:
    if (MODEL_DIR / "config.json").exists() and (MODEL_DIR / "model.pth").exists():
        print(f"이미 로컬에 있습니다: {MODEL_DIR}")
        print("다시 받으려면 models/xtts_v2 폴더를 삭제한 뒤 다시 실행하세요.")
        return

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("huggingface_hub 가 필요합니다: pip install huggingface_hub")
        sys.exit(1)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print("XTTS v2 모델 다운로드 중... (약 2GB, 한 번만 받으면 됩니다)")
    snapshot_download(
        repo_id="coqui/XTTS-v2",
        local_dir=str(MODEL_DIR),
        local_dir_use_symlinks=False,
    )
    print(f"저장 위치: {MODEL_DIR}")
    print("이제 streamlit run app.py 실행 시 XTTS는 이 경로에서 바로 로드됩니다.")


if __name__ == "__main__":
    main()
