# Kokoro + Remote-Whisper Voiceover Pipeline — Implementation Plan

**Goal:** Replace the episode voiceover backend in `video/` from GTTS + local-whisper to local Kokoro (ONNX) TTS + remote whisper.cpp transcription, with a render-time-overridable, blendable voice spec; then re-voice + re-render Episode 1 (12 scenes) at 720p30 into a new `video/final/e1.mp4`.

**Architecture:** One module, `video/common/voice.py`, is the single voice wiring point. Every E1 scene calls `set_voice(self)` in `setup()`; `common/__init__.py` re-exports `set_voice`. The rewrite keeps that interface and swaps the internals: a `KokoroService(SpeechService)` for TTS (lazy module-level `kokoro_onnx.Kokoro` singleton), a `RemoteWhisperModel`/`_RemoteTranscription` for STT (POST to `http://192.168.1.14:8083/inference`), and `parse_voice_spec` for the `name,weight;name,weight` blend spec. `set_voice` reads `VOICE`/`WHISPER_URL` env vars (overridable, settable from `render.py`). A thin `video/render.py` wraps `uv run manim render` to pass those vars.

**Tech Stack:** Python 3.13, `uv`, manim 0.19.2, manim-voiceover 0.4.0, `kokoro-onnx` 0.6.1 (onnxruntime + phonemizer, pure-stdlib otherwise), `requests`, ffmpeg 6.1.1 (final mux only). No third-party additions beyond `kokoro-onnx` + `requests`.

## Global Constraints
- Pure-stdlib + the two approved deps only. No new third-party packages.
- No comments and no docstrings in project code (project convention). The code is the documentation.
- `voice.py` remains the only place that wires voice; scenes only call `set_voice(self)`. `common/__init__.py` re-export is unchanged.
- Cache key = `input_data` which includes the resolved `voice` list + `speed` (and `service:"kokoro"`). Different blends never collide; existing GTTS cache entries (`service:"gtts"`) stay intact and unused.
- Kokoro model files live in `video/model/` (gitignored): `kokoro-v1.0.int8.onnx` (92 MB) + `voices-v1.0.bin` (28 MB).
- No LaTeX. Frame 16:9. `-qm` = 720p30, `-ql` = 480p15 (proof only). `global_speed=1.0`.
- No formal test framework (project convention). Red/green for pure logic is done with ad-hoc `uv run python` scripts under `video/_scratch/`. ML/network paths are verified with ad-hoc smoke scripts, not a test suite.
- The whisper.cpp server at `http://192.168.1.14:8083` is assumed reachable. Every STT step first probes it; if it is down, STOP and report (do not fall back to local whisper — the point is to drop it).
- Git: do NOT commit unless the user asks. (Project code in `video/` is currently untracked; the docs/spec/plan under repo-root `docs/` are tracked.)

