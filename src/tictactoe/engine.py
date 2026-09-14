from collections.abc import Sequence

from tictactoe.commands import PlaceMark, StartGame
from tictactoe.event_bus import EventBus
from tictactoe.errors import GameAlreadyExistsError, GameNotFoundError
from tictactoe.events import DomainEvent
from tictactoe.game import Game


class GameEngine:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._games: dict[str, Game] = {}

    def start_game(self, command: StartGame) -> Game:
        if command.game_id in self._games:
            raise GameAlreadyExistsError(command.game_id)
        transition = Game.start(command.game_id)
        self._games[command.game_id] = transition.game
        self._publish(transition.events)
        return transition.game

    def place_mark(self, command: PlaceMark) -> Game:
        game = self._require(command.game_id)
        transition = game.place_mark(command.position)
        self._games[command.game_id] = transition.game
        self._publish(transition.events)
        return transition.game

    def get_game(self, game_id: str) -> Game:
        return self._require(game_id)

    def _require(self, game_id: str) -> Game:
        try:
            return self._games[game_id]
        except KeyError:
            raise GameNotFoundError(game_id) from None

    def _publish(self, events: Sequence[DomainEvent]) -> None:
        for event in events:
            self._event_bus.publish(event)
