from manim import *
from manim_voiceover import VoiceoverScene

from common import (
    BG_COLOR,
    ERROR_COLOR,
    EVENT_COLOR,
    NEUTRAL_COLOR,
    O_COLOR,
    TEXT_COLOR,
    cell_indices,
    code_highlight,
    draw_mark,
    make_board,
    make_code_panel,
    make_event_card,
    make_o,
    make_x,
    reject,
    set_voice,
)

GUARDS_CODE = '''    def place_mark(self, position: Position) -> "Transition":
        if self.status is not GameStatus.IN_PROGRESS:
            raise GameAlreadyOverError(self.id)
        if self.board.is_occupied(position):
            raise PositionOccupiedError(position.row, position.column)

        marked_board = self.board.with_mark(position, self.current_player)
        line = marked_board.winning_line(self.current_player)'''

WIN_CODE = '''        if line is not None:
            status = GameStatus.X_WON if self.current_player == X else GameStatus.O_WON
            game = Game(self.id, marked_board, self.current_player, status)
            events: tuple[DomainEvent, ...] = (
                MarkPlaced(self.id, self.current_player, position),
                GameWon(self.id, self.current_player, line),
            )
            return Transition(game, events)'''

REST_CODE = '''        if marked_board.is_full():
            game = Game(self.id, marked_board, self.current_player, GameStatus.DRAW)
            events = (
                MarkPlaced(self.id, self.current_player, position),
                GameDrawn(self.id),
            )
            return Transition(game, events)

        game = Game(self.id, marked_board, self.current_player.opponent, GameStatus.IN_PROGRESS)
        events = (MarkPlaced(self.id, self.current_player, position),)
        return Transition(game, events)'''

PANEL_POS = [3.4, -0.3, 0.0]


