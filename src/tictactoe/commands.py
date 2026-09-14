from dataclasses import dataclass

from tictactoe.value_objects import Position


@dataclass(frozen=True, slots=True)
class Command:
    game_id: str


@dataclass(frozen=True, slots=True)
class StartGame(Command):
    pass


@dataclass(frozen=True, slots=True)
class PlaceMark(Command):
    position: Position
