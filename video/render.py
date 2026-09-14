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