## Verified environment facts (from the planning spike — do not re-derive)
- `kokoro_onnx` 0.6.1: module is **`kokoro_onnx`** (not `kokoro`), class **`Kokoro`** (not `KPipeline`). `Kokoro(model_path, voices_path)` loads explicit files (no auto-download).
- `Kokoro.create(text, voice, speed=1.0, lang='en-us', ...) -> (float32[1-D] in [-1,1], 24000)`. Single voice = pass the **name string**; blend = **weighted sum of `get_voice_style(name)`** arrays. `get_voice_style(name) -> float32 (510,1,256)`. `get_voices() -> list[str]` (54 voices).
- Real voice names include `af_heart`, `am_michael` (NOT `af_michael`), `am_eric`, `af_bella`, `am_fenrir`.
- whisper.cpp: POST `/inference`, multipart `file=@<audio>` + form field `response_format=verbose_json` → `{"text": str, "segments":[{"id","text","start","end","tokens":[],"words":[{"word","start","end","t_dtw","probability"}]}]}`. Default (no format) returns only `{"text"}` — so the client MUST send `verbose_json`.
- manim-voiceover contract (`services/base.py`): `generate_from_text(text, cache_dir, path, **kwargs) -> dict` with keys `input_text`, `input_data`, `original_audio`; the base `_wrap_generate_from_text` runs transcription via `self._whisper_model.transcribe(str(cache_dir/original_audio), **self.transcription_kwargs)` only when `self._whisper_model is not None`, then needs `result.text` and `result.segments_to_dicts()` where each segment is `{"words":[{"word": str, "start": float}]}`. Passing `transcription_model=None` to the base `__init__` skips the `stable_whisper` import entirely.
- `stable_whisper`/openai-whisper are NOT installed (extras slimmed). `kokoro_onnx`, `requests`, `numpy` ARE installed. `import common` resolves with `PYTHONPATH=.` (cwd = `video/`).
- Render command form (verified by `-n 0,0` dry-run): `PYTHONPATH=. uv run manim render -qm episodes/e1/<file>.py <SceneClass>`.
- The 12 E1 scenes: `e1s1_series_intro.py:E1S1SeriesIntro`, `e1s2_game_rules.py:E1S2GameRules`, `e1s3_domain_words.py:E1S3DomainWords`, `e1s4_player.py:E1S4Player`, `e1s5_position.py:E1S5Position`, `e1s6_cell_and_board.py:E1S6CellAndBoard`, `e1s7_board_queries.py:E1S7BoardQueries`, `e1s8_error_family.py:E1S8ErrorFamily`, `e1s9_game_aggregate.py:E1S9GameAggregate`, `e1s10_place_mark.py:E1S10PlaceMark`, `e1s11_immutability.py:E1S11Immutability`, `e1s12_closing_hook.py:E1S12ClosingHook`. (`_voiceover_ref.py` is a dev reference, not one of the 12.)

---

## Task 1: Dependencies + model files (verify; already applied in the spike)

These were applied during planning. Re-run to confirm a clean, reproducible state; they are idempotent.

**Files:**
- Modify (already done): `video/pyproject.toml`
- Present (already downloaded, gitignored): `video/model/kokoro-v1.0.int8.onnx`, `video/model/voices-v1.0.bin`
- Modify (already committed): `.gitignore` (repo root) — includes `video/model/` and `video/media/`

**Steps:**
- [ ] Confirm `video/pyproject.toml` `dependencies` block is exactly:
  ```toml
  dependencies = [
      "manim>=0.19,<0.20",
      "manim-voiceover>=0.4.0",
      "kokoro-onnx>=0.6.1",
      "requests>=2.31",
  ]
  ```
  If it still reads `manim-voiceover[gtts,transcribe]` or lacks `kokoro-onnx`/`requests`, set it to the block above.
- [ ] Sync (idempotent):
  ```
  cd video && uv sync
  ```
- [ ] If the model files are missing, download them:
  ```
  cd video && mkdir -p model
  curl -L -o model/kokoro-v1.0.int8.onnx "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx"
  curl -L -o model/voices-v1.0.bin "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
  ```
- [ ] Verify deps + model load:
  ```
  cd video && uv run python -c "import kokoro_onnx, requests, numpy; from kokoro_onnx import Kokoro; k=Kokoro('model/kokoro-v1.0.int8.onnx','model/voices-v1.0.bin'); vs=k.get_voices(); print('voices', len(vs), 'af_heart' in vs, 'am_michael' in vs)"
  ```
  Expected: `voices 54 True True`
- [ ] Verify local whisper is gone (slim worked):
  ```
  cd video && uv run python -c "import importlib.util as u; print('stable_whisper_present', u.find_spec('stable_whisper') is not None)"
  ```
  Expected: `stable_whisper_present False`

## Task 2: Rewrite `video/common/voice.py` (TDD on `parse_voice_spec` + full module)

**Files:**
- Create scratch test: `video/_scratch/test_parse_voice_spec.py`
- Modify (full rewrite): `video/common/voice.py` (currently a 5-line GTTS wrapper)

