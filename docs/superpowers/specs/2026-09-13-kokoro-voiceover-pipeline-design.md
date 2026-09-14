# Design: Kokoro TTS + remote-whisper voiceover pipeline

- Date: 2026-09-13
- Status: approved (design), pending implementation plan
- Scope: `video/` package only. No changes to the `src/tictactoe` domain package.

## Goal

Replace the episode voiceover backend from **GTTS + local whisper** to **Kokoro
(local ONNX) TTS + remote whisper.cpp transcription**, with a **render-time
overridable, blendable voice** option. Then re-voice and re-render Episode 1 at
720p30.

## Non-goals

- **Intel Xe / VAAPI encode.** manim CE renders frames on the CPU (Cairo). The iGPU
  can only accelerate the ffmpeg *encode* step (a small slice), and manim CE does not
  cleanly expose encoder selection. Not worth it.
- **Domain code.** No changes to `src/tictactoe`.
- **Scene content/layout.** Scenes are unchanged; only the audio (and the word-timings
  that follow from it) change.
- **`global_speed` / SoX.** Keep `global_speed=1.0`. manim-voiceover only invokes SoX
  when speed != 1; we do not add a SoX dependency.

## Background / current state

- Every scene subclasses `VoiceoverScene` and calls `set_voice(self)` in `setup()`:
  - `video/episodes/e1/e1s1_series_intro.py:18`
- `video/common/voice.py` is the single wiring point:
  ```python
  from manim_voiceover.services.gtts import GTTSService
  def set_voice(scene) -> None:
      scene.set_speech_service(GTTSService(transcription_model="base"))
  ```
- manim-voiceover's `SpeechService` cleanly separates the two jobs:
  - **TTS**: `generate_from_text(text, cache_dir, path, **kwargs) -> VoiceoverData`
    (abstract, implemented per-service).
  - **Transcription**: `_wrap_generate_from_text` calls
    `self._whisper_model.transcribe(str(cache_dir/original_audio),
    **self.transcription_kwargs)`, then `.text` + `.segments_to_dicts()` →
    `timestamps_to_word_boundaries(...)`.
- `WhisperModel` protocol (what `_whisper_model` must satisfy):
  ```python
  class WhisperModel(Protocol):
      def transcribe(self, audio_path: str, **kwargs: object) -> TranscriptionResult: ...
  ```
  where `TranscriptionResult` exposes `.text: str` and
  `.segments_to_dicts() -> list[TranscriptionSegment]`, and each segment dict has
  `"words": list[{"word", "start", "end"}]`.
- `SpeechService.__init__(global_speed, cache_dir, transcription_model,
  transcription_kwargs, **kwargs)` calls `self.set_transcription(model, kwargs)`.
  The base `set_transcription` imports `stable_whisper` (the local whisper path we
  want to drop). We override it.
- Caching: each service's `generate_from_text` checks
  `self.get_cached_result(input_data, self.cache_dir)` internally; the cache key is
  the serialized `input_data` (`input_text` + `service` + `config`). `_wrap_generate_from_text`
    appends the (possibly cached) entry to `media/voiceovers/cache.json`.

### The remote transcription backend (verified)

- Server: stock `ggml-org/whisper.cpp` at `http://192.168.1.14:8083`.
- It serves the **OpenAI-Whisper-API** shape. `POST /inference` with multipart
  `file=@<audio>` and `response_format=verbose_json` returns:
  ```json
  {"task": "transcribe", "language": "english", "duration": 15.4, "text": "...",
   "segments": [{"id":0,"text":"...","start":0.0,"end":1.94,
                 "words":[{"word":" A","start":0.08,"end":0.08,"probability":0.81}]}]}
  ```
  `segments[].words[]` with `word`/`start`/`end` is exactly the shape
  `timestamps_to_word_boundaries` consumes. The default response (no
  `response_format`) is only `{"text": "..."}` (no timings) — so the client must
  always send `response_format=verbose_json`.
- Audio in: Kokoro emits 24 kHz mono WAV; whisper.cpp decodes WAV natively.
- `requests` is already importable in the `video/` venv (use it; do not add httpx).

### The TTS backend (verified)

- Package: `kokoro-onnx` 0.6.1 (top-level module **`kokoro_onnx`**, class
  **`kokoro_onnx.Kokoro`**). Resolves to `onnxruntime 1.30.0`, `phonemizer 3.4.0`,
  `espeakng-loader 0.2.4` (bundles the espeak lib — **no system install**), numpy
  (2.5.3; manim 0.19.2 already runs on it).
