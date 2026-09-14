from dataclasses import dataclass

from tictactoe.errors import GameAlreadyOverError, PositionOccupiedError
from tictactoe.events import DomainEvent, GameDrawn, GameStarted, GameWon, MarkPlaced
from tictactoe.value_objects import X, Board, GameStatus, Player, Position


@dataclass(frozen=True, slots=True)
class Game:
    id: str
    board: Board
    current_player: Player
    status: GameStatus

    @classmethod
    def start(cls, game_id: str) -> "Transition":
        game = cls(
            id=game_id,
            board=Board.empty(),
            current_player=X,
            status=GameStatus.IN_PROGRESS,
        )
        return Transition(game, (GameStarted(game_id),))

    def place_mark(self, position: Position) -> "Transition":
        if self.status is not GameStatus.IN_PROGRESS:
            raise GameAlreadyOverError(self.id)
        if self.board.is_occupied(position):
            raise PositionOccupiedError(position.row, position.column)

        marked_board = self.board.with_mark(position, self.current_player)
        line = marked_board.winning_line(self.current_player)

        if line is not None:
            status = GameStatus.X_WON if self.current_player == X else GameStatus.O_WON
            game = Game(self.id, marked_board, self.current_player, status)
            events: tuple[DomainEvent, ...] = (
                MarkPlaced(self.id, self.current_player, position),
                GameWon(self.id, self.current_player, line),
            )
            return Transition(game, events)

        if marked_board.is_full():
            game = Game(self.id, marked_board, self.current_player, GameStatus.DRAW)
            events = (
                MarkPlaced(self.id, self.current_player, position),
                GameDrawn(self.id),
            )
            return Transition(game, events)

        game = Game(self.id, marked_board, self.current_player.opponent, GameStatus.IN_PROGRESS)
        events = (MarkPlaced(self.id, self.current_player, position),)
        return Transition(game, events)


@dataclass(frozen=True, slots=True)
class Transition:
    game: Game
    events: tuple[DomainEvent, ...]