**Steps:**
- [ ] Write the failing test `video/_scratch/test_parse_voice_spec.py`:
  ```python
  from common.voice import parse_voice_spec


  def close(a, b):
      return len(a) == len(b) and all(x[0] == y[0] and abs(x[1] - y[1]) < 1e-9 for x, y in zip(a, b))


  def main():
      assert close(parse_voice_spec("af_heart"), [("af_heart", 1.0)])
      assert close(parse_voice_spec("af_michael,0.75"), [("af_michael", 1.0)])
      assert close(parse_voice_spec("af_michael,0.75;af_heart,0.25"), [("af_michael", 0.75), ("af_heart", 0.25)])
      assert close(parse_voice_spec("am_michael,3;af_heart,1"), [("am_michael", 0.75), ("af_heart", 0.25)])
      assert close(parse_voice_spec(" a , 0.6 ; b , 0.4 "), [("a", 0.6), ("b", 0.4)])
      for bad in ["", "   ", "af_heart,,0.5", "af_heart,0", "af_heart,-1", "af_heart,x", "af_heart;"]:
          try:
              parse_voice_spec(bad)
          except ValueError:
              continue
          raise AssertionError("no raise for " + repr(bad))
      print("parse_voice_spec OK")


  main()
  ```
- [ ] Run it and confirm it FAILS (current `voice.py` has no `parse_voice_spec`):
  ```
  cd video && PYTHONPATH=. uv run python _scratch/test_parse_voice_spec.py
  ```
  Expected: `ImportError: cannot import name 'parse_voice_spec'` (RED)
- [ ] Replace `video/common/voice.py` entirely with:
  ```python
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
  ```
- [ ] Re-run the test — expect GREEN:
  ```
  cd video && PYTHONPATH=. uv run python _scratch/test_parse_voice_spec.py
  ```
  Expected: `parse_voice_spec OK`
- [ ] Import smoke (module + constants import cleanly, no kokoro import triggered yet):
  ```
  cd video && PYTHONPATH=. uv run python -c "import common.voice as v; print(v.DEFAULT_VOICE_SPEC, v.DEFAULT_WHISPER_URL, v.parse_voice_spec('am_michael,0.7;af_heart,0.3'))"
  ```
  Expected: `af_heart http://192.168.1.14:8083 [('am_michael', 0.7), ('af_heart', 0.3)]`

## Task 3: Kokoro synthesis + WAV writer (smoke, no server)

Verifies the TTS path and `_write_wav` produce a valid 24 kHz int16 mono WAV (single voice and a blend).

**Steps:**
- [ ]
  ```
  cd video && PYTHONPATH=. uv run python -c "
  import common.voice as v
  import numpy as np, wave, os
  a, sr = v._kokoro_pipeline().create('Hello world, welcome to the series.', voice='af_heart', speed=1.0, lang='en-us')
  v._write_wav('/tmp/_kokoro_single.wav', a, sr)
  blend = v._voice_arg([('am_michael',0.7),('af_heart',0.3)])
  b, sr2 = v._kokoro_pipeline().create('Hello world, welcome to the series.', voice=blend, speed=1.0, lang='en-us')
  v._write_wav('/tmp/_kokoro_blend.wav', b, sr2)
  for p in ('/tmp/_kokoro_single.wav','/tmp/_kokoro_blend.wav'):
      with wave.open(p) as w: print(p, w.getnchannels(), w.getsampwidth(), w.getframerate(), os.path.getsize(p))
  print('OK')
  "
  ```
  Expected: two lines each `1 2 24000 <bytes>` then `OK`. (Channels=1, sample width=2, rate=24000, size>0.)

## Task 4: Remote whisper transcription (smoke; needs the server)

Verifies the remote STT contract: probe the server, POST a real WAV with `verbose_json`, and confirm the `TranscriptionResult` shape the base consumes.

