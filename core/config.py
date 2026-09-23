from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
MODELS_DIR = ROOT_DIR / "models"
LOG_FILE = ROOT_DIR / "jarvis.log"
MEMORY_FILE = DATA_DIR / "memory.json"

load_dotenv(ROOT_DIR / ".env")

ASSISTANT_NAME = os.getenv("JARVIS_NAME", "NEXUS")
WAKE_WORD = os.getenv("WAKE_WORD", "nexus")
WAKE_SOUND_ENABLED = os.getenv("WAKE_SOUND_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
WAKE_SOUND_PATH = os.getenv("WAKE_SOUND_PATH", str(ROOT_DIR / "assets" / "wake.wav")).strip()
WAKE_SOUND_FREQUENCY = int(os.getenv("WAKE_SOUND_FREQUENCY", "880"))
WAKE_SOUND_DURATION_MS = int(os.getenv("WAKE_SOUND_DURATION_MS", "120"))
LANGUAGE = "pt"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
GROQ_TIMEOUT = float(os.getenv("GROQ_TIMEOUT", "15"))
GROQ_COOLDOWN = float(os.getenv("GROQ_COOLDOWN", "60"))

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").strip()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:1.7b").strip()
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "30"))

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small").strip()
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu").strip()
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8").strip()
VOSK_MODEL_PATH = os.getenv(
    "VOSK_MODEL_PATH",
    str(MODELS_DIR / "vosk-model-small-en-us"),
).strip()

SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
WAKE_CHUNK_MS = int(os.getenv("WAKE_CHUNK_MS", "300"))
COMMAND_MAX_SECONDS = float(os.getenv("COMMAND_MAX_SECONDS", "10"))
COMMAND_CHUNK_MS = int(os.getenv("COMMAND_CHUNK_MS", "30"))
COMMAND_PRE_ROLL_MS = int(os.getenv("COMMAND_PRE_ROLL_MS", "300"))
COMMAND_NOISE_CALIBRATION_MS = int(os.getenv("COMMAND_NOISE_CALIBRATION_MS", "240"))
COMMAND_SPEECH_MULTIPLIER = float(os.getenv("COMMAND_SPEECH_MULTIPLIER", "2.2"))
COMMAND_MIN_RMS = float(os.getenv("COMMAND_MIN_RMS", "450"))
COMMAND_SILENCE_MS = int(os.getenv("COMMAND_SILENCE_MS", "650"))
COMMAND_START_TIMEOUT_MS = int(os.getenv("COMMAND_START_TIMEOUT_MS", "5000"))
WHISPER_HOTWORDS = os.getenv(
    "WHISPER_HOTWORDS",
    "NEXUS, Spotify, YouTube, Google, WhatsApp, Discord, Gmail, Opera",
).strip()
WHISPER_INITIAL_PROMPT = os.getenv(
    "WHISPER_INITIAL_PROMPT",
    "Comando de voz do assistente NEXUS em português brasileiro. "
    "Palavras importantes: NEXUS, Spotify, YouTube, Google, WhatsApp, Discord, Gmail, Opera.",
).strip()

