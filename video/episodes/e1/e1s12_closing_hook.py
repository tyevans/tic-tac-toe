from manim import *
from manim_voiceover import VoiceoverScene

from common import (
    BG_COLOR,
    MUTED_COLOR,
    RULE_COLOR,
    TEXT_COLOR,
    make_command_card,
    set_voice,
)


def make_row(icon_color: str, label: str) -> VGroup:
    icon = Square(
        side_length=0.28,
        fill_color=icon_color,
        fill_opacity=1,
        stroke_color=icon_color,
        stroke_width=2,
    )
    text = Text(label, font_size=30, color=TEXT_COLOR)
    return VGroup(icon, text).arrange(RIGHT, buff=0.25)


class E1S12ClosingHook(VoiceoverScene):
    def setup(self) -> None:
        set_voice(self)

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR
        title = Text("Summary", font_size=40, color=TEXT_COLOR).to_edge(UP, buff=0.4)

        rows = VGroup(
            make_row(RULE_COLOR, "Value objects check invariants"),
            make_row(TEXT_COLOR, "Game keeps the rules → Transition"),
            make_row(MUTED_COLOR, "A move makes a new version"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.8)
        rows.shift(np.array([-6.0 + rows.width / 2, 0.6, 0.0]))

        card = make_command_card("PlaceMark", ["position: ?"])
        arrow = Arrow(ORIGIN, RIGHT * 0.9, buff=0, stroke_color=MUTED_COLOR, stroke_width=4)
        question = Text("?", font_size=60, color=MUTED_COLOR)
        hook_group = VGroup(card, arrow, question).arrange(RIGHT, buff=0.45).move_to([4.0, -0.2, 0.0])

        hook_text = Text(
            "How does a move request travel through the system?",
            font_size=34,
            color=TEXT_COLOR,
        ).move_to([0, -2.4, 0.0])

        next_title = Text(
            "Next: How a Move Happens",
            font_size=30,
            color=MUTED_COLOR,
        ).to_edge(DOWN, buff=0.4)

        with self.voiceover(
            "Let us review. <bookmark mark='values'/>Value objects check their own invariants. "
            "Player, Position, and Board raise a Domain Error for a bad value. "
            "<bookmark mark='game'/>The Game aggregate keeps the rules of play. "
            "Each move gives a Transition. "
            "<bookmark mark='immutable'/>Nothing changes in place. Each move makes a new version."
        ) as tracker:
            self.play(Write(title))
            self.wait_until_bookmark("values")
            self.play(FadeIn(rows[0]))
            self.wait_until_bookmark("game")
            self.play(FadeIn(rows[1]))
            self.wait_until_bookmark("immutable")
            self.play(FadeIn(rows[2]))

        with self.voiceover(
            "<bookmark mark='hook'/>Now we can hold a game. But how does a move request travel "
            "through the system? Video two shows how a move happens."
        ) as tracker:
            self.wait_until_bookmark("hook")
            self.play(
                *[r.animate.set_opacity(0.4) for r in rows],
                FadeIn(card),
                FadeIn(arrow),
                FadeIn(question),
                run_time=0.9,
            )
            self.play(Write(hook_text), run_time=1.4)
            self.play(FadeIn(next_title), run_time=0.8)
            self.wait(1.5)
