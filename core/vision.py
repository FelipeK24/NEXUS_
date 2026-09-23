from __future__ import annotations

import base64
import io
import logging
from pathlib import Path

from PIL import Image, ImageGrab
from groq import Groq

from core.config import GROQ_API_KEY, GROQ_TIMEOUT, VISION_ENABLED, VISION_MODEL, VISION_MAX_IMAGE_MB
from core.errors import LLMError

logger = logging.getLogger("jarvis.vision")


def _encode_image(path: Path) -> str:
    size_mb = path.stat().st_size / 1024 / 1024
    if size_mb > VISION_MAX_IMAGE_MB:
        raise ValueError(f"Imagem acima do limite de {VISION_MAX_IMAGE_MB:.0f} MB.")
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    suffix = path.suffix.lower()
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(suffix, "image/png")
    return f"data:{mime};base64,{data}"


def analisar_imagem(path: str, pergunta: str = "Descreva o que há nesta imagem.") -> str:
    if not VISION_ENABLED:
        return "A visão do NEXUS está desativada."
    if not GROQ_API_KEY:
        return "A análise visual exige uma GROQ_API_KEY configurada."
    image_path = Path(path).expanduser().resolve()
    if not image_path.is_file():
        return f"Não encontrei a imagem: {path}"
    client = Groq(api_key=GROQ_API_KEY, timeout=GROQ_TIMEOUT)
    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": pergunta},
                {"type": "image_url", "image_url": {"url": _encode_image(image_path)}},
            ],
        }],
        temperature=0.2,
        max_completion_tokens=800,
    )
    content = response.choices[0].message.content
    return content.strip() if content else "Não consegui interpretar a imagem."


def capturar_tela(temp_path: Path) -> Path:
    image = ImageGrab.grab()
    image.save(temp_path, format="PNG")
    return temp_path


def analisar_tela(pergunta: str = "Descreva o que aparece na minha tela e destaque o que for relevante.") -> str:
    temp_path = Path.cwd() / "data" / "nexus_screen.png"
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        capturar_tela(temp_path)
        return analisar_imagem(str(temp_path), pergunta)
    finally:
        try:
            temp_path.unlink()
        except OSError:
            pass
