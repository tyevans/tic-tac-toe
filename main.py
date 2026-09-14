import random
import uuid

from tictactoe import (
    DomainEvent,
    FirstAvailableStrategy,
    GameEngine,
    GameStatus,
    MinimaxStrategy,
    NeuralPolicyLearner,
    O,
    PlaceMark,
    Player,
    PolicyLearner,
    Position,
    SimpleEventBus,
    StartGame,
    Strategy,
    ThreatBuilderStrategy,
    Trainer,
    X,
)

EPISODES = 6000


def print_event(event: DomainEvent) -> None:
    print(type(event).__name__)


def pick(agent: Strategy | PolicyLearner | NeuralPolicyLearner, game, explore: bool) -> Position:
    if isinstance(agent, (PolicyLearner, NeuralPolicyLearner)):
        return agent.choose_position(game, explore=explore)
    return agent.choose_position(game)


def run_match(
    engine: GameEngine,
    x: Strategy | PolicyLearner | NeuralPolicyLearner,
    o: Strategy | PolicyLearner | NeuralPolicyLearner,
    explore: bool = True,
) -> None:
    print(f"{type(x).__name__} (X) vs {type(o).__name__} (O)")
    agents: dict[Player, Strategy | PolicyLearner | NeuralPolicyLearner] = {X: x, O: o}
    game_id = str(uuid.uuid4())
    engine.start_game(StartGame(game_id))
    game = engine.get_game(game_id)
    while game.status is GameStatus.IN_PROGRESS:
        position = pick(agents[game.current_player], game, explore)
        game = engine.place_mark(PlaceMark(game_id, position))
        print(game.board.render())
        print()
    print(game.status)
    print()


def main() -> None:
    bus = SimpleEventBus()
    bus.subscribe(DomainEvent, print_event)
    engine = GameEngine(bus)

    run_match(engine, FirstAvailableStrategy(), MinimaxStrategy())
    run_match(engine, MinimaxStrategy(), MinimaxStrategy())

    print(f"Training tabular X and O PolicyLearners over {EPISODES} episodes each")
    x_learner = PolicyLearner(learning_rate=0.1, rng=random.Random(0))
    x_summary = Trainer().train(x_learner, X, FirstAvailableStrategy(), EPISODES)
    o_learner = PolicyLearner(learning_rate=0.1, rng=random.Random(1))
    o_summary = Trainer().train(o_learner, O, FirstAvailableStrategy(), EPISODES)
    print(f"tabular X vs naive: won {x_summary.wins}, drew {x_summary.draws}, lost {x_summary.losses}")
    print(f"tabular O vs naive: won {o_summary.wins}, drew {o_summary.draws}, lost {o_summary.losses}")
    print()

    run_match(engine, FirstAvailableStrategy(), o_learner, explore=False)
    run_match(engine, x_learner, o_learner, explore=False)

    print(f"Training deep X and O NeuralPolicyLearners against a threat-building opponent over {EPISODES} episodes each")
    x_net = NeuralPolicyLearner(learning_rate=0.1, rng=random.Random(0))
    x_net_summary = Trainer().train(x_net, X, ThreatBuilderStrategy(random.Random(7)), EPISODES)
    o_net = NeuralPolicyLearner(learning_rate=0.1, rng=random.Random(1))
    o_net_summary = Trainer().train(o_net, O, ThreatBuilderStrategy(random.Random(8)), EPISODES)
    print(f"deep X vs threat-builder: won {x_net_summary.wins}, drew {x_net_summary.draws}, lost {x_net_summary.losses}")
    print(f"deep O vs threat-builder: won {o_net_summary.wins}, drew {o_net_summary.draws}, lost {o_net_summary.losses}")
    print()

    run_match(engine, FirstAvailableStrategy(), o_net, explore=False)
    run_match(engine, x_net, o_net, explore=False)


if __name__ == "__main__":
    main()
