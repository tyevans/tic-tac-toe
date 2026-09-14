from dataclasses import dataclass

from tictactoe.value_objects import Player, Position


@dataclass(frozen=True, slots=True)
class DomainEvent:
    pass


@dataclass(frozen=True, slots=True)
class GameStarted(DomainEvent):
    game_id: str


@dataclass(frozen=True, slots=True)
class MarkPlaced(DomainEvent):
    game_id: str
    player: Player
    position: Position


@dataclass(frozen=True, slots=True)
class GameWon(DomainEvent):
    game_id: str
    winner: Player
    winning_line: tuple[Position, Position, Position]


@dataclass(frozen=True, slots=True)
class GameDrawn(DomainEvent):
    game_id: str
