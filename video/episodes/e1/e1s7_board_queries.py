from manim import *
from manim_voiceover import VoiceoverScene

from common import (
    BG_COLOR,
    ERROR_COLOR,
    MUTED_COLOR,
    NEUTRAL_COLOR,
    RULE_COLOR,
    TEXT_COLOR,
    X_COLOR,
    cell_indices,
    code_highlight,
    draw_mark,
    make_board,
    make_code_panel,
    make_o,
    reject,
    set_voice,
)

WITH_MARK_SNIPPET = '''    def with_mark(self, position: Position, player: Player) -> "Board":
        if self.is_occupied(position):
            raise PositionOccupiedError(position.row, position.column)
        cells = list(self.cells)
        cells[position.index] = Cell(player)
        return Board(tuple(cells))'''

WINNING_LINE_SNIPPET = '''    def winning_line(self, player: Player) -> tuple[Position, Position, Position] | None:
        for first, second, third in WINNING_LINES:
            positions = (
                Position.from_index(first),
                Position.from_index(second),
                Position.from_index(third),
            )
            if all(self.player_at(position) == player for position in positions):
                return positions
        return None'''

IS_FULL_SNIPPET = '''    def is_full(self) -> bool:
        return all(cell.player is not None for cell in self.cells)'''


class E1S7BoardQueries(VoiceoverScene):
    def setup(self) -> None:
        set_voice(self)

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR
        title = Text("The Board answers questions", font_size=40, color=TEXT_COLOR).to_edge(UP, buff=0.4)
        board = make_board().move_to([-3.6, -0.3, 0.0])
        indices = cell_indices(board)
        x4 = draw_mark(board, 4, "X")
        panel = make_code_panel(WITH_MARK_SNIPPET).move_to([3.4, -0.3, 0.0])
        panel_wl = make_code_panel(WINNING_LINE_SNIPPET).move_to([3.4, -0.3, 0.0])
        panel_if = make_code_panel(IS_FULL_SNIPPET).move_to([3.4, -0.3, 0.0])
        rect = code_highlight(panel, 1, 2, color=RULE_COLOR)
        rect_wl = code_highlight(panel_wl, 7, 8, color=RULE_COLOR)
        rect_if = code_highlight(panel_if, 0, 1, color=RULE_COLOR)
        o_probe = make_o().move_to([-3.6, 2.6, 0.0])
        error_label = VGroup(
            Text("PositionOccupiedError:", font_size=22, color=ERROR_COLOR),
            Text("cell (1, 1) is already occupied", font_size=22, color=ERROR_COLOR),
        ).arrange(DOWN, buff=0.12).move_to([-3.6, -2.5, 0.0])
        new_marks = VGroup(
            draw_mark(board, 0, "X"),
            draw_mark(board, 8, "X"),
            draw_mark(board, 1, "O"),
            draw_mark(board, 2, "O"),
        )
        win_line = Line(board[0].get_center(), board[8].get_center(), stroke_color=X_COLOR, stroke_width=8)
        win_result = Text(
            "(Position(0, 0), Position(1, 1), Position(2, 2))",
            font_size=20,
            color=TEXT_COLOR,
        ).move_to([-3.6, -2.5, 0.0])
        fills = VGroup(
            *[
                Square(side_length=1.2 * 0.98, stroke_opacity=0)
                .set_fill(MUTED_COLOR, opacity=0.3)
                .move_to(board[i].get_center())
                for i in (3, 5, 6, 7)
            ]
        )
        full_result = Text("False", font_size=28, color=NEUTRAL_COLOR).move_to([-3.6, -2.5, 0.0])
        why_labels = VGroup(
            Text("strategies", font_size=14, color=MUTED_COLOR),
            Text("learners", font_size=14, color=MUTED_COLOR),
            Text("demo printer", font_size=14, color=MUTED_COLOR),
        ).arrange(DOWN, buff=0.45, aligned_edge=RIGHT)
        why_labels.align_to([-5.85, 0.0, 0.0], RIGHT)
        why_arrows = VGroup(
            *[
                Arrow(
                    label.get_right() + RIGHT * 0.04,
                    [board.get_left()[0] - 0.08, label.get_center()[1], 0.0],
                    buff=0,
                    stroke_color=MUTED_COLOR,
                    stroke_width=3,
                    max_tip_length_to_length_ratio=0.3,
                )
                for label in why_labels
            ]
        )
        why_group = VGroup(why_labels, why_arrows)
        with self.voiceover(
            "The Board also answers questions about itself. "
            "<bookmark mark='with_mark'/>The method with mark puts a player's mark in one cell. "
            "<bookmark mark='guard'/>First, it checks that the cell is empty."
        ) as tracker:
            self.play(Write(title))
            self.play(FadeIn(VGroup(board, indices, x4)))
            self.wait_until_bookmark("with_mark")
            self.play(FadeIn(panel))
            self.wait_until_bookmark("guard")
            self.play(Create(rect))
        with self.voiceover(
            "<bookmark mark='occupied'/>Here, the center cell already holds an X. "
            "We try to put an O there. "
            "<bookmark mark='reject'/>The cell is occupied, so the Board raises Position Occupied Error. "
            "The board does not change."
        ) as tracker:
            self.wait_until_bookmark("occupied")
            self.play(FadeIn(o_probe), run_time=0.4)
            self.play(o_probe.animate.move_to(x4.get_center()), run_time=1.0)
            self.wait_until_bookmark("reject")
            reject(self, o_probe, error_label)
            self.remove(o_probe)
            self.play(rect.animate.set_color(ERROR_COLOR))
            self.play(Indicate(x4))
        with self.voiceover(
            "<bookmark mark='winning_line'/>The method winning line checks the eight lines for one player. "
            "It gives back the three positions of a line, or None. "
            "<bookmark mark='is_full'/>The method is full tells if all nine cells hold a mark."
        ) as tracker:
            self.wait_until_bookmark("winning_line")
            self.play(FadeOut(error_label), Transform(panel, panel_wl), Transform(rect, rect_wl))
            self.remove(error_label)
            self.play(FadeIn(new_marks, lag_ratio=0.15))
            self.play(Create(win_line))
            self.play(Write(win_result))
            self.wait_until_bookmark("is_full")
            self.play(Transform(panel, panel_if), Transform(rect, rect_if))
            self.play(FadeOut(win_line), FadeOut(win_result))
            self.remove(win_line, win_result)
            self.play(FadeIn(fills), run_time=0.5)
            self.wait(0.5)
            self.play(FadeOut(fills), run_time=0.5)
            self.play(Write(full_result))
        with self.voiceover(
            "<bookmark mark='why'/>These rules are part of the Board. "
            "Other code asks the Board. "
            "It does not keep its own copy of the rules."
        ) as tracker:
            self.wait_until_bookmark("why")
            self.play(FadeIn(why_group))
        self.wait(1)
