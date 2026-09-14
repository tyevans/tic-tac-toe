from manim import *
from manim_voiceover import VoiceoverScene

from common import (
    BG_COLOR,
    ERROR_COLOR,
    MUTED_COLOR,
    NEUTRAL_COLOR,
    TEXT_COLOR,
    code_highlight,
    draw_mark,
    make_board,
    make_code_panel,
    make_game_card,
    make_o,
    make_x,
    reject,
    set_voice,
)

WITH_MARK_CODE = '''    def with_mark(self, position: Position, player: Player) -> "Board":
        if self.is_occupied(position):
            raise PositionOccupiedError(position.row, position.column)
        cells = list(self.cells)
        cells[position.index] = Cell(player)
        return Board(tuple(cells))'''

PANEL_POS = [3.4, -0.3, 0.0]
OLD_POS = [-4.8, 0.6, 0.0]
NEW_POS = [-1.6, 0.6, 0.0]
BOARD_SCALE = 0.7


def strip_board(x: float, marks: list[tuple[int, str]]) -> VGroup:
    board = make_board().scale(0.35).move_to([x, 0.5, 0.0])
    marks_grp = VGroup(
        *[
            (make_x(scale=0.35) if player == "X" else make_o(scale=0.35)).move_to(
                board[i].get_center()
            )
            for i, player in marks
        ]
    )
    return VGroup(board, marks_grp)


