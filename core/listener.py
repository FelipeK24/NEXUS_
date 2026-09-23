from __future__ import annotations

import json
import logging
import math
import os
import tempfile
import wave
from array import array
from collections import deque

import sounddevice as sd
from faster_whisper import WhisperModel
from vosk import KaldiRecognizer, Model

from core.config import (
    COMMAND_CHUNK_MS,
    COMMAND_MAX_SECONDS,
    COMMAND_MIN_RMS,
    COMMAND_NOISE_CALIBRATION_MS,
    COMMAND_PRE_ROLL_MS,
    COMMAND_SILENCE_MS,
    COMMAND_SPEECH_MULTIPLIER,
    COMMAND_START_TIMEOUT_MS,
    SAMPLE_RATE,
    VOSK_MODEL_PATH,
    WAKE_CHUNK_MS,
    WAKE_WORD,
    WHISPER_COMPUTE_TYPE,
    WHISPER_DEVICE,
    WHISPER_HOTWORDS,
    WHISPER_INITIAL_PROMPT,
    WHISPER_MODEL,
)
from core.sounds import play_wake_sound

_vosk_model: Model | None = None
_whisper_model: WhisperModel | None = None


def _get_vosk_model() -> Model:
    global _vosk_model
    if _vosk_model is None:
        if not os.path.isdir(VOSK_MODEL_PATH):
            raise FileNotFoundError(
                f"Modelo Vosk não encontrado em: {VOSK_MODEL_PATH}"
            )
        _vosk_model = Model(VOSK_MODEL_PATH)
    return _vosk_model


def _get_whisper_model() -> WhisperModel:
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = WhisperModel(
            WHISPER_MODEL,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE,
        )
    return _whisper_model


def listen_for_wake_word(stop_event=None) -> None:
    model = _get_vosk_model()
    if os.getenv("WAKE_GRAMMAR_ONLY", "true").lower() in {"1", "true", "yes", "on"}:
        grammar = json.dumps([WAKE_WORD.lower()])
        recognizer = KaldiRecognizer(model, SAMPLE_RATE, grammar)
    else:
        recognizer = KaldiRecognizer(model, SAMPLE_RATE)
    recognizer.SetWords(False)
    blocksize = int(SAMPLE_RATE * WAKE_CHUNK_MS / 1000)

    logger = logging.getLogger("jarvis.listener")
    logger.info("Aguardando a palavra de ativação: %s", WAKE_WORD)

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=blocksize,
        dtype="int16",
        channels=1,
    ) as stream:
        while True:
            if stop_event is not None and stop_event.is_set():
                return
            data, _ = stream.read(blocksize)
            if recognizer.AcceptWaveform(bytes(data)):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").lower()
                if WAKE_WORD.lower() in text:
                    logger.info("Wake word detectada.")
                    play_wake_sound()
                    return


def _rms_level(data: bytes) -> float:
    samples = array("h")
    samples.frombytes(data)
    if not samples:
        return 0.0
    mean_square = sum(sample * sample for sample in samples) / len(samples)
    return math.sqrt(mean_square)


def _write_wav(frames: list[bytes]) -> str:
    temp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp.close()

    with wave.open(temp.name, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(b"".join(frames))

    return temp.name


def _record_audio() -> str:
    blocksize = max(1, int(SAMPLE_RATE * COMMAND_CHUNK_MS / 1000))
    pre_roll_blocks = max(1, math.ceil(COMMAND_PRE_ROLL_MS / COMMAND_CHUNK_MS))
    calibration_blocks = max(1, math.ceil(COMMAND_NOISE_CALIBRATION_MS / COMMAND_CHUNK_MS))
    max_blocks = max(1, math.ceil(COMMAND_MAX_SECONDS * 1000 / COMMAND_CHUNK_MS))
    start_timeout_blocks = max(1, math.ceil(COMMAND_START_TIMEOUT_MS / COMMAND_CHUNK_MS))
    silence_blocks_required = max(1, math.ceil(COMMAND_SILENCE_MS / COMMAND_CHUNK_MS))

    calibration_levels: list[float] = []
    frames: list[bytes] = []
    pre_roll = deque(maxlen=pre_roll_blocks)
    speech_started = False
    silence_blocks = 0
    waited_blocks = 0

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=blocksize,
        dtype="int16",
        channels=1,
    ) as stream:
        for _ in range(calibration_blocks):
            data, _ = stream.read(blocksize)
            data = bytes(data)
            calibration_levels.append(_rms_level(data))
            pre_roll.append(data)

        sorted_levels = sorted(calibration_levels)
        quiet_count = max(1, math.ceil(len(sorted_levels) * 0.7))
        quiet_levels = sorted_levels[:quiet_count]
        noise_floor = sum(quiet_levels) / len(quiet_levels)
        speech_threshold = max(
            COMMAND_MIN_RMS,
            noise_floor * COMMAND_SPEECH_MULTIPLIER,
        )

        while len(frames) < max_blocks:
            data, _ = stream.read(blocksize)
            data = bytes(data)
            level = _rms_level(data)
            pre_roll.append(data)

            if not speech_started:
                waited_blocks += 1
                if level >= speech_threshold:
                    speech_started = True
                    frames.extend(pre_roll)
                    silence_blocks = 0
                elif waited_blocks >= start_timeout_blocks:
                    break
                continue

            frames.append(data)

            if level < speech_threshold:
                silence_blocks += 1
                if silence_blocks >= silence_blocks_required:
                    break
            else:
                silence_blocks = 0

    if not frames:
        return _write_wav([b"\x00\x00"] * blocksize)

    return _write_wav(frames)


def transcribe_command() -> str:
    logger = logging.getLogger("jarvis.listener")
    logger.info("Ouvindo o comando...")
    path = _record_audio()
    try:
        model = _get_whisper_model()
        segments, _ = model.transcribe(
            path,
            language="pt",
            beam_size=5,
            temperature=0,
            condition_on_previous_text=False,
            initial_prompt=WHISPER_INITIAL_PROMPT,
            hotwords=WHISPER_HOTWORDS or None,
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": 500,
            },
        )
        text = " ".join(segment.text.strip() for segment in segments).strip()
        logger.info("Transcrição: %s", text)
        return text
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
