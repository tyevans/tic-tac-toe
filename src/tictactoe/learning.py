import math
import random
from dataclasses import dataclass
from typing import Protocol

from tictactoe.game import Game
from tictactoe.value_objects import Board, Player, Position, SIZE

_ACTIONS = SIZE * SIZE
_FEATURES = _ACTIONS + 1


@dataclass(frozen=True, slots=True)
class Experience:
    board: Board
    player: Player
    action: Position
    reward: float


class ReinforcementLearner(Protocol):
    def choose_position(self, game: Game) -> Position: ...

    def learn(self, experience: Experience) -> None: ...


def _features(board: Board, player: Player) -> tuple[float, ...]:
    opponent = player.opponent
    values = []
    for index in range(_ACTIONS):
        mark = board.player_at(Position.from_index(index))
        if mark == player:
            values.append(1.0)
        elif mark == opponent:
            values.append(-1.0)
        else:
            values.append(0.0)
    values.append(1.0)
    return tuple(values)


class PolicyLearner:
    def __init__(self, learning_rate: float = 0.1, value_rate: float = 0.9, rng: random.Random | None = None) -> None:
        self._learning_rate = learning_rate
        self._value_rate = value_rate
        self._values: dict[Board, float] = {}
        self._rng = rng if rng is not None else random.Random()
        self._weights = [[0.0 for _ in range(_FEATURES)] for _ in range(_ACTIONS)]

    def _probabilities(self, board: Board, player: Player) -> tuple[tuple[int, ...], tuple[float, ...]]:
        free = tuple(index for index in range(_ACTIONS) if not board.is_occupied(Position.from_index(index)))
        features = _features(board, player)
        logits = [
            sum(weight * feature for weight, feature in zip(self._weights[action], features))
            for action in free
        ]
        peak = max(logits)
        exps = [math.exp(logit - peak) for logit in logits]
        total = sum(exps)
        return free, tuple(expired / total for expired in exps)

    def choose_position(self, game: Game, explore: bool = True) -> Position:
        free, probabilities = self._probabilities(game.board, game.current_player)
        if not explore:
            best = max(range(len(free)), key=lambda position: probabilities[position])
            return Position.from_index(free[best])
        roll = self._rng.random()
        cumulative = 0.0
        for action, probability in zip(free, probabilities):
            cumulative += probability
            if roll < cumulative:
                return Position.from_index(action)
        return Position.from_index(free[-1])

    def learn(self, experience: Experience) -> None:
        value = self._values.get(experience.board, 0.0)
        advantage = experience.reward - value
        self._values[experience.board] = self._value_rate * value + (1.0 - self._value_rate) * experience.reward
        free, probabilities = self._probabilities(experience.board, experience.player)
        features = _features(experience.board, experience.player)
        for position, action in enumerate(free):
            indicator = 1.0 if action == experience.action.index else 0.0
            scale = self._learning_rate * advantage * (indicator - probabilities[position])
            if scale == 0.0:
                continue
            weight = self._weights[action]
            for feature_index in range(_FEATURES):
                weight[feature_index] += scale * features[feature_index]
