from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.config import PIPER_DATA_DIR, TTS_VOICE_NAME


def main() -> int:
    data_dir = Path(PIPER_DATA_DIR).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"Baixando voz Piper: {TTS_VOICE_NAME}")
    print(f"Destino: {data_dir}")
    command = [
        sys.executable,
        "-m",
        "piper.download_voices",
        "--data-dir",
        str(data_dir),
        TTS_VOICE_NAME,
    ]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