TTS_ENABLED = os.getenv("TTS_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
TTS_RATE = int(os.getenv("TTS_RATE", "175"))
TTS_VOLUME = float(os.getenv("TTS_VOLUME", "1.0"))
TTS_ENGINE = os.getenv("TTS_ENGINE", "piper").strip().lower()
TTS_FALLBACK_ENABLED = os.getenv("TTS_FALLBACK_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
TTS_VOICE_NAME = os.getenv("TTS_VOICE_NAME", "pt_BR-jeff-medium").strip()
PIPER_DATA_DIR = os.getenv("PIPER_DATA_DIR", str(MODELS_DIR / "piper")).strip()
PIPER_MODEL_PATH = os.getenv(
    "PIPER_MODEL_PATH",
    str(Path(PIPER_DATA_DIR) / f"{TTS_VOICE_NAME}.onnx"),
).strip()
PIPER_LENGTH_SCALE = float(os.getenv("PIPER_LENGTH_SCALE", "0.95"))
PIPER_NOISE_SCALE = float(os.getenv("PIPER_NOISE_SCALE", "0.667"))
PIPER_NOISE_W_SCALE = float(os.getenv("PIPER_NOISE_W_SCALE", "0.8"))
PIPER_VOLUME = float(os.getenv("PIPER_VOLUME", "1.0"))
TEXT_ONLY = os.getenv("TEXT_ONLY", "false").lower() in {"1", "true", "yes", "on"}

PANEL_ENABLED = os.getenv("PANEL_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
PANEL_HOST = os.getenv("PANEL_HOST", "127.0.0.1").strip()
PANEL_PORT = int(os.getenv("PANEL_PORT", "8765"))

# NEXUS 6.0 - Web e navegador
WEB_SEARCH_ENGINE = os.getenv("WEB_SEARCH_ENGINE", "bing").strip().lower()
WEB_SEARCH_LIMIT = int(os.getenv("WEB_SEARCH_LIMIT", "6"))
WEB_REQUEST_TIMEOUT = float(os.getenv("WEB_REQUEST_TIMEOUT", "10"))
BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "false").lower() in {"1", "true", "yes", "on"}
BROWSER_CHANNEL = os.getenv("BROWSER_CHANNEL", "").strip()
BROWSER_PROFILE_DIR = os.getenv("BROWSER_PROFILE_DIR", str(DATA_DIR / "browser_profile")).strip()
BROWSER_NAV_TIMEOUT = int(os.getenv("BROWSER_NAV_TIMEOUT", "15000"))
BROWSER_READ_LIMIT = int(os.getenv("BROWSER_READ_LIMIT", "8000"))

# NEXUS Final - produtividade, visão, API e extensões
TASKS_FILE = DATA_DIR / "tasks.json"
CONTACTS_FILE = DATA_DIR / "contacts.json"
GOOGLE_CREDENTIALS_FILE = Path(os.getenv("GOOGLE_CREDENTIALS_FILE", str(DATA_DIR / "google_credentials.json"))).resolve()
GOOGLE_TOKEN_FILE = Path(os.getenv("GOOGLE_TOKEN_FILE", str(DATA_DIR / "google_token.json"))).resolve()
GOOGLE_GMAIL_TOKEN_FILE = Path(os.getenv("GOOGLE_GMAIL_TOKEN_FILE", str(DATA_DIR / "google_gmail_token.json"))).resolve()
GOOGLE_TASKS_TOKEN_FILE = Path(os.getenv("GOOGLE_TASKS_TOKEN_FILE", str(DATA_DIR / "google_tasks_token.json"))).resolve()
GOOGLE_ENABLED = os.getenv("GOOGLE_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
GOOGLE_TIMEZONE = os.getenv("GOOGLE_TIMEZONE", "America/Sao_Paulo").strip()
GMAIL_MAX_RESULTS = int(os.getenv("GMAIL_MAX_RESULTS", "10"))
VISION_ENABLED = os.getenv("VISION_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
VISION_MODEL = os.getenv("VISION_MODEL", "qwen/qwen3.6-27b").strip()
VISION_MAX_IMAGE_MB = float(os.getenv("VISION_MAX_IMAGE_MB", "20"))
API_ENABLED = os.getenv("API_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
API_HOST = os.getenv("API_HOST", "127.0.0.1").strip()
API_PORT = int(os.getenv("API_PORT", "8766"))
API_TOKEN = os.getenv("API_TOKEN", "").strip()
REMINDERS_FILE = DATA_DIR / "reminders.json"
REMINDER_POLL_SECONDS = float(os.getenv("REMINDER_POLL_SECONDS", "2"))
REMINDER_SPEAK = os.getenv("REMINDER_SPEAK", "true").lower() in {"1", "true", "yes", "on"}

SMART_HOME_PROVIDER = os.getenv("SMART_HOME_PROVIDER", "none").strip().lower()
HOME_ASSISTANT_URL = os.getenv("HOME_ASSISTANT_URL", "").strip().rstrip("/")
HOME_ASSISTANT_TOKEN = os.getenv("HOME_ASSISTANT_TOKEN", "").strip()
ESP32_BASE_URL = os.getenv("ESP32_BASE_URL", "").strip().rstrip("/")

APPLICATIONS = {
    "spotify": os.getenv(
        "SPOTIFY_PATH",
        str(Path(os.getenv("APPDATA", "")) / "Spotify" / "Spotify.exe"),
    ),
    "opera": os.getenv(
        "OPERA_PATH",
        str(
            Path(os.getenv("LOCALAPPDATA", ""))
            / "Programs"
            / "Opera GX"
            / "opera.exe"
        ),
    ),
}

PROCESS_NAMES = {
    "spotify": "Spotify.exe",
    "opera": "opera.exe",
}

PATHS_FILE = DATA_DIR / "paths.json"
APPLICATIONS_FILE = DATA_DIR / "applications.json"
PROCESS_ALLOWLIST_PATH = DATA_DIR / "processes.json"
FILE_SEARCH_LIMIT = int(os.getenv("FILE_SEARCH_LIMIT", "30"))
PROCESS_LIST_LIMIT = int(os.getenv("PROCESS_LIST_LIMIT", "25"))

def _load_json_file(path: Path, default: dict) -> dict:
    try:
        import json
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else default
    except (OSError, ValueError):
        return default


_loaded_paths = _load_json_file(PATHS_FILE, {})
FILE_ALLOWED_ROOTS = {
    str(key).lower(): os.path.expandvars(os.path.expanduser(str(value)))
    for key, value in _loaded_paths.items()
    if isinstance(value, str) and value.strip()
}

SPOTIFY_PLAYLISTS = {
    "treino": os.getenv("SPOTIFY_PLAYLIST_TREINO", ""),
    "calma": os.getenv("SPOTIFY_PLAYLIST_CALMA", ""),
    "foco": os.getenv("SPOTIFY_PLAYLIST_FOCO", ""),
}

SITES_FILE = DATA_DIR / "sites.json"

SITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "whatsapp": "https://web.whatsapp.com",
    "discord": "https://discord.com/app",
    "gmail": "https://mail.google.com",
    "spotify web": "https://open.spotify.com",
}

SENSITIVE_INTENTS = {
    "close_application": "medium",
    "system_control": "low",
    "file_delete": "high",
    "file_move": "medium",
    "email_send": "high",
    "web_action": "medium",
    "smart_home_action": "high",
    "email_send": "high",
    "calendar_create": "medium",
    "calendar_delete": "high",
    "task_delete": "medium",
}

DATA_DIR.mkdir(parents=True, exist_ok=True)
