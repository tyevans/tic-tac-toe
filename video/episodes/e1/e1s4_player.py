from manim import *
from manim_voiceover import VoiceoverScene

from common import (
    BG_COLOR,
    ERROR_COLOR,
    O_COLOR,
    RULE_COLOR,
    TEXT_COLOR,
    X_COLOR,
    code_highlight,
    make_code_panel,
    make_o,
    make_x,
    reject,
    set_voice,
)

PLAYER_SNIPPET = '''@dataclass(frozen=True, slots=True)
class Player:
    symbol: str

    def __post_init__(self) -> None:
        if self.symbol not in ("X", "O"):
            raise InvalidPlayerError(self.symbol)

    @property
    def opponent(self) -> "Player":
        return Player("O" if self.symbol == "X" else "X")


X = Player("X")
O = Player("O")'''


class E1S4Player(VoiceoverScene):
    def setup(self) -> None:
        set_voice(self)

    def _make_token(self, text: str, color: str) -> VGroup:
        label = Text(text, font_size=24, color=color)
        box = RoundedRectangle(
            corner_radius=0.1,
            width=label.width + 0.4,
            height=label.height + 0.25,
            stroke_color=color,
            stroke_width=3,
            fill_opacity=0,
        )
        label.move_to(box)
        return VGroup(box, label)

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR
        title = Text("The Player value object", font_size=40, color=TEXT_COLOR).to_edge(UP, buff=0.4)
        panel = make_code_panel(PLAYER_SNIPPET).move_to([3.4, -0.3, 0.0])
        rule_box = RoundedRectangle(
            corner_radius=0.12,
            width=3.6,
            height=1.2,
            stroke_color=RULE_COLOR,
            stroke_width=3,
            fill_opacity=0,
        ).move_to([-3.6, 1.2, 0.0])
        rule_text = Text('symbol in ("X", "O")', font_size=24, color=RULE_COLOR).move_to(rule_box)
        rule_panel = VGroup(rule_box, rule_text)
        token_q = self._make_token('Player("Q")', TEXT_COLOR).move_to([-3.6, 2.9, 0.0])
        token_x = self._make_token('Player("X")', X_COLOR).move_to([-3.6, 2.9, 0.0])
        token_o = self._make_token('Player("O")', O_COLOR).move_to([-3.6, 2.9, 0.0])
        error_label = Text("InvalidPlayerError: invalid player symbol 'Q'", font_size=24, color=ERROR_COLOR).move_to(
            [-3.6, 0.0, 0.0]
        )
        x_mark = make_x(scale=0.7).move_to([-4.6, -1.2, 0.0])
        o_mark = make_o(scale=0.7).move_to([-2.6, -1.2, 0.0])
        rect_symbol = code_highlight(panel, 2, color=TEXT_COLOR)
        rect_frozen = code_highlight(panel, 0, color=TEXT_COLOR)
        rect_postinit = code_highlight(panel, 4, 5, 6, color=RULE_COLOR)
        rect_error = code_highlight(panel, 6, color=ERROR_COLOR)
        rect_consts = code_highlight(panel, 13, 14, color=TEXT_COLOR)
        rect_opp = code_highlight(panel, 8, 9, 10, color=TEXT_COLOR)
        arrow = CurvedArrow(
            [-4.15, -1.2, 0.0],
            [-3.05, -1.2, 0.0],
            angle=-TAU / 4,
            stroke_color=TEXT_COLOR,
            stroke_width=4,
        )
        opp_label = Text("opponent", font_size=22, color=TEXT_COLOR).move_to([-3.6, -0.75, 0.0])
        with self.voiceover(
            "Our first value object is Player. <bookmark mark='code'/>"
            "Player has one field: symbol. Player is a frozen dataclass. "
            "Frozen means that its fields cannot change."
        ) as tracker:
            self.play(Write(title))
            self.wait_until_bookmark("code")
            self.play(FadeIn(panel))
            self.play(Create(rect_symbol))
            self.play(Create(rect_frozen))
        with self.voiceover(
            "<bookmark mark='post_init'/>Python runs the method post init immediately after it sets the fields. "
            "Here, post init checks the invariant: the symbol must be X or O."
        ) as tracker:
            self.wait_until_bookmark("post_init")
            self.play(FadeOut(rect_symbol), FadeOut(rect_frozen), Create(rect_postinit))
            self.play(FadeIn(rule_panel, shift=RIGHT * 0.3))
        with self.voiceover(
            "<bookmark mark='bad'/>Now we try to make a Player with the symbol Q. "
            "<bookmark mark='reject'/>The check fails. Python raises Invalid Player Error, and no Player object exists."
        ) as tracker:
            self.wait_until_bookmark("bad")
            self.play(FadeIn(token_q))
            self.play(token_q.animate.move_to(rule_box.get_top() + UP * 0.32), run_time=0.8)
            self.wait_until_bookmark("reject")
            reject(self, token_q, error_label)
            self.play(Create(rect_error))
            self.remove(token_q)
        with self.voiceover(
            "<bookmark mark='constants'/>Only two players are possible, so the module makes two constants, X and O. "
            "<bookmark mark='opponent'/>The opponent property gives the other player. The opponent of X is O."
        ) as tracker:
            self.wait_until_bookmark("constants")
            self.play(FadeOut(error_label), FadeOut(rect_error))
            self.remove(error_label)
            self.play(Create(rect_consts))
            self.play(FadeIn(token_x))
            self.play(token_x.animate.move_to(x_mark.get_center()), run_time=1.0)
            self.play(FadeOut(token_x), FadeIn(x_mark), run_time=0.4)
            self.remove(token_x)
            self.play(FadeIn(token_o))
            self.play(token_o.animate.move_to(o_mark.get_center()), run_time=1.0)
            self.play(FadeOut(token_o), FadeIn(o_mark), run_time=0.4)
            self.remove(token_o)
            self.wait_until_bookmark("opponent")
            self.play(Transform(rect_consts, rect_opp))
            self.play(Create(arrow), FadeIn(opp_label))
        self.wait(1)
