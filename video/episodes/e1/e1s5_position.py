from manim import *
from manim_voiceover import VoiceoverScene

from common import (
    BG_COLOR,
    ERROR_COLOR,
    MUTED_COLOR,
    RULE_COLOR,
    TEXT_COLOR,
    cell_indices,
    code_highlight,
    make_board,
    make_code_panel,
    reject,
    set_voice,
)

CHECK_SNIPPET = '''SIZE = 3

@dataclass(frozen=True, slots=True)
class Position:
    row: int
    column: int

    def __post_init__(self) -> None:
        if not 0 <= self.row < SIZE or not 0 <= self.column < SIZE:
            raise InvalidPositionError(self.row, self.column)'''

INDEX_SNIPPET = '''    @property
    def index(self) -> int:
        return self.row * SIZE + self.column

    @classmethod
    def from_index(cls, index: int) -> "Position":
        if not 0 <= index < SIZE * SIZE:
            raise InvalidPositionError(index // SIZE, index % SIZE)
        return cls(index // SIZE, index % SIZE)'''


class E1S5Position(VoiceoverScene):
    def setup(self) -> None:
        set_voice(self)

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR
        title = Text("The Position value object", font_size=40, color=TEXT_COLOR).to_edge(UP, buff=0.4)
        board = make_board().move_to([-3.6, -0.3, 0.0])
        indices = cell_indices(board, font_size=22, color=MUTED_COLOR)
        row_labels = VGroup(
            Text("row 0", font_size=20, color=MUTED_COLOR).move_to([-6.05, 0.9, 0.0]),
            Text("row 1", font_size=20, color=MUTED_COLOR).move_to([-6.05, -0.3, 0.0]),
            Text("row 2", font_size=20, color=MUTED_COLOR).move_to([-6.05, -1.5, 0.0]),
        )
        col_labels = VGroup(
            Text("col 0", font_size=20, color=MUTED_COLOR).move_to([-4.2, 1.75, 0.0]),
            Text("col 1", font_size=20, color=MUTED_COLOR).move_to([-3.6, 1.75, 0.0]),
            Text("col 2", font_size=20, color=MUTED_COLOR).move_to([-3.0, 1.75, 0.0]),
        )
        panel_check = make_code_panel(CHECK_SNIPPET).move_to([3.4, -0.3, 0.0])
        panel_index = make_code_panel(INDEX_SNIPPET).move_to([3.4, -0.3, 0.0])
        rect_check = code_highlight(panel_check, 8, color=RULE_COLOR)
        rect_error = code_highlight(panel_check, 9, color=ERROR_COLOR)
        rect_index = code_highlight(panel_index, 2, color=TEXT_COLOR)
        rect_from = code_highlight(panel_index, 4, 5, 6, 7, 8, color=TEXT_COLOR)
        fill5 = Square(side_length=1.176, stroke_width=0).set_fill(TEXT_COLOR, opacity=0.3).move_to(
            board[5].get_center()
        )
        token_12 = Text("Position(1, 2)", font_size=28, color=TEXT_COLOR).move_to([-2.4, -2.9, 0.0])
        token_50 = Text("Position(5, 0)", font_size=28, color=TEXT_COLOR).move_to([-2.4, -2.9, 0.0])
        ghost = (
            Square(side_length=1.2, fill_opacity=0)
            .set_stroke(color=ERROR_COLOR, width=3)
            .set_dashed_stroke(0.14)
            .move_to([-4.2, -2.7, 0.0])
        )
        row5_text = Text("row 5", font_size=22, color=ERROR_COLOR).move_to(ghost.get_center())
        ghost_arrow = Arrow(
            ghost.get_bottom() + DOWN * 0.05,
            ghost.get_bottom() + DOWN * 0.55,
            stroke_color=ERROR_COLOR,
            stroke_width=4,
            buff=0.02,
        )
        bad_group = VGroup(token_50, ghost, row5_text, ghost_arrow)
        error_label = Text(
            "InvalidPositionError: invalid position (5, 0)",
            font_size=22,
            color=ERROR_COLOR,
        ).move_to([-3.6, -3.4, 0.0])
        formula = Text("1 × 3 + 2 = 5", font_size=32, color=TEXT_COLOR).move_to([-2.6, -3.4, 0.0])
        index_5 = indices[5]
        arrow_row1 = Arrow(
            index_5.get_center(),
            row_labels[1].get_center(),
            stroke_color=TEXT_COLOR,
            stroke_width=4,
            buff=0.12,
        )
        arrow_col2 = Arrow(
            index_5.get_center(),
            col_labels[2].get_center(),
            stroke_color=TEXT_COLOR,
            stroke_width=4,
            buff=0.12,
        )
        with self.voiceover(
            "A Position is one cell on the board, as a row and a column. <bookmark mark='code'/>"
            "SIZE is 3, so a row and a column must each be 0, 1, or 2."
        ) as tracker:
            self.play(Write(title))
            self.play(FadeIn(board), FadeIn(indices))
            self.play(FadeIn(row_labels, shift=RIGHT * 0.3), FadeIn(col_labels, shift=DOWN * 0.3))
            self.wait_until_bookmark("code")
            self.play(FadeIn(panel_check))
            self.play(Create(rect_check))
        with self.voiceover(
            "<bookmark mark='good'/>Position with row 1 and column 2 is correct. "
            "It is the cell in the middle row, on the right. "
            "<bookmark mark='bad'/>Now we try row 5, column 0. "
            "<bookmark mark='reject'/>Row 5 is not on the board. Python raises Invalid Position Error."
        ) as tracker:
            self.wait_until_bookmark("good")
            self.play(FadeIn(token_12))
            self.play(FadeIn(fill5))
            self.play(Indicate(row_labels[1]), Indicate(col_labels[2]))
            self.wait_until_bookmark("bad")
            self.play(FadeOut(token_12), FadeOut(fill5))
            self.remove(token_12, fill5)
            self.play(FadeIn(bad_group))
            self.wait_until_bookmark("reject")
            reject(self, bad_group, error_label)
            self.remove(bad_group)
            self.play(Create(rect_error))
        with self.voiceover(
            "<bookmark mark='index_code'/>The index property changes a row and a column into one cell number. "
            "The cell number is the row times 3, plus the column. "
            "<bookmark mark='index_example'/>Row 1, column 2 gives 1 times 3, plus 2. That is 5. "
            "<bookmark mark='from_index'/>The method from index does the opposite. "
            "It changes cell number 5 back into row 1, column 2."
        ) as tracker:
            self.wait_until_bookmark("index_code")
            self.play(FadeOut(error_label), FadeOut(rect_check), FadeOut(rect_error))
            self.remove(error_label, rect_check, rect_error)
            self.play(Transform(panel_check, panel_index))
            self.play(Create(rect_index))
            self.wait_until_bookmark("index_example")
            self.play(FadeIn(fill5))
            self.play(Write(formula))
            self.play(Indicate(index_5))
            self.wait_until_bookmark("from_index")
            self.play(Transform(rect_index, rect_from))
            self.play(Create(arrow_row1), Create(arrow_col2))
        self.wait(1)
