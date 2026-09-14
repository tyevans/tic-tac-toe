from manim import *
from manim_voiceover import VoiceoverScene

from common import (
    BG_COLOR,
    NEUTRAL_COLOR,
    RULE_COLOR,
    TEXT_COLOR,
    cell_indices,
    code_highlight,
    draw_mark,
    make_board,
    make_code_panel,
    make_o,
    make_x,
    set_voice,
)

WINNING_LINES_SNIPPET = """WINNING_LINES: tuple[tuple[int, int, int], ...] = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)"""

WINNING_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)

TURN_MOVES = ((4, "X"), (0, "O"), (8, "X"))

DRAW_POSITION = ("X", "X", "O", "O", "O", "X", "X", "O", "X")


class E1S2GameRules(VoiceoverScene):
    def setup(self) -> None:
        set_voice(self)

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR
        title = Text("The rules of tic-tac-toe", font_size=40, color=TEXT_COLOR).to_edge(UP, buff=0.4)
        board_center = [-3.6, -0.3, 0.0]
        board = make_board().move_to(board_center)
        indices = cell_indices(board, font_size=22)
        x_mark = make_x().scale(0.8).move_to([board_center[0] - 0.9, board_center[1], 0.0])
        o_mark = make_o().scale(0.8).move_to([board_center[0] + 0.9, board_center[1], 0.0])
        counter = Text("8 lines", font_size=32, color=RULE_COLOR).move_to(
            [board_center[0], board.get_bottom()[1] - 0.5, 0.0]
        )
        with self.voiceover(
            "Tic-tac-toe has two players, X and O. <bookmark mark='grid'/>"
            "They play on a grid of three rows and three columns. That makes nine cells. "
            "<bookmark mark='indices'/>The code gives each cell a number from 0 to 8. "
            "Cell 0 is at the top left. Cell 8 is at the bottom right."
        ) as tracker:
            self.play(Write(title))
            self.play(FadeIn(x_mark), FadeIn(o_mark))
            self.wait_until_bookmark("grid")
            self.play(FadeOut(x_mark), FadeOut(o_mark), Create(board))
            self.wait_until_bookmark("indices")
            self.play(FadeIn(indices, lag_ratio=0.1))
            self.play(Indicate(indices[0]))
            self.play(Indicate(indices[8]))
        with self.voiceover(
            "<bookmark mark='turns'/>X plays first. Then the players take turns. "
            "In each turn, a player puts one mark in one empty cell."
        ) as tracker:
            self.wait_until_bookmark("turns")
            turn_marks = VGroup()
            for i, (cell, player) in enumerate(TURN_MOVES):
                mark = draw_mark(board, cell, player)
                turn_marks.add(mark)
                self.play(FadeIn(mark), run_time=0.3)
                if i < len(TURN_MOVES) - 1:
                    self.wait(0.5)
            self.play(FadeOut(turn_marks))
        with self.voiceover(
            "<bookmark mark='lines'/>A player wins with three marks in a line. "
            "There are eight lines: three rows, three columns, and two diagonals. "
            "<bookmark mark='code'/>The code keeps the eight lines as plain data, "
            "in a tuple with the name winning lines. "
            "<bookmark mark='line_example'/>Each line is three cell numbers. "
            "For example, 0, 4, 8 is a diagonal."
        ) as tracker:
            self.wait_until_bookmark("lines")
            for first, middle, last in WINNING_LINES:
                line = Line(
                    board[first].get_center(),
                    board[last].get_center(),
                    stroke_color=RULE_COLOR,
                    stroke_width=8,
                )
                self.play(Create(line), run_time=0.4)
                self.play(FadeOut(line), run_time=0.2)
            self.play(FadeIn(counter))
            self.wait_until_bookmark("code")
            panel = make_code_panel(WINNING_LINES_SNIPPET).move_to([3.4, -0.3, 0.0])
            self.play(FadeIn(panel))
            self.wait_until_bookmark("line_example")
            example_line = Line(
                board[0].get_center(),
                board[8].get_center(),
                stroke_color=RULE_COLOR,
                stroke_width=8,
            )
            example_rect = code_highlight(panel, 7, color=RULE_COLOR)
            self.play(Create(example_line), Create(example_rect))
        with self.voiceover(
            "<bookmark mark='draw'/>If all nine cells are full and no player has a line, "
            "the game is a draw."
        ) as tracker:
            self.wait_until_bookmark("draw")
            self.play(FadeOut(example_line), FadeOut(example_rect))
            for cell, player in enumerate(DRAW_POSITION):
                mark = draw_mark(board, cell, player)
                self.play(FadeIn(mark), run_time=0.15)
            draw_text = Text("DRAW", font_size=40, color=NEUTRAL_COLOR).move_to(counter.get_center())
            self.play(FadeOut(counter), FadeIn(draw_text))
            self.remove(counter)
        self.wait(1)
