from manim import *
from manim_voiceover import VoiceoverScene

from common import (
    BG_COLOR,
    ERROR_COLOR,
    MUTED_COLOR,
    RULE_COLOR,
    TEXT_COLOR,
    code_highlight,
    draw_mark,
    make_board,
    make_code_panel,
    make_o,
    make_x,
    reject,
    set_voice,
)

CELL_SNIPPET = '''@dataclass(frozen=True, slots=True)
class Cell:
    player: Player | None

    @property
    def display(self) -> str:
        return self.player.symbol if self.player is not None else " "'''

BOARD_SNIPPET = '''@dataclass(frozen=True, slots=True)
class Board:
    cells: tuple[Cell, ...]

    def __post_init__(self) -> None:
        if len(self.cells) != SIZE * SIZE:
            raise InvalidBoardError()

    @classmethod
    def empty(cls) -> "Board":
        return cls(tuple(Cell(None) for _ in range(SIZE * SIZE)))'''


class E1S6CellAndBoard(VoiceoverScene):
    def setup(self) -> None:
        set_voice(self)

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR
        title = Text("Cell and Board", font_size=40, color=TEXT_COLOR).to_edge(UP, buff=0.4)
        panel_cell = make_code_panel(CELL_SNIPPET).move_to([3.4, -0.3, 0.0])
        panel_board = make_code_panel(BOARD_SNIPPET).move_to([3.4, -0.3, 0.0])
        rect_cell = code_highlight(panel_cell, 2, color=TEXT_COLOR)
        rect_rule = code_highlight(panel_board, 5, 6, color=RULE_COLOR)
        rect_empty = code_highlight(panel_board, 9, 10, color=TEXT_COLOR)
        rect_len = code_highlight(panel_board, 5, color=RULE_COLOR)
        cells3 = VGroup(
            *[
                Square(side_length=1.2, stroke_color=TEXT_COLOR, stroke_width=4, fill_opacity=0)
                for _ in range(3)
            ]
        ).arrange(RIGHT, buff=0.4).move_to([-3.6, 0.5, 0.0])
        x_mark = make_x().move_to(cells3[1].get_center())
        o_mark = make_o().move_to(cells3[2].get_center())
        labels3 = VGroup(
            Text("Cell(None)", font_size=22, color=MUTED_COLOR).next_to(cells3[0], DOWN, buff=0.25),
            Text("Cell(X)", font_size=22, color=MUTED_COLOR).next_to(cells3[1], DOWN, buff=0.25),
            Text("Cell(O)", font_size=22, color=MUTED_COLOR).next_to(cells3[2], DOWN, buff=0.25),
        )
        cells_group = VGroup(cells3, x_mark, o_mark, labels3)
        squares8 = VGroup(
            *[
                Square(side_length=0.55, stroke_color=TEXT_COLOR, stroke_width=4, fill_opacity=0)
                for _ in range(8)
            ]
        ).arrange(RIGHT, buff=0.08).move_to([-3.6, 0.8, 0.0])
        counter8 = Text("8 cells", font_size=28, color=TEXT_COLOR).next_to(squares8, DOWN, buff=0.25)
        bad_mob = VGroup(squares8, counter8)
        error_label = VGroup(
            Text("InvalidBoardError:", font_size=22, color=ERROR_COLOR),
            Text("a board must have exactly 9 cells", font_size=22, color=ERROR_COLOR),
        ).arrange(DOWN, buff=0.12).move_to([-3.6, -1.0, 0.0])
        board = make_board().move_to([-3.6, -0.3, 0.0])
        empty_label = Text("Board.empty()", font_size=26, color=TEXT_COLOR).move_to([-3.6, -2.5, 0.0])
        len_text = Text("len(cells) == 9  ✓", font_size=26, color=RULE_COLOR).move_to([-3.6, -2.5, 0.0])
        game_text = Text("Game gives turns: X, O, X, O …", font_size=26, color=TEXT_COLOR).move_to(
            [-3.6, -3.05, 0.0]
        )
        marks9 = VGroup(*[draw_mark(board, i, "X") for i in range(9)])
        with self.voiceover(
            "A Cell holds one Player, or None when the cell is empty. "
            "<bookmark mark='cell_code'/>Cell has no post init check of its own. "
            "It uses the Player type, and a real Player can only be X or O."
        ) as tracker:
            self.play(Write(title))
            self.play(FadeIn(cells_group))
            self.wait_until_bookmark("cell_code")
            self.play(FadeIn(panel_cell))
            self.play(Create(rect_cell))
        with self.voiceover(
            "<bookmark mark='board_code'/>A Board is a tuple of cells. "
            "The Board has one invariant: the tuple must have exactly nine cells. "
            "<bookmark mark='bad'/>Now we try to make a Board with eight cells. "
            "<bookmark mark='reject'/>The check fails. Python raises Invalid Board Error."
        ) as tracker:
            self.wait_until_bookmark("board_code")
            self.play(FadeOut(cells_group), Transform(panel_cell, panel_board), FadeOut(rect_cell))
            self.remove(cells_group, rect_cell)
            self.play(Create(rect_rule))
            self.wait_until_bookmark("bad")
            self.play(FadeIn(squares8, lag_ratio=0.1))
            self.play(Write(counter8))
            self.wait_until_bookmark("reject")
            reject(self, bad_mob, error_label)
            self.remove(bad_mob)
            self.play(rect_rule.animate.set_color(ERROR_COLOR))
        with self.voiceover(
            "<bookmark mark='empty'/>The method empty makes the start board. "
            "It has nine cells, and each cell holds None."
        ) as tracker:
            self.wait_until_bookmark("empty")
            self.play(FadeOut(error_label))
            self.remove(error_label)
            self.play(Transform(rect_rule, rect_empty))
            self.play(Create(board))
            self.play(Write(empty_label))
        with self.voiceover(
            "<bookmark mark='limits'/>Be careful here. The Board checks only the number of cells. "
            "It does not count turns. A board with nine X marks passes the check. "
            "<bookmark mark='game_guard'/>The Game object prevents such a board in play, "
            "because Game gives the turns to X and O in order."
        ) as tracker:
            self.wait_until_bookmark("limits")
            self.play(FadeOut(empty_label))
            self.remove(empty_label)
            self.play(FadeIn(marks9, lag_ratio=0.05))
            self.play(Write(len_text))
            self.play(Transform(rect_rule, rect_len))
            self.wait_until_bookmark("game_guard")
            self.play(Write(game_text))
            self.play(marks9.animate.set_opacity(0.3))
        self.wait(1)
