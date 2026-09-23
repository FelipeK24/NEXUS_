from __future__ import annotations

from core.config import TTS_ENGINE, TTS_VOICE_NAME
from core.speaker import falar


if __name__ == "__main__":
    text = "NEXUS online. Sistema de voz funcionando corretamente."
    print(f"Motor TTS: {TTS_ENGINE}")
    print(f"Voz configurada: {TTS_VOICE_NAME}")
    falar(text)
    print("Teste concluído.")
