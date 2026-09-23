from __future__ import annotations

import logging
import os
import tempfile
import threading
import wave

import pyttsx3

from core.config import (
    PIPER_LENGTH_SCALE,
    PIPER_MODEL_PATH,
    PIPER_NOISE_SCALE,
    PIPER_NOISE_W_SCALE,
    PIPER_VOLUME,
    TTS_ENGINE,
    TTS_ENABLED,
    TTS_FALLBACK_ENABLED,
    TTS_RATE,
    TTS_VOLUME,
)

logger = logging.getLogger("jarvis.speaker")

_engine = None
_piper_voice = None
_lock = threading.Lock()


def _get_windows_engine():
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty("rate", TTS_RATE)
        _engine.setProperty("volume", TTS_VOLUME)

        voices = _engine.getProperty("voices") or []
        for voice in voices:
            data = f"{voice.id} {voice.name}".lower()
            if "pt-br" in data or "brazil" in data or "portugu" in data:
                _engine.setProperty("voice", voice.id)
                break
    return _engine


def _get_piper_voice():
    global _piper_voice

    if _piper_voice is None:
        from piper import PiperVoice

        model_path = os.path.abspath(PIPER_MODEL_PATH)
        if not os.path.isfile(model_path):
            raise FileNotFoundError(
                f"Modelo Piper não encontrado em: {model_path}"
            )
        _piper_voice = PiperVoice.load(model_path)
        logger.info("Voz Piper carregada: %s", model_path)

    return _piper_voice


def _falar_piper(texto: str) -> None:
    from piper import SynthesisConfig

    voice = _get_piper_voice()
    temp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp.close()

    try:
        with wave.open(temp.name, "wb") as wav_file:
            voice.synthesize_wav(
                texto,
                wav_file,
                syn_config=SynthesisConfig(
                    volume=PIPER_VOLUME,
                    length_scale=PIPER_LENGTH_SCALE,
                    noise_scale=PIPER_NOISE_SCALE,
                    noise_w_scale=PIPER_NOISE_W_SCALE,
                    normalize_audio=True,
                ),
            )

        import winsound

        winsound.PlaySound(temp.name, winsound.SND_FILENAME)
    finally:
        try:
            os.remove(temp.name)
        except OSError:
            pass


def _falar_windows(texto: str) -> None:
    engine = _get_windows_engine()
    engine.say(texto)
    engine.runAndWait()


def falar(texto: str) -> None:
    if not TTS_ENABLED or not texto.strip():
        return

    with _lock:
        if TTS_ENGINE == "piper":
            try:
                _falar_piper(texto)
                return
            except Exception:
                logger.exception("Falha no Piper TTS.")
                if not TTS_FALLBACK_ENABLED:
                    raise

        _falar_windows(texto)