class E1S11Immutability(VoiceoverScene):
    def setup(self) -> None:
        set_voice(self)

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR
        title = Text("Nothing changes in place", font_size=40, color=TEXT_COLOR).to_edge(UP, buff=0.4)
        panel = make_code_panel(WITH_MARK_CODE, max_width=6.2, max_height=6.2).move_to(PANEL_POS)

        old_board = make_board().scale(BOARD_SCALE).move_to(OLD_POS)
        x_mark = draw_mark(old_board, 0, "X")
        old_group = VGroup(old_board, x_mark)
        old_label = Text("old board", font_size=24, color=MUTED_COLOR).next_to(old_board, DOWN, buff=0.18)

        new_group = old_group.copy()
        new_board = new_group[0]
        new_label = Text("new board", font_size=24, color=TEXT_COLOR).next_to(
            old_board.copy().move_to(NEW_POS), DOWN, buff=0.18
        )

        arrow = Arrow(
            old_board.get_corner(UR),
            np.array([NEW_POS[0] - 1.8 * BOARD_SCALE, NEW_POS[1] + 1.8 * BOARD_SCALE, 0.0]),
            buff=0.05,
            stroke_color=TEXT_COLOR,
            stroke_width=4,
        )
        arrow_label = Text(
            "with_mark(Position(1, 1), O)", font_size=20, color=TEXT_COLOR
        ).next_to(arrow, UP, buff=0.12)

        assign_text = Text("old.cells = ()", font_size=26, color=TEXT_COLOR).move_to([-3.2, -2.0, 0.0])
        error_label = Text(
            "FrozenInstanceError: cannot assign to field 'cells'",
            font_size=22,
            color=ERROR_COLOR,
        ).next_to(assign_text, DOWN, buff=0.2)

        old_card = make_game_card("g1").scale(0.6).move_to([-5.0, 0.6, 0.0])
        new_card = make_game_card("g1").scale(0.6).move_to([-1.45, 0.6, 0.0])
        card_arrow = Arrow(
            old_card.get_corner(UR),
            new_card.get_corner(UL),
            buff=0.04,
            stroke_color=TEXT_COLOR,
            stroke_width=4,
        )
        card_arrow_label = Text("place_mark(...)", font_size=20, color=TEXT_COLOR).next_to(
            card_arrow, UP, buff=0.12
        )
        card_labels = VGroup(
            Text("old Game", font_size=24, color=MUTED_COLOR).next_to(old_card, DOWN, buff=0.18),
            Text("new Game", font_size=24, color=TEXT_COLOR).next_to(new_card, DOWN, buff=0.18),
        )

        strip = VGroup(
            strip_board(-5.2, [(0, "X")]),
            strip_board(-2.6, [(0, "X"), (4, "O")]),
            strip_board(0.0, [(0, "X"), (4, "O"), (1, "X")]),
            strip_board(2.6, [(0, "X"), (4, "O"), (1, "X"), (2, "O")]),
            strip_board(5.2, [(0, "X"), (4, "O"), (1, "X"), (2, "O"), (3, "X")]),
        )
        read_text = Text("read at any time", font_size=24, color=TEXT_COLOR).next_to(
            strip[0][0], DOWN, buff=0.15
        )

        mini_board = make_board().scale(0.3)
        mini_marks = VGroup(
            make_x(scale=0.3).move_to(mini_board[0].get_center()),
            make_o(scale=0.3).move_to(mini_board[4].get_center()),
        )
        dict_mob = VGroup(
            Text("{", font_size=32, color=TEXT_COLOR),
            VGroup(mini_board, mini_marks),
            Text(":", font_size=32, color=TEXT_COLOR),
            Text("0.5", font_size=32, color=NEUTRAL_COLOR),
            Text("}", font_size=32, color=TEXT_COLOR),
        ).arrange(RIGHT, buff=0.18).move_to([0.0, -2.4, 0.0])

        with self.voiceover(
            "Look again at the method with mark. It does not change the board. "
            "<bookmark mark='old'/>Here is a board with an X in cell 0. "
            "<bookmark mark='call'/>We call with mark for cell 4 and player O."
        ) as tracker:
            self.play(Write(title), run_time=1.6)
            self.play(FadeIn(panel), run_time=1.2)
            self.wait_until_bookmark("old")
            self.play(Create(old_board), run_time=1.0)
            self.play(GrowFromCenter(x_mark), Write(old_label), run_time=0.8)
            self.wait_until_bookmark("call")
            self.play(GrowArrow(arrow), run_time=0.8)
            self.play(Write(arrow_label), run_time=0.9)

        with self.voiceover(
            "<bookmark mark='copy'/>The method copies the cells, puts an O in cell 4, and makes a new Board. "
            "<bookmark mark='compare'/>The old board still has only one mark. The new board has two marks."
        ) as tracker:
            self.wait_until_bookmark("copy")
            hl = code_highlight(panel, 3, color=TEXT_COLOR)
            self.play(FadeIn(hl), run_time=0.6)
            self.play(new_group.animate.move_to(NEW_POS), run_time=1.0)
            self.play(Transform(hl, code_highlight(panel, 4, color=TEXT_COLOR)), run_time=0.6)
            o_mark = draw_mark(new_board, 4, "O")
            new_group.add(o_mark)
            self.play(GrowFromCenter(o_mark), run_time=0.6)
            self.play(Transform(hl, code_highlight(panel, 5, color=TEXT_COLOR)), run_time=0.6)
            self.play(Write(new_label), run_time=0.6)
            self.wait_until_bookmark("compare")
            self.play(Indicate(old_board[4], scale_factor=1.15, run_time=0.8), run_time=0.8)
            self.play(Indicate(o_mark, scale_factor=1.15, run_time=0.8), run_time=0.8)

        with self.voiceover(
            "<bookmark mark='frozen'/>Frozen dataclasses make this a rule. If code tries to set a field, "
            "Python raises Frozen Instance Error. "
            "<bookmark mark='game'/>The method place mark works the same way. Each branch makes a new Game. "
            "The old Game does not change."
        ) as tracker:
            self.wait_until_bookmark("frozen")
            self.play(Write(assign_text), run_time=0.8)
            reject(self, assign_text, error_label)
            self.wait_until_bookmark("game")
            self.play(
                FadeOut(error_label),
                FadeOut(old_group),
                FadeOut(new_group),
                FadeOut(arrow),
                FadeOut(arrow_label),
                FadeOut(old_label),
                FadeOut(new_label),
                FadeOut(hl),
                run_time=1.0,
            )
            self.play(FadeIn(old_card), FadeIn(new_card), run_time=1.0)
            self.play(GrowArrow(card_arrow), Write(card_arrow_label), Write(card_labels), run_time=0.9)

        with self.voiceover(
            "<bookmark mark='history'/>This has three good results. First, a game history is simply a list of Game objects. "
            "<bookmark mark='readers'/>Second, code can read an old board at any time, and the board stays the same. "
            "<bookmark mark='keys'/>Third, a frozen Board can be a dictionary key. The learners in videos five and six use this."
        ) as tracker:
            self.wait_until_bookmark("history")
            self.play(
                FadeOut(old_card),
                FadeOut(new_card),
                FadeOut(card_arrow),
                FadeOut(card_arrow_label),
                FadeOut(card_labels),
                FadeOut(panel),
                run_time=1.0,
            )
            self.play(LaggedStart(*[FadeIn(b, run_time=0.7) for b in strip], lag_ratio=0.2), run_time=1.8)
            self.wait_until_bookmark("readers")
            self.play(Write(read_text), run_time=0.8)
            self.play(Indicate(strip[0], scale_factor=1.08, run_time=0.8), run_time=0.8)
            self.wait_until_bookmark("keys")
            self.play(FadeIn(dict_mob), run_time=0.9)
            self.wait(1.0)
