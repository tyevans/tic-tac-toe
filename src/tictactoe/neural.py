import math
import random

from tictactoe.game import Game
from tictactoe.learning import Experience
from tictactoe.value_objects import Board, Player, Position, SIZE

_INPUT_SIZE = SIZE * SIZE
_MASK = -1e9


class _Feedforward:
    def __init__(self, input_size: int, hidden_size: int, output_size: int, rng: random.Random) -> None:
        input_scale = 1.0 / math.sqrt(input_size)
        hidden_scale = 1.0 / math.sqrt(hidden_size)
        self._w1 = [[rng.uniform(-input_scale, input_scale) for _ in range(input_size)] for _ in range(hidden_size)]
        self._b1 = [0.0 for _ in range(hidden_size)]
        self._w2 = [[rng.uniform(-hidden_scale, hidden_scale) for _ in range(hidden_size)] for _ in range(output_size)]
        self._b2 = [0.0 for _ in range(output_size)]

    def forward(self, x: tuple[float, ...]) -> tuple[list[float], list[float]]:
        hidden = [
            math.tanh(sum(weight * value for weight, value in zip(row, x)) + bias)
            for row, bias in zip(self._w1, self._b1)
        ]
        logits = [
            sum(weight * value for weight, value in zip(row, hidden)) + bias
            for row, bias in zip(self._w2, self._b2)
        ]
        return hidden, logits

    def update(self, grad_logits: list[float], hidden: list[float], x: tuple[float, ...], learning_rate: float) -> None:
        grad_hidden = [0.0 for _ in self._b1]
        for out_index, grad_logit in enumerate(grad_logits):
            if grad_logit == 0.0:
                continue
            row = self._w2[out_index]
            for hidden_index, weight in enumerate(row):
                row[hidden_index] += learning_rate * grad_logit * hidden[hidden_index]
                grad_hidden[hidden_index] += grad_logit * weight
            self._b2[out_index] += learning_rate * grad_logit
        for hidden_index in range(len(self._b1)):
            grad_hidden[hidden_index] *= 1.0 - hidden[hidden_index] * hidden[hidden_index]
        for hidden_index, grad_z in enumerate(grad_hidden):
            if grad_z == 0.0:
                continue
            row = self._w1[hidden_index]
            for input_index, weight in enumerate(row):
                row[input_index] += learning_rate * grad_z * x[input_index]
            self._b1[hidden_index] += learning_rate * grad_z


def _features(board: Board, player: Player) -> tuple[float, ...]:
    opponent = player.opponent
    values = []
    for cell in board.cells:
        if cell.player == player:
            values.append(1.0)
        elif cell.player == opponent:
            values.append(-1.0)
        else:
            values.append(0.0)
    return tuple(values)


def _free_indices(board: Board) -> tuple[int, ...]:
    return tuple(index for index, cell in enumerate(board.cells) if cell.player is None)


def _mask_occupied(logits: list[float], board: Board) -> None:
    for index, cell in enumerate(board.cells):
        if cell.player is not None:
            logits[index] = _MASK


def _softmax(logits: list[float]) -> list[float]:
    peak = max(logits)
    exps = [math.exp(logit - peak) for logit in logits]
    total = sum(exps)
    return [value / total for value in exps]


class NeuralPolicyLearner:
    def __init__(
        self,
        hidden_size: int = 16,
        learning_rate: float = 0.1,
        value_rate: float = 0.9,
        rng: random.Random | None = None,
    ) -> None:
        self._learning_rate = learning_rate
        self._value_rate = value_rate
        self._rng = rng if rng is not None else random.Random()
        self._net = _Feedforward(_INPUT_SIZE, hidden_size, _INPUT_SIZE, self._rng)
        self._values: dict[Board, float] = {}

    def _probabilities(self, board: Board, player: Player) -> list[float]:
        logits = self._net.forward(_features(board, player))[1]
        _mask_occupied(logits, board)
        return _softmax(logits)

    def choose_position(self, game: Game, explore: bool = True) -> Position:
        probabilities = self._probabilities(game.board, game.current_player)
        free = _free_indices(game.board)
        if not explore:
            return Position.from_index(max(free, key=probabilities.__getitem__))
        roll = self._rng.random()
        cumulative = 0.0
        for index in free:
            cumulative += probabilities[index]
            if roll < cumulative:
                return Position.from_index(index)
        return Position.from_index(free[-1])

    def learn(self, experience: Experience) -> None:
        value = self._values.get(experience.board, 0.0)
        advantage = experience.reward - value
        self._values[experience.board] = self._value_rate * value + (1.0 - self._value_rate) * experience.reward
        if advantage == 0.0:
            return
        features = _features(experience.board, experience.player)
        hidden, logits = self._net.forward(features)
        _mask_occupied(logits, experience.board)
        probabilities = _softmax(logits)
        grad_logits = [-probability for probability in probabilities]
        grad_logits[experience.action.index] += 1.0
        for index in range(_INPUT_SIZE):
            grad_logits[index] *= advantage
        self._net.update(grad_logits, hidden, features, self._learning_rate)
