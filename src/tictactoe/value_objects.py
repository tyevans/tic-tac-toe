from dataclasses import dataclass
from enum import Enum

from tictactoe.errors import InvalidBoardError, InvalidPlayerError, InvalidPositionError, PositionOccupiedError

SIZE = 3

WINNING_LINES: tuple[tuple[int, int, int], ...] = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


@dataclass(frozen=True, slots=True)
class Player:
    symbol: str

    def __post_init__(self) -> None:
        if self.symbol not in ("X", "O"):
            raise InvalidPlayerError(self.symbol)

    @property
    def opponent(self) -> "Player":
        return Player("O" if self.symbol == "X" else "X")


X = Player("X")
O = Player("O")


class GameStatus(Enum):
    IN_PROGRESS = "in_progress"
    X_WON = "x_won"
    O_WON = "o_won"
    DRAW = "draw"


@dataclass(frozen=True, slots=True)
class Position:
    row: int
    column: int

    def __post_init__(self) -> None:
        if not 0 <= self.row < SIZE or not 0 <= self.column < SIZE:
            raise InvalidPositionError(self.row, self.column)

    @property
    def index(self) -> int:
        return self.row * SIZE + self.column

    @classmethod
    def from_index(cls, index: int) -> "Position":
        if not 0 <= index < SIZE * SIZE:
            raise InvalidPositionError(index // SIZE, index % SIZE)
        return cls(index // SIZE, index % SIZE)


@dataclass(frozen=True, slots=True)
class Cell:
    player: Player | None

    @property
    def display(self) -> str:
        return self.player.symbol if self.player is not None else " "


@dataclass(frozen=True, slots=True)
class Board:
    cells: tuple[Cell, ...]

    def __post_init__(self) -> None:
        if len(self.cells) != SIZE * SIZE:
            raise InvalidBoardError()

    @classmethod
    def empty(cls) -> "Board":
        return cls(tuple(Cell(None) for _ in range(SIZE * SIZE)))

    def cell_at(self, position: Position) -> Cell:
        return self.cells[position.index]

    def player_at(self, position: Position) -> Player | None:
        return self.cell_at(position).player

    def is_occupied(self, position: Position) -> bool:
        return self.cell_at(position).player is not None

    def is_full(self) -> bool:
        return all(cell.player is not None for cell in self.cells)

    def with_mark(self, position: Position, player: Player) -> "Board":
        if self.is_occupied(position):
            raise PositionOccupiedError(position.row, position.column)
        cells = list(self.cells)
        cells[position.index] = Cell(player)
        return Board(tuple(cells))

    def winning_line(self, player: Player) -> tuple[Position, Position, Position] | None:
        for first, second, third in WINNING_LINES:
            positions = (
                Position.from_index(first),
                Position.from_index(second),
                Position.from_index(third),
            )
            if all(self.player_at(position) == player for position in positions):
                return positions
        return None

    def render(self) -> str:
        rows = []
        for row in range(SIZE):
            marks = [self.cell_at(Position(row, column)).display for column in range(SIZE)]
            rows.append(f" {marks[0]} | {marks[1]} | {marks[2]} ")
        return "\n---+---+---\n".join(rows)