**Steps:**
- [ ] Probe + transcribe the Task-3 WAV through `RemoteWhisperModel`:
  ```
  cd video && PYTHONPATH=. uv run python -c "
  import common.voice as v
  m = v.RemoteWhisperModel(v.DEFAULT_WHISPER_URL)
  r = m.transcribe('/tmp/_kokoro_single.wav')
  segs = r.segments_to_dicts()
  print('text_len', len(r.text))
  print('segments', len(segs))
  print('first_words', segs[0]['words'][:3])
  assert r.text and segs and all('word' in w and 'start' in w for s in segs for w in s['words'])
  print('WHISPER_OK')
  "
  ```
  Expected: `text_len <n>`, `segments >=1`, `first_words [...]` of `{'word':..., 'start':...}`, then `WHISPER_OK`.
  - If the request times out or connection fails: the server is down. STOP, report to the user, and do not proceed to Tasks 5-9.

## Task 5: `KokoroService` end-to-end (TTS + cache + STT word boundaries)

Verifies the full `SpeechService` path: `generate_from_text` writes a WAV into the cache dir, and the base `_wrap_generate_from_text` attaches `word_boundaries` + `transcribed_text` via the remote model (the integration point that was failing under GTTS).

**Steps:**
- [ ]
  ```
  cd video && PYTHONPATH=. uv run python -c "
  import common.voice as v
  svc = v.KokoroService('af_heart')
  d = svc._wrap_generate_from_text('Hello world, welcome to the series.')
  print('original_audio', d['original_audio'])
  print('has_final_audio', d.get('final_audio'))
  print('transcribed', repr(d.get('transcribed_text',''))[:60])
  print('word_boundaries', len(d.get('word_boundaries', [])))
  assert d['original_audio'].endswith('.wav')
  assert d.get('word_boundaries'), 'expected word_boundaries from remote whisper'
  print('E2E_OK')
  "
  ```
  Expected: `original_audio <slug>-<hash>.wav`, `has_final_audio <...>.wav`, `transcribed '...'`, `word_boundaries <n>` (>0), `E2E_OK`.
- [ ] Confirm cache reuse (second call for the same text must NOT re-synthesize or re-transcribe; the entry is served from `media/voiceovers/cache.json`):
  ```
  cd video && PYTHONPATH=. uv run python -c "
  import common.voice as v
  svc = v.KokoroService('af_heart')
  d1 = svc._wrap_generate_from_text('Hello world, welcome to the series.')
  d2 = svc._wrap_generate_from_text('Hello world, welcome to the series.')
  assert d1['original_audio'] == d2['original_audio']
  print('cache_key_stable', d2['original_audio'])
  print('CACHE_OK')
  "
  ```
  Expected: `cache_key_stable <same>.wav` then `CACHE_OK`. (The second call returns the cached entry, which already carries `word_boundaries`, so transcription is skipped.)

## Task 6: `set_voice` wiring + re-export

Verifies `set_voice` installs a `KokoroService` with the correct voice + a `RemoteWhisperModel` (no `stable_whisper`), honors the `VOICE`/`WHISPER_URL` env vars, and that `from common import set_voice` still works.

**Steps:**
- [ ]
  ```
  cd video && PYTHONPATH=. uv run python -c "
  import os
  import common.voice as v
  class S:
      def __init__(self): self._svc = None
      def set_speech_service(self, svc): self._svc = svc
  os.environ['VOICE'] = 'am_michael,0.7;af_heart,0.3'
  os.environ['WHISPER_URL'] = 'http://127.0.0.1:9999'
  s = S(); v.set_voice(s)
  svc = s._svc
  print('type', type(svc).__name__)
  print('voice', svc.voice)
  print('wm_type', type(svc._whisper_model).__name__)
  print('wm_url', svc._whisper_model._url)
  assert type(svc).__name__ == 'KokoroService'
  assert svc.voice == [('am_michael', 0.7), ('af_heart', 0.3)]
  assert type(svc._whisper_model).__name__ == 'RemoteWhisperModel'
  assert svc._whisper_model._url == 'http://127.0.0.1:9999'
  print('WIRE_OK')
  "
  ```
  Expected: `type KokoroService`, `voice [('am_michael', 0.7), ('af_heart', 0.3)]`, `wm_type RemoteWhisperModel`, `wm_url http://127.0.0.1:9999`, `WIRE_OK`.
