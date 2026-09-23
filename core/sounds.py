from __future__ import annotations

import logging
import os
from pathlib import Path

from core.config import (
    WAKE_SOUND_DURATION_MS,
    WAKE_SOUND_ENABLED,
    WAKE_SOUND_FREQUENCY,
    WAKE_SOUND_PATH,
)

logger = logging.getLogger("jarvis.sounds")


def play_wake_sound() -> None:
    if not WAKE_SOUND_ENABLED:
        return

    try:
        import winsound

        sound_path = Path(WAKE_SOUND_PATH)
        if sound_path.is_file():
            winsound.PlaySound(
                str(sound_path),
                winsound.SND_FILENAME | winsound.SND_NODEFAULT,
            )
            return

        winsound.Beep(WAKE_SOUND_FREQUENCY, WAKE_SOUND_DURATION_MS)
    except Exception:
        logger.exception("Falha ao reproduzir som da wake word.")