- The model is **not bundled**: `Kokoro(model_path, voices_path)` loads explicit
  files. Download once from the `model-files-v1.0` release into `video/model/`:
  - `kokoro-v1.0.int8.onnx` (~92 MB, int8 — smaller/faster on CPU)
  - `voices-v1.0.bin` (~28 MB, `np.load`-able; 54 voices, e.g. `af_heart`, `am_michael`)
- API (verified on this machine):
  - `Kokoro(model_path, voices_path)`
  - `create(text, voice, speed=1.0, lang="en-us", ...) -> (audio: float32[1-D], 24000)`
  - `voice` is either a **name string** (single voice) **or** a `float32` style
    vector; `get_voice_style(name) -> float32 (510,1,256)`, `get_voices() -> list[str]`.
    Blending = weighted sum of the per-voice style vectors.
- No system `espeak-ng` needed. No numpy conflict.

## Design

### Components (all in `video/common/voice.py`)

1. **`parse_voice_spec(spec: str) -> list[tuple[str, float]]`**
   - Splits on `;` into per-voice pairs; each pair splits on `,` into
     `(name, weight?)`. A bare name means weight 1.0.
   - Always normalize weights so they sum to 1.0 (a lone `af_michael,0.75` becomes
     full-strength `af_michael`).
   - Raises `ValueError` on malformed input (empty, extra commas, non-numeric or
     non-positive weight, unknown delimiters).
   - Examples:
     - `"af_heart"` → `[("af_heart", 1.0)]`
     - `"af_michael,0.75"` → `[("af_michael", 1.0)]` (single voice; the 0.75 is
       normalized to 1.0)
     - `"af_michael,0.75;af_heart,0.25"` → `[("af_michael", 0.75), ("af_heart", 0.25)]`

2. **`RemoteWhisperModel`** (implements the `WhisperModel` protocol)
   - `__init__(self, url: str)`.
   - `transcribe(self, audio_path: str, **kwargs) -> _RemoteTranscription`:
     - `requests.post(f"{url}/inference", files={"file": open(audio_path,"rb")},
       data={"response_format": "verbose_json"})`; raise on non-200 (include body).
     - Parse JSON, return `_RemoteTranscription` with:
       - `.text` = `data["text"]`
       - `.segments_to_dicts()` →
         `[{"words": [{"word": w["word"], "start": w["start"], "end": w["end"]}
           for w in seg["words"]]} for seg in data["segments"]]`

3. **`KokoroService(SpeechService)`**
   - `__init__(self, voice_spec, whisper_url=DEFAULT_WHISPER_URL, global_speed=1.0,
     cache_dir=None)`:
     - `self.voice = parse_voice_spec(voice_spec)` (list of `(name, weight)`).
     - store `self._whisper_url = whisper_url` **before** `super().__init__` (the
       base `__init__` calls `set_transcription`, which we override to read the URL).
     - `super().__init__(global_speed=global_speed, cache_dir=cache_dir,
       transcription_model="__remote__", transcription_kwargs={})`.
   - `set_transcription(self, model=None, kwargs=None)` — **override** to set
     `self._whisper_model = RemoteWhisperModel(self._whisper_url)`, then
     `self.transcription_model = model`, `self.transcription_kwargs = kwargs or {}`.
     (Bypasses the `stable_whisper` import entirely.)
   - `generate_from_text(self, text, cache_dir=None, path=None, **kwargs)`:
     - `input_text = remove_bookmarks(text)`
     - `input_data = {"input_text": input_text, "service": "kokoro",
       "config": {"voice": [[n, w] for n, w in self.voice], "speed": self.global_speed}}`
     - cache check: `cached = self.get_cached_result(input_data, self.cache_dir)`;
       if `cached` and `Path(self.cache_dir)/cached["original_audio"]` exists → return
       `cached`.
     - `basename = self.get_audio_basename(input_data)`; `audio_path = f"{basename}.wav"`
     - synthesize via the lazily-cached `KPipeline` (see below), write 24 kHz mono
       int16 WAV to `Path(self.cache_dir)/audio_path`.
     - return `{"input_text": text, "input_data": input_data,
       "original_audio": audio_path}`
    - **Kokoro pipeline singleton** (module-level, lazy): build
      `kokoro_onnx.Kokoro(model_path, voices_path)` once per render process (paths
      default to `video/model/`, overridable via `KOKORO_MODEL`/`KOKORO_VOICES`).
      Synthesize with `create(text, voice, speed)` — name string for a single voice,
      weighted `get_voice_style` vectors for a blend — and write the returned `float32`
      as a 24 kHz int16 mono WAV via stdlib `wave` (no new audio dep).

