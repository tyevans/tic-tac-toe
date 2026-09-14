import random
from typing import Protocol

from tictactoe.game import Game
from tictactoe.value_objects import Board, Player, Position, SIZE, WINNING_LINES


class Strategy(Protocol):
    def choose_position(self, game: Game) -> Position: ...


class FirstAvailableStrategy:
    def choose_position(self, game: Game) -> Position:
        board = game.board
        free = [
            Position.from_index(index)
            for index in range(SIZE * SIZE)
            if not board.is_occupied(Position.from_index(index))
        ]
        return free[0]


class MinimaxStrategy:
    def choose_position(self, game: Game) -> Position:
        board = game.board
        me = game.current_player
        candidates = [
            (self._score(board.with_mark(Position.from_index(index), me), me.opponent, me), index)
            for index in range(SIZE * SIZE)
            if not board.is_occupied(Position.from_index(index))
        ]
        _, best_index = max(candidates, key=lambda candidate: candidate[0])
        return Position.from_index(best_index)

    def _score(self, board: Board, player_to_move: Player, me: Player) -> int:
        if board.winning_line(me) is not None:
            return 10
        if board.winning_line(me.opponent) is not None:
            return -10
        if board.is_full():
            return 0
        scores = [
            self._score(board.with_mark(Position.from_index(index), player_to_move), player_to_move.opponent, me)
            for index in range(SIZE * SIZE)
            if not board.is_occupied(Position.from_index(index))
        ]
        return max(scores) if player_to_move == me else min(scores)


class ThreatBuilderStrategy:
    def __init__(self, rng: random.Random) -> None:
        self.rng = rng

    def choose_position(self, game: Game) -> Position:
        board = game.board
        me = game.current_player
        free = [
            Position.from_index(index)
            for index in range(SIZE * SIZE)
            if not board.is_occupied(Position.from_index(index))
        ]
        wins = [position for position in free if board.with_mark(position, me).winning_line(me) is not None]
        if wins:
            return self.rng.choice(wins)
        blocks = [position for position in free if board.with_mark(position, me.opponent).winning_line(me.opponent) is not None]
        if blocks:
            return self.rng.choice(blocks)
        forks = [position for position in free if self._threat_count(board.with_mark(position, me), me) >= 2]
        if forks:
            return self.rng.choice(forks)
        builds = [position for position in free if self._threat_count(board.with_mark(position, me), me) >= 1]
        if builds:
            return self.rng.choice(builds)
        return self.rng.choice(free)

    def _threat_count(self, board: Board, player: Player) -> int:
        count = 0
        for first, second, third in WINNING_LINES:
            values = [
                board.player_at(Position.from_index(first)),
                board.player_at(Position.from_index(second)),
                board.player_at(Position.from_index(third)),
            ]
            if values.count(player) == 2 and values.count(None) == 1:
                count += 1
        return count