- [ ] Default path (no `VOICE`/`WHISPER_URL` set → `DEFAULT_VOICE_SPEC` + `DEFAULT_WHISPER_URL`):
  ```
  cd video && PYTHONPATH=. env -u VOICE -u WHISPER_URL uv run python -c "
  import common.voice as v
  class S:
      def set_speech_service(self, svc): self._svc = svc
  s = S(); v.set_voice(s)
  assert s._svc.voice == [('af_heart', 1.0)], s._svc.voice
  assert s._svc._whisper_model._url == 'http://192.168.1.14:8083'
  print('DEFAULT_OK', s._svc.voice)
  "
  ```
  Expected: `DEFAULT_OK [('af_heart', 1.0)]`
- [ ] Re-export intact:
  ```
  cd video && PYTHONPATH=. uv run python -c "from common import set_voice; print('reexport_ok', set_voice.__module__)"
  ```
  Expected: `reexport_ok common.voice`

## Task 7: `video/render.py` thin CLI

A small wrapper so a voice/whisper override doesn't have to be typed on every command. It forwards to `uv run manim render` and injects `VOICE`/`WHISPER_URL`. `--dry-run` prints the composed command instead of running it.

**Files:**
- Create: `video/render.py`

**Steps:**
- [ ] Create `video/render.py`:
  ```python
  import os
  import shlex
  import sys


  def parse_args(argv):
      voice = None
      whisper_url = None
      quality = None
      dry_run = False
      rest = []
      i = 0
      while i < len(argv):
          a = argv[i]
          if a == "--voice":
              i += 1
              voice = argv[i]
          elif a.startswith("--voice="):
              voice = a.split("=", 1)[1]
          elif a == "--whisper-url":
              i += 1
              whisper_url = argv[i]
          elif a.startswith("--whisper-url="):
              whisper_url = a.split("=", 1)[1]
          elif a.startswith("--quality="):
              quality = a.split("=", 1)[1]
          elif a == "--quality":
              i += 1
              quality = argv[i]
          elif a == "--dry-run":
              dry_run = True
          else:
              rest.append(a)
          i += 1
      return voice, whisper_url, quality, dry_run, rest


  def main():
      voice, whisper_url, quality, dry_run, rest = parse_args(sys.argv[1:])
      if "--help" in rest or "-h" in rest:
          print("usage: render.py [--voice SPEC] [--whisper-url URL] [--quality=qc] [manim args...]")
          print("  forwards to: uv run manim render [manim args...]")
          print("  e.g. render.py --voice af_heart --quality=ql episodes/e1/e1s1_series_intro.py E1S1SeriesIntro")
          return 0
      qflag = "-qm" if quality is None else "-" + quality
      args = ["render", qflag, "--disable_caching", *rest]
      env = dict(os.environ)
      if voice is not None:
          env["VOICE"] = voice
      if whisper_url is not None:
          env["WHISPER_URL"] = whisper_url
      full = ["uv", "run", "manim"] + args
      if dry_run:
          print(" ".join(shlex.quote(x) for x in full))
          print("VOICE=" + (voice or "<default>") + "  WHISPER_URL=" + (whisper_url or "<default>"))
          return 0
      os.execvpe("uv", full, {**env, "PYTHONPATH": "."})


  if __name__ == "__main__":
      sys.exit(main())
  ```
- [ ] Verify the dry-run composes the right manim command + env (no render executed):
  ```
  cd video && PYTHONPATH=. uv run python render.py --voice 'am_michael,0.7;af_heart,0.3' --quality=ql --dry-run episodes/e1/e1s1_series_intro.py E1S1SeriesIntro
  ```
  Expected:
  ```
  uv run manim render -ql --disable_caching episodes/e1/e1s1_series_intro.py E1S1SeriesIntro
  VOICE=am_michael,0.7;af_heart,0.3  WHISPER_URL=<default>
  ```
