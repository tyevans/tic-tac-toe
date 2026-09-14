import os
import wave
from pathlib import Path

import numpy as np
import requests

from manim_voiceover._typing import VoiceoverData
from manim_voiceover.helper import remove_bookmarks
from manim_voiceover.services.base import PathLike, SpeechService, path_to_string

DEFAULT_WHISPER_URL = "http://192.168.1.14:8083"
DEFAULT_VOICE_SPEC = "af_heart"

_MODEL_DIR = Path(__file__).resolve().parent.parent / "model"
_KOKORO_MODEL = _MODEL_DIR / "kokoro-v1.0.int8.onnx"
_KOKORO_VOICES = _MODEL_DIR / "voices-v1.0.bin"

_kokoro = None


def parse_voice_spec(spec):
    spec = spec.strip()
    if not spec:
        raise ValueError("voice spec is empty")
    pairs = []
    for chunk in spec.split(";"):
        chunk = chunk.strip()
        if not chunk:
            raise ValueError("empty voice entry in: " + spec)
        parts = chunk.split(",")
        if len(parts) > 2:
            raise ValueError("too many commas in: " + chunk)
        name = parts[0].strip()
        if not name:
            raise ValueError("missing voice name in: " + chunk)
        weight = 1.0
        if len(parts) == 2:
            try:
                weight = float(parts[1].strip())
            except ValueError:
                raise ValueError("non-numeric weight in: " + chunk)
            if weight <= 0:
                raise ValueError("non-positive weight in: " + chunk)
        pairs.append((name, weight))
    total = sum(w for _, w in pairs)
    return [(n, w / total) for n, w in pairs]


def _kokoro_pipeline():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro

        _kokoro = Kokoro(str(_KOKORO_MODEL), str(_KOKORO_VOICES))
    return _kokoro


def _voice_arg(pairs):
    if len(pairs) == 1:
        return pairs[0][0]
    pipe = _kokoro_pipeline()
    vec = None
    for name, weight in pairs:
        style = pipe.get_voice_style(name)
        vec = style * weight if vec is None else vec + style * weight
    return vec


def _write_wav(path, audio, sr):
    audio = np.asarray(audio, dtype=np.float32)
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > 0:
        audio = audio * (0.9 / peak)
    pcm = np.clip(audio * 32767.0, -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(int(sr))
        w.writeframes(pcm.tobytes())


class _RemoteTranscription:
    def __init__(self, payload):
        self.text = (payload.get("text") or "").strip()
        self._segments = payload.get("segments") or []

    def segments_to_dicts(self):
        return [
            {
                "words": [
                    {"word": w.get("word", ""), "start": float(w.get("start", 0.0))}
                    for w in (seg.get("words") or [])
                ]
            }
            for seg in self._segments
        ]


class RemoteWhisperModel:
    def __init__(self, url):
        self._url = url

    def transcribe(self, audio_path, **kwargs):
        url = self._url.rstrip("/")
        with open(audio_path, "rb") as f:
            resp = requests.post(
                url + "/inference",
                files={"file": f},
                data={"response_format": "verbose_json"},
                timeout=300,
            )
        resp.raise_for_status()
        return _RemoteTranscription(resp.json())


class KokoroService(SpeechService):
    def __init__(self, voice_spec, whisper_url=DEFAULT_WHISPER_URL, global_speed=1.0, cache_dir=None):
        self._whisper_url = whisper_url
        self.voice = parse_voice_spec(voice_spec)
        super().__init__(global_speed=global_speed, cache_dir=cache_dir, transcription_model=None)
        self._whisper_model = RemoteWhisperModel(self._whisper_url)

    def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
        if cache_dir is None:
            cache_dir = self.cache_dir
        input_text = remove_bookmarks(text)
        input_data = {
            "input_text": input_text,
            "service": "kokoro",
            "config": {"voice": [[n, w] for n, w in self.voice], "speed": self.global_speed},
        }
        cached = self.get_cached_result(input_data, cache_dir)
        if cached is not None and (Path(cache_dir) / cached["original_audio"]).exists():
            return cached
        if path is None:
            audio_path = self.get_audio_basename(input_data) + ".wav"
        else:
            audio_path = path_to_string(path)
        audio, sr = _kokoro_pipeline().create(
            input_text, voice=_voice_arg(self.voice), speed=self.global_speed, lang="en-us"
        )
        _write_wav(Path(cache_dir) / audio_path, audio, sr)
        return {
            "input_text": text,
            "input_data": input_data,
            "original_audio": audio_path,
        }


def set_voice(scene):
    spec = os.environ.get("VOICE") or DEFAULT_VOICE_SPEC
    url = os.environ.get("WHISPER_URL", DEFAULT_WHISPER_URL)
    scene.set_speech_service(KokoroService(spec, url))
