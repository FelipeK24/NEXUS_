from __future__ import annotations

import importlib.util
import os
from pathlib import Path

from core.config import (
    API_ENABLED, API_HOST, API_PORT, GROQ_API_KEY, GROQ_MODEL, OLLAMA_MODEL,
    PIPER_MODEL_PATH, SMART_HOME_PROVIDER, TTS_ENGINE, TTS_VOICE_NAME,
    VISION_ENABLED, VISION_MODEL, VOSK_MODEL_PATH, GOOGLE_ENABLED, GOOGLE_CREDENTIALS_FILE,
    GOOGLE_GMAIL_TOKEN_FILE, GOOGLE_TASKS_TOKEN_FILE, REMINDERS_FILE,
)

REQUIRED = [
    "groq", "ollama", "vosk", "faster_whisper", "sounddevice",
    "pyttsx3", "piper", "psutil", "dotenv", "PIL", "playwright", "winotify",
]
OPTIONAL_GOOGLE = ["googleapiclient", "google_auth_oauthlib"]

print("=== NEXUS FINAL DOCTOR ===")

for module in REQUIRED:
    ok = importlib.util.find_spec(module) is not None
    print(f"{'OK' if ok else 'FALTA':5} {module}")

for module in OPTIONAL_GOOGLE:
    ok = importlib.util.find_spec(module) is not None
    print(f"{'OK' if ok else 'OPC':5} {module}")

print(f"GROQ_API_KEY: {'configurada' if GROQ_API_KEY else 'não configurada'}")
print(f"GROQ_MODEL: {GROQ_MODEL}")
print(f"OLLAMA_MODEL: {OLLAMA_MODEL}")
print(f"VOSK_MODEL_PATH: {'encontrado' if os.path.isdir(VOSK_MODEL_PATH) else 'não encontrado'}")
print(f"TTS_ENGINE: {TTS_ENGINE}")
print(f"TTS_VOICE_NAME: {TTS_VOICE_NAME}")
print(f"PIPER_MODEL_PATH: {'encontrado' if os.path.isfile(PIPER_MODEL_PATH) else 'não encontrado'}")
print(f"Playwright Chromium: opcional - use 'python -m playwright install chromium'")
print(f"Vision: {'habilitada' if VISION_ENABLED else 'desabilitada'} | modelo={VISION_MODEL}")
print(f"Google: {'habilitado' if GOOGLE_ENABLED else 'desabilitado'} | credentials={'encontrado' if Path(GOOGLE_CREDENTIALS_FILE).exists() else 'ausente'} | gmail_token={'sim' if GOOGLE_GMAIL_TOKEN_FILE.exists() else 'não'} | tasks_token={'sim' if GOOGLE_TASKS_TOKEN_FILE.exists() else 'não'}")
print(f"API: {'habilitada' if API_ENABLED else 'desabilitada'} | {API_HOST}:{API_PORT}")
print(f"Lembretes: {REMINDERS_FILE}")
print(f"Smart Home: {SMART_HOME_PROVIDER}")