- [ ] Verify `--help`:
  ```
  cd video && PYTHONPATH=. uv run python render.py --help
  ```
  Expected: the usage block, exit 0.

## Task 8: Proof-render E1S1 in 3 candidate voices (DECISION GATE — stop for the user)

Render `E1S1SeriesIntro` at `-ql` (480p15, fast) in 3 distinct voices so the user can pick by ear. Each render re-voices + re-renders the scene with the new Kokoro/remote-whisper pipeline (this is also the first full real render of the new stack).

**Steps:**
- [ ] Confirm the whisper server is up (reuse Task 4 if already green this session):
  ```
  cd video && PYTHONPATH=. uv run python -c "import common.voice as v; print(v.RemoteWhisperModel(v.DEFAULT_WHISPER_URL).transcribe('/tmp/_kokoro_single.wav').text[:40])"
  ```
  If it fails, STOP and tell the user the whisper server is unreachable.
- [ ] Render three `-ql` proof clips (separate media dirs so their voiceover caches don't interfere). This synthesizes + transcribes each, then renders:
  ```
  cd video && PYTHONPATH=. VOICE=af_heart      uv run manim render -ql --disable_caching --media_dir media/proof_af_heart      episodes/e1/e1s1_series_intro.py E1S1SeriesIntro
  cd video && PYTHONPATH=. VOICE=am_michael    uv run manim render -ql --disable_caching --media_dir media/proof_am_michael    episodes/e1/e1s1_series_intro.py E1S1SeriesIntro
  cd video && PYTHONPATH=. VOICE=am_eric       uv run manim render -ql --disable_caching --media_dir media/proof_am_eric       episodes/e1/e1s1_series_intro.py E1S1SeriesIntro
  ```
  (Swap in other `VOICE=` values on request — any of the 54 names from `Kokoro.get_voices()`, or a blend like `am_michael,0.7;af_heart,0.3`.)
- [ ] Confirm the three mp4s exist with audio tracks:
  ```
  cd video && for d in af_heart am_michael am_eric; do f=$(ls media/proof_$d/videos/e1s1_series_intro/480p15/E1S1SeriesIntro.mp4 2>/dev/null); echo "$d -> ${f:-MISSING}"; [ -n "$f" ] && ffprobe -v error -select_streams a -show_entries stream=codec_name -of csv=p=0 "$f"; done
  ```
  Expected: three paths (not MISSING), each with an audio codec line.
- [ ] **STOP and present the three proof files to the user** with paths:
  - `video/media/proof_af_heart/videos/e1s1_series_intro/480p15/E1S1SeriesIntro.mp4`
  - `video/media/proof_am_michael/videos/e1s1_series_intro/480p15/E1S1SeriesIntro.mp4`
  - `video/media/proof_am_eric/videos/e1s1_series_intro/480p15/E1S1SeriesIntro.mp4`
  Ask which voice (or blend) to use for the full re-render. Do not proceed to Task 9 until the user chooses.

## Task 9: Re-voice + re-render all 12 E1 scenes at 720p30, mux final

After the user picks a voice: set it as the default, re-voice + re-render all 12 scenes at `-qm`, and concatenate into `video/final/e1.mp4`.

**Steps:**
- [ ] Set `DEFAULT_VOICE_SPEC` in `video/common/voice.py` to the user's chosen voice (replace the current `"af_heart"`). This makes the chosen voice the standing default; individual runs can still override with `VOICE=`.
- [ ] Re-voice + re-render all 12 scenes at `-qm` (720p30). TTS + whisper results are cached per scene narration, so re-runs are cheap. Run 2-at-a-time in the background to bound memory/CPU:
  ```
  cd video && PYTHONPATH=. bash -c '
  files=(
    "e1s1_series_intro.py:E1S1SeriesIntro"
    "e1s2_game_rules.py:E1S2GameRules"
    "e1s3_domain_words.py:E1S3DomainWords"
    "e1s4_player.py:E1S4Player"
    "e1s5_position.py:E1S5Position"
    "e1s6_cell_and_board.py:E1S6CellAndBoard"
    "e1s7_board_queries.py:E1S7BoardQueries"
    "e1s8_error_family.py:E1S8ErrorFamily"
    "e1s9_game_aggregate.py:E1S9GameAggregate"
    "e1s10_place_mark.py:E1S10PlaceMark"
    "e1s11_immutability.py:E1S11Immutability"
    "e1s12_closing_hook.py:E1S12ClosingHook"
  );
  for chunk in "${files[@]:0:2}" "${files[@]:2:2}" "${files[@]:4:2}" "${files[@]:6:2}" "${files[@]:8:2}" "${files[@]:10:2}"; do
    pids=();
    for pair in $chunk; do
      f="${pair%%:*}"; c="${pair##*:}";
      uv run manim render -qm --disable_caching "episodes/e1/$f" "$c" &
      pids+=($!);
    done;
    wait "${pids[@]}";
  done
  '
  ```
  Watch for any scene that fails; re-run just that one (its voiceover is cached, so only the render redoes).
- [ ] Verify all 12 mp4s exist at 720p30:
  ```
  cd video && for f in media/videos/e1s*/720p30/*.mp4; do echo "$f"; done | wc -l
  ```
  Expected: `12`
- [ ] Concatenate the 12 clips, in scene order, into the final. Create `video/media/concat_e1.txt` listing the 12 mp4 paths in order, then:
  ```
  cd video && printf "file '%s'\n" \
    media/videos/e1s1_series_intro/720p30/E1S1SeriesIntro.mp4 \
    media/videos/e1s2_game_rules/720p30/E1S2GameRules.mp4 \
    media/videos/e1s3_domain_words/720p30/E1S3DomainWords.mp4 \
    media/videos/e1s4_player/720p30/E1S4Player.mp4 \
    media/videos/e1s5_position/720p30/E1S5Position.mp4 \
    media/videos/e1s6_cell_and_board/720p30/E1S6CellAndBoard.mp4 \
    media/videos/e1s7_board_queries/720p30/E1S7BoardQueries.mp4 \
    media/videos/e1s8_error_family/720p30/E1S8ErrorFamily.mp4 \
    media/videos/e1s9_game_aggregate/720p30/E1S9GameAggregate.mp4 \
    media/videos/e1s10_place_mark/720p30/E1S10PlaceMark.mp4 \
    media/videos/e1s11_immutability/720p30/E1S11Immutability.mp4 \
    media/videos/e1s12_closing_hook/720p30/E1S12ClosingHook.mp4 \
    > media/concat_e1.txt
  cd video && ffmpeg -y -f concat -safe 0 -i media/concat_e1.txt -c copy final/e1.mp4
  ```
  (If the concat-copy produces A/V drift, re-encode: replace `-c copy` with `-c:v libx264 -crf 18 -c:a aac`.)
- [ ] Verify the final: duration, resolution, audio present.
  ```
  cd video && ffprobe -v error -show_entries format=duration:stream=width,height,codec_type -of default=noprint_wrappers=1 final/e1.mp4
  ```
  Expected: `video` stream `width=1280 height=720`, an `audio` stream, and a duration in the same ballpark as the previous `final/e1.mp4` (the Kokoro narration length sets the timeline; expect it to differ from the GTTS version).
- [ ] Report the new `video/final/e1.mp4` path + duration to the user. (Optionally move the previous file aside if the user wants to keep it, e.g. it is already saved as `final/e1_draft.mp4` alongside.)

## Rollback
The change is isolated to `video/common/voice.py` (plus new `video/render.py`, `video/pyproject.toml`, `video/_scratch/`). To revert to the old stack: restore `voice.py` to its 5-line GTTS form and restore `pyproject.toml` to `manim-voiceover[gtts,transcribe]`, then `uv sync`. No scene or `common/__init__.py` changes are required to go either way.
