from manim import *
from manim_voiceover import VoiceoverScene

from common import (
    BG_COLOR,
    EVENT_COLOR,
    NEUTRAL_COLOR,
    O_COLOR,
    RULE_COLOR,
    TEXT_COLOR,
    X_COLOR,
    code_highlight,
    make_code_panel,
    make_event_card,
    make_game_card,
    set_voice,
)

FIELDS_CODE = '''@dataclass(frozen=True, slots=True)
class Game:
    id: str
    board: Board
    current_player: Player
    status: GameStatus'''

STATUS_CODE = '''class GameStatus(Enum):
    IN_PROGRESS = "in_progress"
    X_WON = "x_won"
    O_WON = "o_won"
    DRAW = "draw"'''

START_CODE = '''    @classmethod
    def start(cls, game_id: str) -> "Transition":
        game = cls(
            id=game_id,
            board=Board.empty(),
            current_player=X,
            status=GameStatus.IN_PROGRESS,
        )
        return Transition(game, (GameStarted(game_id),))'''

TRANSITION_CODE = '''@dataclass(frozen=True, slots=True)
class Transition:
    game: Game
    events: tuple[DomainEvent, ...]'''

PANEL_POS = [3.4, -0.3, 0.0]


def status_chip(name: str, color: str) -> VGroup:
    label = Text(name, font_size=20, color=color)
    box = RoundedRectangle(
        width=label.width + 0.3,
        height=label.height + 0.24,
        corner_radius=0.08,
        stroke_color=color,
        stroke_width=2.5,
    )
    return VGroup(box, label)


class E1S9GameAggregate(VoiceoverScene):
    def setup(self) -> None:
        set_voice(self)

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR
        title = Text("Game: the aggregate", font_size=40, color=TEXT_COLOR).to_edge(UP, buff=0.4)
        panel = make_code_panel(FIELDS_CODE, max_width=6.2, max_height=6.2).move_to(PANEL_POS)
        card = make_game_card("g1").move_to([-3.6, 0.3, 0.0])
        chips = VGroup(
            *[
                status_chip(name, color)
                for name, color in [
                    ("IN_PROGRESS", TEXT_COLOR),
                    ("X_WON", X_COLOR),
                    ("O_WON", O_COLOR),
                    ("DRAW", NEUTRAL_COLOR),
                ]
            ]
        ).arrange(RIGHT, buff=0.25).move_to([-3.6, -2.4, 0.0])
        rule_rect = SurroundingRectangle(
            card[0],
            buff=0.15,
            stroke_color=RULE_COLOR,
            stroke_width=3,
            corner_radius=0.12,
        )
        rule_label = Text("rules of play", font_size=24, color=RULE_COLOR).next_to(card[0], UP, buff=0.28)
        trans_box = DashedVMobject(
            RoundedRectangle(width=6.4, height=5.6, corner_radius=0.12, stroke_color=TEXT_COLOR, stroke_width=3),
            num_dashes=36,
            dashed_ratio=0.55,
        ).move_to([-3.6, -0.3, 0.0])
        trans_label = Text("Transition", font_size=28, color=TEXT_COLOR).next_to(trans_box, UP, buff=0.1)
        card_moved = card.copy().scale(0.8).move_to([-3.6, 0.9, 0.0])
        event_card = make_event_card("GameStarted", ["game_id: g1"]).move_to([-3.6, -1.1, 0.0])
        with self.voiceover(
            "Now the data is safe. Next, we need the rules that change it. "
            "<bookmark mark='fields'/>The Game aggregate has four fields: an id, a board, the current player, and a status."
        ) as tracker:
            self.play(Write(title), run_time=1.6)
            self.wait_until_bookmark("fields")
            self.play(FadeIn(panel), Create(card[0]), Write(card[1]), run_time=1.2)
            hl = code_highlight(panel, 2, color=TEXT_COLOR)
            self.play(FadeIn(hl), FadeIn(card[2]), run_time=0.7)
            for num, row in zip([3, 4, 5], card[3:6]):
                self.play(
                    Transform(hl, code_highlight(panel, num, color=TEXT_COLOR)),
                    FadeIn(row),
                    run_time=0.7,
                )
        with self.voiceover(
            "<bookmark mark='status'/>Game Status is an enum with four values: in progress, X won, O won, and draw. "
            "<bookmark mark='one_place'/>Game is the one place where the rules of play live. Only the methods of Game make a new Game."
        ) as tracker:
            self.wait_until_bookmark("status")
            self.play(
                Transform(panel, make_code_panel(STATUS_CODE, max_width=6.2, max_height=6.2).move_to(PANEL_POS)),
                FadeIn(chips),
                run_time=1.4,
            )
            self.wait_until_bookmark("one_place")
            self.play(FadeOut(chips), Create(rule_rect), Write(rule_label), run_time=1.2)
        with self.voiceover(
            "<bookmark mark='start_code'/>The method start makes a new game. "
            "<bookmark mark='start_values'/>It uses an empty board. It sets the current player to X. It sets the status to in progress."
        ) as tracker:
            self.wait_until_bookmark("start_code")
            self.play(
                FadeOut(rule_rect),
                FadeOut(rule_label),
                Transform(panel, make_code_panel(START_CODE, max_width=6.2, max_height=6.2).move_to(PANEL_POS)),
                run_time=1.2,
            )
            self.wait_until_bookmark("start_values")
            hl_s = code_highlight(panel, 4, color=TEXT_COLOR)
            self.play(FadeIn(hl_s), Indicate(card[3], scale_factor=1.08, run_time=0.8), run_time=0.8)
            for num, row in [(5, card[4]), (6, card[5])]:
                self.play(
                    Transform(hl_s, code_highlight(panel, num, color=TEXT_COLOR)),
                    Indicate(row, scale_factor=1.08, run_time=0.8),
                    run_time=0.8,
                )
        with self.voiceover(
            "<bookmark mark='transition'/>But start does not give back a Game. It gives back a Transition. "
            "<bookmark mark='transition_fields'/>A Transition holds two things: the next Game, and a list of what happened. "
            "Here, the list has one item: Game Started. Video two tells more about these items."
        ) as tracker:
            self.wait_until_bookmark("transition")
            self.play(
                Create(trans_box),
                Write(trans_label),
                Transform(hl_s, code_highlight(panel, 8, color=TEXT_COLOR)),
                Transform(card, card_moved),
                run_time=1.4,
            )
            self.wait_until_bookmark("transition_fields")
            self.play(
                Transform(panel, make_code_panel(TRANSITION_CODE, max_width=6.2, max_height=6.2).move_to(PANEL_POS)),
                FadeIn(event_card),
                run_time=1.4,
            )
            self.play(Create(code_highlight(panel, 3, color=EVENT_COLOR)), run_time=0.8)
            self.wait(1.0)
