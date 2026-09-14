from manim import *
from manim_voiceover import VoiceoverScene

from common import (
    BG_COLOR,
    ERROR_COLOR,
    MUTED_COLOR,
    TEXT_COLOR,
    code_highlight,
    make_code_panel,
    set_voice,
)

ERRORS_CODE = '''class DomainError(Exception):
    pass


class InvalidPlayerError(DomainError):
    def __init__(self, symbol: str) -> None:
        super().__init__(f"invalid player symbol {symbol!r}")


class InvalidBoardError(DomainError):
    def __init__(self) -> None:
        super().__init__("a board must have exactly 9 cells")'''

LEFT_NAMES = ["InvalidPlayerError", "InvalidPositionError", "InvalidBoardError", "PositionOccupiedError"]
RIGHT_NAMES = ["GameAlreadyOverError", "GameNotFoundError", "GameAlreadyExistsError"]


def error_box(name: str, font_size: int, stroke_color: str):
    label = Text(name, font_size=font_size, color=TEXT_COLOR)
    box = RoundedRectangle(
        width=label.width + 0.35,
        height=label.height + 0.26,
        corner_radius=0.08,
        stroke_color=stroke_color,
        stroke_width=2.5,
    )
    return box, label


class E1S8ErrorFamily(VoiceoverScene):
    def setup(self) -> None:
        set_voice(self)

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR
        title = Text("One base class: DomainError", font_size=40, color=TEXT_COLOR).to_edge(UP, buff=0.4)
        panel = make_code_panel(ERRORS_CODE, max_width=5.6, max_height=6.2).move_to([3.8, -0.3, 0.0])
        root_box, root_label = error_box("DomainError", 26, ERROR_COLOR)
        root_box.move_to([-3.6, 2.2, 0.0])
        root_label.move_to([-3.6, 2.2, 0.0])
        left_items = VGroup()
        left_lines = VGroup()
        for name, y in zip(LEFT_NAMES, [1.0, 0.25, -0.5, -1.25]):
            box, label = error_box(name, 20, ERROR_COLOR)
            box.move_to([-5.2, y, 0.0])
            label.move_to([-5.2, y, 0.0])
            left_items.add(VGroup(box, label))
            left_lines.add(Line(root_box.get_bottom(), box.get_top(), stroke_color=MUTED_COLOR, stroke_width=1.5))
        right_items = VGroup()
        right_lines = VGroup()
        for name, y, stroke in zip(RIGHT_NAMES, [1.0, 0.25, -0.5], [ERROR_COLOR, MUTED_COLOR, MUTED_COLOR]):
            box, label = error_box(name, 20, stroke)
            box.move_to([-2.0, y, 0.0])
            label.move_to([-2.0, y, 0.0])
            right_items.add(VGroup(box, label))
            right_lines.add(Line(root_box.get_bottom(), box.get_top(), stroke_color=MUTED_COLOR, stroke_width=1.5))
        tag_game = Text("Game", font_size=18, color=MUTED_COLOR).next_to(right_items[0], RIGHT, buff=0.15)
        tag_video2_a = Text("video 2", font_size=18, color=MUTED_COLOR).next_to(right_items[1], RIGHT, buff=0.15)
        tag_video2_b = Text("video 2", font_size=18, color=MUTED_COLOR).next_to(right_items[2], RIGHT, buff=0.15)
        highlight = code_highlight(panel, 0, color=TEXT_COLOR)
        full_frame = RoundedRectangle(
            width=panel.get_right()[0] - panel.get_left()[0] + 0.1,
            height=panel.get_top()[1] - panel.get_bottom()[1] + 0.1,
            corner_radius=0.05,
            stroke_color=MUTED_COLOR,
            stroke_width=3,
        ).move_to(panel.get_center())
        import_text = Text("import", font_size=28, color=TEXT_COLOR).move_to([3.4, -3.2, 0.0])
        import_cross = Cross(import_text, stroke_color=ERROR_COLOR, stroke_width=5)
        with self.voiceover(
            "Each broken rule has its own error class. "
            "<bookmark mark='base'/>All of them come from one base class, Domain Error."
        ) as tracker:
            self.play(Write(title))
            self.play(FadeIn(panel))
            self.wait_until_bookmark("base")
            self.play(Create(root_box), Write(root_label), Create(highlight))
        with self.voiceover(
            "<bookmark mark='seen'/>We saw four of them: Invalid Player Error, Invalid Position Error, Invalid Board Error, and Position Occupied Error. "
            "<bookmark mark='game_over'/>Game uses a fifth, Game Already Over Error. "
            "<bookmark mark='engine'/>Video two uses the last two."
        ) as tracker:
            self.wait_until_bookmark("seen")
            for item, line in zip(left_items, left_lines):
                self.play(FadeIn(line), FadeIn(item), run_time=0.9)
            self.wait_until_bookmark("game_over")
            self.play(FadeIn(right_lines[0]), FadeIn(right_items[0]), FadeIn(tag_game), run_time=1.0)
            self.wait_until_bookmark("engine")
            self.play(
                FadeIn(right_lines[1]),
                FadeIn(right_items[1]),
                FadeIn(right_lines[2]),
                FadeIn(right_items[2]),
                FadeIn(tag_video2_a),
                FadeIn(tag_video2_b),
                run_time=1.2,
            )
        with self.voiceover(
            "<bookmark mark='no_imports'/>The file errors dot py imports nothing from the other domain files. "
            "Each error takes only simple values, like text and numbers."
        ) as tracker:
            self.wait_until_bookmark("no_imports")
            self.play(Transform(highlight, full_frame), run_time=1.0)
            self.play(FadeIn(import_text), Create(import_cross), run_time=0.8)
            self.wait(1.0)
