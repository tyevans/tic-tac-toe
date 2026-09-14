# Production Workflow

This document tells a production LLM how to make the videos from the episode files. The procedure is for an LLM that is less capable than the LLM that wrote the plan. Thus the procedure uses small steps, fixed tools, and frequent checks.

## 1. Tool selection

### Recommendation: Manim Community Edition with manim-voiceover

Use [Manim Community Edition](https://docs.manim.community/) (Manim CE) for animation. Use the [manim-voiceover](https://voiceover.manim.community/) plugin for narration.

| Tool | Result | Audio sync | Code on screen | Fit for a less capable LLM |
|------|--------|------------|----------------|----------------------------|
| **Manim CE + manim-voiceover** | MP4 | Yes. Animations wait for bookmarks in the narration. | Yes. `Code` mobject with syntax colors. | Good. Python, many examples in training data, one class for each scene. |
| Motion Canvas | MP4 | Yes, with manual timing | Yes | Medium. TypeScript, fewer examples in training data. |
| Remotion | MP4 | Yes, with manual timing | With extra work | Medium. React, the LLM must calculate frame numbers. |
| Animated SVG (SMIL or CSS) | SVG in a browser | No | No syntax colors | Poor. No timeline, no audio, hard to export to video, errors do not show. |

Reasons for the recommendation:

- The project is Python. The videos show Python code. Manim CE is Python.
- manim-voiceover makes the animation length equal to the narration length. The LLM does not calculate times.
- Each scene is one Python class. The LLM can render and check one scene at a time.
- Manim CE writes a PNG of the last frame (`-s` flag). A multimodal LLM can look at the PNG and find layout errors.

Use animated SVG only for small images in the blog articles. Do not use animated SVG for the videos.

### Hazards for the production LLM

- **Two libraries have the name "manim".** Use only Manim CE: `from manim import *`. Do not use `manimlib` or `manimgl`. The two APIs are different.
- **The Manim CE API changes.** Pin the version in `pyproject.toml`. Before you use a class, read its signature in the installed version (step 3.4).
- **LaTeX.** `MathTex` and `Tex` need a LaTeX installation. Use `Text` with Unicode symbols (`π`, `Σ`, `∂`, `·`, `−`) if LaTeX is not installed.

## 2. Directory layout

The `tictactoe` package has no dependencies. Do not add Manim to the root `pyproject.toml`. Make a separate project in `video/`.

```
video/
  pyproject.toml            separate uv project: manim, manim-voiceover
  common/
    __init__.py
    style.py                colors and sizes from blog/videos/README.md
    board.py                make_board(), make_x(), make_o(), draw_mark(), heat_map()
    cards.py                make_command_card(), make_event_card()
    code_panel.py           make_code_panel(code_string)
    voice.py                set_voice(scene): selects the speech service
  episodes/
    e1/
      e1s1_series_intro.py  one scene class in each file
      ...
    e2/ ... e6/
  media/                    Manim output (do not commit)
  final/                    joined episode MP4 files (do not commit)
```

## 3. One-time setup

Do these steps one time, before episode 1.

### 3.1 Install system packages

Install `ffmpeg`, `cairo`, and `pango`. On Debian or Ubuntu:

```sh
sudo apt install ffmpeg libcairo2-dev libpango1.0-dev
```

LaTeX is optional (see section 1).

### 3.2 Make the video project

```sh
mkdir -p video && cd video
uv init --no-package --name tictactoe-videos
uv add "manim>=0.19,<0.20" "manim-voiceover[gtts,transcribe]"
uv run manim checkhealth
```

Add `video/media/` and `video/final/` to `.gitignore`.

Make sure that the installed extras are correct. Read the manim-voiceover installation page. Extras names can change between releases.

### 3.3 Write the `common` package

Write the files in `video/common/` from the rules in `blog/videos/README.md`, section "Shared visual language".

- Put each hex color in `style.py` as a named constant (`X_COLOR`, `O_COLOR`, `RULE_COLOR`, `COMMAND_COLOR`, `EVENT_COLOR`, `ERROR_COLOR`, `POSITIVE_COLOR`, `NEGATIVE_COLOR`, `NEUTRAL_COLOR`, `BG_COLOR`, `TEXT_COLOR`, `MUTED_COLOR`).
- Set the background in each scene: `self.camera.background_color = BG_COLOR`.
- `make_board()` returns a `VGroup` of 9 squares. Keep the squares in index order 0 to 8, so that `board[i]` is cell `i`.
- `make_code_panel(code_string)` returns `Code(code_string=code_string, language="python", background="window", add_line_numbers=False)`, scaled to fit the right half of the screen.
- `set_voice(scene)` uses `GTTSService(transcription_model="base")` for drafts. Section 6 tells how to change the voice for the final render.

### 3.4 Test the common package

Write `video/episodes/e00_style_test.py`. The scene shows a board, an X, an O, a code panel, one command card, one event card, and a heat map. Render it:

```sh
uv run manim -ql -s episodes/e00_style_test.py StyleTest
```

Open the PNG in `media/images/`. Compare it with the README rules. Correct `common/` until the PNG is correct. All episodes use this package, so an error here goes into every video.

If a Manim class does not accept a parameter, read the signature in the installed version:

```sh
uv run python -c "import inspect, manim; print(inspect.signature(manim.Code.__init__))"
```

## 4. Procedure for one episode

Do one episode at a time, in number order. Do one scene at a time.

### 4.1 Read

1. Read `blog/videos/README.md`.
2. Read the episode file, for example `blog/videos/03-the-naive-opponent.md`.
3. Do not read the blog articles or the source code. The episode file contains all the facts. If a fact is missing, stop and record a question (step 4.6).

### 4.2 Write the scene file

Use this prompt for each scene. Replace the parts in angle brackets.

```text
You write one Manim Community Edition scene.

Rules:
- Use `from manim import *` and `from manim_voiceover import VoiceoverScene`.
- Import colors and builders from `common`. Do not write hex colors in the scene.
- Make one class, <ClassName>, a subclass of VoiceoverScene.
- Call `set_voice(self)` first.
- Put each narration block in `with self.voiceover(text="...") as tracker:`.
- Copy the narration text exactly, including the bookmark tags.
- Start each animation step after `self.wait_until_bookmark("<name>")`.
- Copy code snippets exactly from the episode file. Do not change the code.
- Keep all objects inside the frame. Do not let objects overlap unless the scene says so.
- Remove objects that the next step does not use (FadeOut).

Scene specification:
<paste the full scene section from the episode file>
```

Save the file as `video/episodes/e<N>/e<N>s<M>_<short_name>.py`.

### 4.3 Render a draft and check the layout

1. Render the last frame at low quality:

   ```sh
   uv run manim -ql -s episodes/e3/e3s2_strategy_seam.py E3S2StrategySeam
   ```

2. Render the full scene at low quality:

   ```sh
   uv run manim -ql episodes/e3/e3s2_strategy_seam.py E3S2StrategySeam
   ```

3. Extract one frame each 3 seconds:

   ```sh
   mkdir -p /tmp/frames && ffmpeg -loglevel error -i media/videos/e3s2_strategy_seam/480p15/E3S2StrategySeam.mp4 -vf fps=1/3 /tmp/frames/f_%03d.png
   ```

4. Look at each frame. Answer these questions:
   - Is all text inside the frame?
   - Is all text readable (no overlap)?
   - Do the colors agree with the README table?
   - Does the frame agree with the "Visuals" list of the scene?

5. If an answer is "no", correct the scene file and go to step 1.

### 4.4 Correct render errors

If the render fails:

1. Read the last 30 lines of the error output.
2. Find the one line in the scene file that caused the error.
3. Change only that line or its block.
4. Render again.

If the render fails three times for the same scene, stop. Record the error in `video/episodes/e<N>/QUESTIONS.md` and go to the next scene.

### 4.5 Check the facts

Compare the rendered scene with the "Accuracy notes" and "Checks" of the episode file. Make sure that:

- The code on screen is the same as the code in the episode file.
- Numbers (weights, probabilities, win counts, sizes) are the same as the episode file.
- The narration uses the correct names from the README section "Correct names for the learners".

### 4.6 Record questions

If the episode file is not clear, do not guess a technical fact. Write the question in `video/episodes/e<N>/QUESTIONS.md`. A person or a more capable LLM answers the questions. Continue with the parts that are clear.

### 4.7 Render the final scenes

When all scenes of the episode pass steps 4.3 and 4.5, render at full quality:

```sh
uv run manim -qh --fps 30 episodes/e3/e3s2_strategy_seam.py E3S2StrategySeam
```

### 4.8 Join the scenes

Write a list of the scene files in order:

```sh
cd video
: > /tmp/e3_list.txt
for f in media/videos/e3s*/1080p30/*.mp4; do echo "file '$PWD/$f'" >> /tmp/e3_list.txt; done
sort -o /tmp/e3_list.txt /tmp/e3_list.txt
cat /tmp/e3_list.txt
```

Make sure that the order in the list is the scene order. Then join the files:

```sh
mkdir -p final && ffmpeg -f concat -safe 0 -i /tmp/e3_list.txt -c copy final/e3.mp4
```

manim-voiceover writes an `.srt` subtitle file next to each scene video. Join the subtitle files with a subtitle tool, or burn in subtitles at a later step.

## 5. Review

A person or a more capable LLM watches each final episode. The reviewer uses the "Checks" section of the episode file. The reviewer records problems in `QUESTIONS.md`. The production LLM corrects only the scenes with problems, then does steps 4.7 and 4.8 again.

## 6. Voice

- **Drafts.** Use `GTTSService`. It is free and it needs an internet connection.
- **Final.** Use one of these:
  - A human voice with `RecorderService`. manim-voiceover shows each narration block and records it from the microphone.
  - A good text-to-speech service (for example `OpenAIService`, `ElevenLabsService`, or `AzureService`).
- Change only `common/voice.py` to change the voice. The scene files do not change.
- Bookmarks need word timing. Keep `transcription_model="base"` for all services.

## 7. Rules summary

1. Do one scene at a time.
2. Copy narration and code exactly from the episode file.
3. Use the `common` package for all colors and fixed objects.
4. Render at low quality and look at frames before you continue.
5. Do not guess a technical fact. Record a question.
6. Do not add Manim to the root project.
