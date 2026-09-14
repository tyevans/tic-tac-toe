from manim import *
from manim_voiceover import VoiceoverScene

from common import BG_COLOR, MUTED_COLOR, RULE_COLOR, TEXT_COLOR, make_board, set_voice

TITLES = [
    "The Parts of the Game",
    "How a Move Happens",
    "The Naive Opponent",
    "The Perfect Player",
    "Learning from Rewards",
    "A Neural Network Policy",
]


class E1S1SeriesIntro(VoiceoverScene):
    def setup(self) -> None:
        set_voice(self)

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR
        question = Text("Who decides the next move?", font_size=56, color=TEXT_COLOR)
        question_top = Text("Who decides the next move?", font_size=40, color=TEXT_COLOR).to_edge(UP, buff=0.4)
        board = make_board().scale(0.6).move_to([-4.2, -0.3, 0])
        rows = VGroup(
            *[Text(f"{n}  {title}", font_size=26, color=MUTED_COLOR) for n, title in enumerate(TITLES, start=1)]
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.6).move_to([2.4, -0.3, 0])
        rows.shift(RIGHT * (rows.width / 2))
        highlight = SurroundingRectangle(rows[0], buff=0.1, corner_radius=0.08, stroke_color=RULE_COLOR, stroke_width=3)

        with self.voiceover(
            "This series asks one question. <bookmark mark='question'/>Who decides the next move? Each video gives a different answer."
        ) as tracker:
            self.wait_until_bookmark("question")
            self.play(Write(question))

        with self.voiceover(
            "<bookmark mark='roadmap'/>Video one shows the parts of the game. Video two shows how a move happens. "
            "<bookmark mark='players'/>Videos three and four show a naive opponent and a perfect player. "
            "<bookmark mark='learners'/>Videos five and six show two players that learn. One learns from rewards. One uses a neural network."
        ) as tracker:
            self.wait_until_bookmark("roadmap")
            self.play(Transform(question, question_top))
            self.play(FadeIn(board))
            self.play(FadeIn(rows[0]))
            self.play(FadeIn(rows[1]))
            self.wait_until_bookmark("players")
            self.play(FadeIn(rows[2]))
            self.play(FadeIn(rows[3]))
            self.wait_until_bookmark("learners")
            self.play(FadeIn(rows[4]))
            self.play(FadeIn(rows[5]))

        with self.voiceover(
            "<bookmark mark='today'/>In this video, the answer is: nobody. We build only the game, and we make sure that its rules are always correct."
        ) as tracker:
            self.wait_until_bookmark("today")
            self.play(rows[0].animate.set_color(TEXT_COLOR))
            self.play(Create(highlight))
            self.play(rows[1:].animate.set_opacity(0.4))
            self.play(Indicate(board))
            self.wait(1)