4. **`set_voice(scene)`**
   - `spec = os.environ.get("VOICE") or DEFAULT_VOICE_SPEC`
   - `url = os.environ.get("WHISPER_URL", DEFAULT_WHISPER_URL)`
   - `scene.set_speech_service(KokoroService(spec, url))`
   - `DEFAULT_WHISPER_URL = "http://192.168.1.14:8083"`
   - `DEFAULT_VOICE_SPEC = "af_heart"` (placeholder until the audition picks a voice)

### Files changed

- **`video/pyproject.toml`** — add `kokoro-onnx`; slim `manim-voiceover[gtts,transcribe]`
  → `manim-voiceover` (drops the now-unused GTTS and local `stable_whisper`/torch deps;
  uv re-locks).
- **`video/common/voice.py`** — rewrite as above.
- **`video/common/__init__.py`** — unchanged (still re-exports `set_voice`).
- **`video/render.py`** — new, thin, **optional** CLI wrapper.
- **`video/model/`** — downloaded Kokoro model + voices (int8 `.onnx` ~92 MB,
  `voices-v1.0.bin` ~28 MB); **gitignored**.
- **`.gitignore`** (repo root) — add `video/model/`.
- **No scene file changes.**

### `video/render.py` (thin, optional)

Maps the desired `--voice` flag UX onto the env-var mechanism and forwards to manim,
preserving the existing render/media behavior:

```
render.py [-q {l|m|h}] [--voice SPEC] [--whisper-url URL] <file> <SceneName> [SceneName ...]
```

- `--voice` → env `VOICE`; `--whisper-url` → env `WHISPER_URL`.
- `-q <letter>` → manim `-q<letter>` (`l`=480p15, `m`=720p30, `h`=1080p30).
- Everything else (file, scene names, any extra manim flags) forwarded verbatim to
  `uv run manim render …`, run from `video/`, so the existing `media/` layout and
  output naming are unchanged.
- The env var is the real mechanism; this wrapper only adds the literal `--voice`
  flag. It can be dropped without changing behavior if env vars suffice.

## Voice spec + render-time override

- Format (chosen): `name,weight;name,weight`. `;` separates voices; `,` separates a
  voice's name from its weight; a bare name = full strength.
- Weights auto-normalize to sum 1.0.
- Overridable at render time via `VOICE=…` (set before `manim render`), or
  `render.py --voice …`.
- The parsed blend is part of the cache key (`input_data.config.voice`), so
  different voices/blends never collide, and the existing GTTS cache (keyed
  `service=gtts`) is left intact.

## Delivery plan

1. ~~`uv add kokoro-onnx`; one-line synth to pin the call shape.~~ **Done during the
   design spike:** deps added + `[gtts,transcribe]` slimmed, `video/model/` (int8
   `.onnx` + voices) downloaded, and a real 24 kHz synth + WAV write verified on this
   laptop.
2. Render the **proof scene `E1S1` at `-ql`** with 3 candidate voice specs → 3 short
   audition clips for the user to listen to.
3. User picks the voice → set it as `DEFAULT_VOICE_SPEC`.
4. Re-voice + re-render all 12 of E1 at `-qm` (720p30) in the background
   (2-at-a-time, ~90 min); join → new `video/final/e1.mp4`.
5. Spot-check stills + confirm audio/word-sync; hand the final to the user.

## Risks / open items

- **Model files** (~120 MB, int8) live in gitignored `video/model/`; a fresh checkout
  must download them once (the plan's setup step). If missing, fail with the package's
  own download hint rather than a cryptic ONNX error.
- **Remote server availability** — if `192.168.1.14:8083` is down at render time,
  transcription fails. Fail loud (do not silently fall back to no word-timing);
  ensure the server is up before a batch render.
- **Default voice** is a placeholder until the audition (delivery step 2–3).
- The harmless "SoX not found" warning persists (we keep speed=1.0, so it is not
  invoked).

## Testing / verification

- `parse_voice_spec`: verify with an ad-hoc `uv run python -c` table (malformed +
  valid + normalization cases). No formal test framework is added (consistent with
  the project).
- **Transcription path**: after the proof scene, confirm the manim log line
  `Transcription: …` appears and `word_boundaries`/`transcribed_text` are populated
  from the remote server (i.e., word-sync is driven by the real audio).
- **Proof scene**: listen to the 3 auditions (user), and run
  `uv run python check_layout.py episodes/e1/e1s1_series_intro.py E1S1SeriesIntro`
  to confirm no layout regressions from the re-voice.
- **Final**: spot-check a couple of frames and the joined `video/final/e1.mp4`
  (duration ≈ 9.4 min, 1280×720@30, h264+aac).