class E1S10PlaceMark(VoiceoverScene):
    def setup(self) -> None:
        set_voice(self)

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR
        title = Text("Game.place_mark", font_size=40, color=TEXT_COLOR).to_edge(UP, buff=0.4)
        panel = make_code_panel(GUARDS_CODE).move_to(PANEL_POS)
        board = make_board().scale(0.8).move_to([-3.6, 0.6, 0])
        start_marks = VGroup(
            *[draw_mark(board, i, "X") for i in (0, 1, 3)]
            + [draw_mark(board, i, "O") for i in (2, 4)]
        )
        status = Text("status: IN_PROGRESS", font_size=24, color=TEXT_COLOR).move_to([-3.6, -1.6, 0.0])
        status_won = Text("status: O_WON", font_size=24, color=O_COLOR).move_to([-3.6, -1.6, 0.0])
        turn = Text("current_player: O", font_size=24, color=O_COLOR).move_to([-3.6, -2.1, 0.0])
        board_grp = VGroup(board, cell_indices(board, font_size=22), start_marks, status, turn)
        o_drop = make_o().move_to(board[6].get_center() + [0, 2.8 - board[6].get_center()[1], 0])
        win_line = Line(
            board[2].get_center(), board[6].get_center(), stroke_color=O_COLOR, stroke_width=8
        )
        card_mp = make_event_card("MarkPlaced", ["player: O", "position: (2, 0)"])
        card_gw = make_event_card("GameWon", ["winner: O", "line: 2, 4, 6"])
        cards_grp = VGroup(card_mp, card_gw).arrange(RIGHT, buff=0.3).scale(0.75).move_to([-3.6, -3.0, 0.0])
        try_mark = make_x().move_to([-2.6, 2.8, 0.0])
        error_label = Text(
            "GameAlreadyOverError: game g1 is already over", font_size=22, color=ERROR_COLOR
        ).scale(0.94).move_to([-3.6, -3.0, 0.0])
        with self.voiceover(
            "The method place mark applies one move. We read it in three parts. "
            "<bookmark mark='guards'/>Part one has two guards. First, the game must be in progress. "
            "Second, the cell must be empty. "
            "<bookmark mark='marked'/>Then Game asks the Board for a marked board. "
            "Game also asks if the current player now has a line."
        ) as tracker:
            self.play(Write(title), run_time=1.2)
            self.play(FadeIn(panel), run_time=1.0)
            self.wait_until_bookmark("guards")
            hl = code_highlight(panel, 1, 2)
            self.play(FadeIn(hl), run_time=0.6)
            self.wait(2.0)
            self.play(Transform(hl, code_highlight(panel, 3, 4)), run_time=0.7)
            self.wait_until_bookmark("marked")
            self.play(Transform(hl, code_highlight(panel, 6, 7, color=TEXT_COLOR)), run_time=0.7)
        with self.voiceover(
            "<bookmark mark='example'/>Here is a real game from the demo. X has cells 0, 1, and 3. "
            "O has cells 2 and 4. Now O plays cell 6."
        ) as tracker:
            self.wait_until_bookmark("example")
            self.play(FadeIn(board_grp), run_time=1.2)
            self.play(FadeIn(o_drop), run_time=0.4)
            self.play(o_drop.animate.move_to(board[6].get_center()), run_time=1.0)
        with self.voiceover(
            "<bookmark mark='win_code'/>Part two is the win branch. "
            "<bookmark mark='win_line'/>Cells 2, 4, and 6 make a diagonal line for O. "
            "The new Game gets the status O won. "
            "<bookmark mark='win_events'/>The list of what happened has two items: Mark Placed and Game Won."
        ) as tracker:
            self.wait_until_bookmark("win_code")
            win_panel = make_code_panel(WIN_CODE).move_to(PANEL_POS)
            self.play(
                Transform(panel, win_panel),
                Transform(hl, code_highlight(win_panel, 0, color=TEXT_COLOR)),
                run_time=1.2,
            )
            self.wait_until_bookmark("win_line")
            self.play(
                Create(win_line),
                Transform(hl, code_highlight(panel, 1, 2, color=TEXT_COLOR)),
                Transform(status, status_won),
                run_time=1.2,
            )
            self.wait_until_bookmark("win_events")
            self.play(Transform(hl, code_highlight(panel, 4, 5, color=EVENT_COLOR)), run_time=0.6)
            self.play(FadeIn(card_mp), run_time=0.5)
            self.play(FadeIn(card_gw), run_time=0.5)
        with self.voiceover(
            "<bookmark mark='rest_code'/>Part three has two more branches. "
            "If the board is full and there is no line, the status is draw. "
            "<bookmark mark='continue'/>If not, the game continues. "
            "The new Game gives the turn to the opponent."
        ) as tracker:
            self.wait_until_bookmark("rest_code")
            rest_panel = make_code_panel(REST_CODE).move_to(PANEL_POS)
            self.play(
                Transform(panel, rest_panel),
                Transform(hl, code_highlight(rest_panel, 0, 1, 2, 3, 4, 5, 6, color=NEUTRAL_COLOR)),
                run_time=1.2,
            )
            self.wait_until_bookmark("continue")
            self.play(Transform(hl, code_highlight(panel, 8, 9, 10, color=TEXT_COLOR)), run_time=0.8)
        with self.voiceover(
            "<bookmark mark='over'/>Our game is over now. We try to play cell 8. "
            "<bookmark mark='reject'/>The first guard fails. Game raises Game Already Over Error."
        ) as tracker:
            self.wait_until_bookmark("over")
            guards_panel = make_code_panel(GUARDS_CODE).move_to(PANEL_POS)
            err_rect = code_highlight(guards_panel, 1, 2, color=ERROR_COLOR)
            self.play(Transform(panel, guards_panel), FadeOut(hl), FadeIn(try_mark), run_time=1.0)
            self.play(try_mark.animate.move_to([-2.6, 2.4, 0.0]), run_time=0.8)
            self.wait_until_bookmark("reject")
            self.play(FadeOut(cards_grp), run_time=0.5)
            reject(self, try_mark, error_label)
            self.play(FadeIn(err_rect), run_time=0.5)
        self.wait(1.0)
