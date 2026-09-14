from dataclasses import dataclass

from tictactoe.game import Game
from tictactoe.learning import Experience, ReinforcementLearner
from tictactoe.strategies import Strategy
from tictactoe.value_objects import O, X, Board, GameStatus, Player, Position


@dataclass(frozen=True, slots=True)
class TrainingSummary:
    wins: int
    draws: int
    losses: int


def _reward(player: Player, status: GameStatus) -> float:
    if status is GameStatus.DRAW:
        return 0.0
    winner = X if status is GameStatus.X_WON else O
    return 1.0 if player == winner else -1.0


class Trainer:
    def train(self, learner: ReinforcementLearner, seat: Player, opponent: Strategy, episodes: int) -> TrainingSummary:
        wins = 0
        draws = 0
        losses = 0
        for episode in range(episodes):
            game = Game.start(str(episode)).game
            moves: list[tuple[Board, Position]] = []
            while game.status is GameStatus.IN_PROGRESS:
                if game.current_player == seat:
                    action = learner.choose_position(game)
                    moves.append((game.board, action))
                else:
                    action = opponent.choose_position(game)
                game = game.place_mark(action).game
            for board, action in moves:
                learner.learn(Experience(board, seat, action, _reward(seat, game.status)))
            if _reward(seat, game.status) > 0.0:
                wins += 1
            elif _reward(seat, game.status) == 0.0:
                draws += 1
            else:
                losses += 1
        return TrainingSummary(wins, draws, losses)
