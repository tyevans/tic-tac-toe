from manim import *
from manim_voiceover import VoiceoverScene

from common import (
    BG_COLOR,
    ERROR_COLOR,
    TEXT_COLOR,
    cell_indices,
    code_highlight,
    make_board,
    make_code_panel,
    reject,
    set_voice,
)


class _VoiceoverRef(VoiceoverScene):
    def setup(self) -> None:
        set_voice(self)

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR

        title = Text("Voiceover reference", font_size=40, color=TEXT_COLOR)
        title.to_edge(UP, buff=0.4)

        board = make_board().move_to([-3.6, -0.3, 0])
        indices = cell_indices(board)

        panel = make_code_panel(
            "def check(board):\n    if board.full():\n        return 'draw'\n    return 'open'"
        ).move_to([3.4, -0.3, 0])
        highlight = code_highlight(panel, 1)

        token = Text("bad move", font_size=28, color=TEXT_COLOR).move_to([-3.6, -2.9, 0])
        err = Text("Rule rejected", font_size=22, color=ERROR_COLOR).move_to([-3.6, -3.5, 0])

        with self.voiceover(
            "Here is the game board. <bookmark mark='cells'/>It shows the nine cells, numbered from zero to eight."
        ) as tracker:
            self.play(Write(title), run_time=1.5)
            self.wait_until_bookmark("cells")
            self.play(FadeIn(board, lag_ratio=0.05), FadeIn(indices, lag_ratio=0.1), run_time=2.0)

        with self.voiceover(
            "The code that draws the board lives in the panel on the right."
        ) as tracker:
            self.play(FadeIn(panel), run_time=2.0)

        with self.voiceover(
            "One line is highlighted, so you can see which line the rule checks."
        ) as tracker:
            self.play(FadeIn(highlight), run_time=1.5)

        with self.voiceover(
            "Now we try a bad move, and the rule rejects it."
        ) as tracker:
            self.play(FadeIn(token), run_time=1.0)
            reject(self, token, err)
