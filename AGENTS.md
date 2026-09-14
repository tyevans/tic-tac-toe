# AGENTS.md

## Project

Tic-tac-toe modeled with strong DDD: value objects, an aggregate root, domain events, domain commands, an event bus, and an application engine. Pure Python standard library, no third-party dependencies. Python >= 3.13, managed with `uv`.

## Layout

```
main.py                      demo entrypoint (only file outside the package that uses it)
src/tictactoe/
  value_objects.py           Player (+ X/O constants), Position, Cell, Board, GameStatus
  events.py                  DomainEvent base, GameStarted, MarkPlaced, GameWon, GameDrawn
  commands.py                Command base, StartGame, PlaceMark
  errors.py                  DomainError base and specific domain violations
  game.py                    Game aggregate root and Transition
  event_bus.py               EventBus protocol and SimpleEventBus
  engine.py                  GameEngine application service
  strategies.py              Strategy protocol, MinimaxStrategy, FirstAvailableStrategy, ThreatBuilderStrategy
  learning.py                Experience value object, ReinforcementLearner protocol, PolicyLearner (actor-critic)
  neural.py                  NeuralPolicyLearner: a hand-rolled pure-Python feedforward policy net (deep RL)
  trainer.py                 Trainer application service, TrainingSummary
  __init__.py                re-exports the public API
```

## Commands

- `uv sync` — install the package (editable) into `.venv`
- `uv run main.py` — run the demo (strategy matches, then trains and plays a tabular X/O policy learner against the naive strategy and a deep X/O policy learner against a threat-building opponent; prints events and boards)
- There is no test suite.

## Architecture rules

- `GameEngine` is the application service: it validates command preconditions (game exists / does not exist), asks the aggregate to apply the command, stores the resulting state, and publishes the transition's events on the bus.
- The `Game` aggregate is the only place game rules live. `place_mark` enforces "game not over" and "cell free", then returns a `Transition`: the next immutable `Game` plus the domain events that occurred.
- State flows one way: command -> engine -> aggregate -> `Transition` (new state + events) -> engine stores state -> bus publishes -> handlers react.
- The bus dispatches by type including subtypes: a handler subscribed to `DomainEvent` sees every event; a handler on `GameWon` sees only wins.
- `errors.py` takes only primitive parameters (no imports from other domain modules) to avoid import cycles. Keep it that way.

## Conventions

- Every domain object (value objects, events, commands, `Game`, `Transition`) is a frozen, slotted dataclass.
- Immutability is strict: any transformation (`Board.with_mark`, `Game.place_mark`) returns a new instance; nothing is mutated.
- Value objects validate their own invariants in `__post_init__` and raise the matching `DomainError` subclass.
- No comments and no docstrings anywhere. The code is the documentation.
- The package is dependency-free and contains no I/O. `main.py` is the only place that prints or uses `uuid`.
- New events, commands, or errors go in their existing modules (`events.py`, `commands.py`, `errors.py`), not in new files, and are re-exported from `__init__.py`.
- Player constants are module-level `X` and `O` in `value_objects.py`, not class attributes.
- `strategies.py` holds the `Strategy` protocol (a structural `typing.Protocol`, like `EventBus`) and concrete strategies, which are behavior classes — not frozen dataclasses. A strategy is player-agnostic: it plays for `game.current_player`, so one strategy can drive either side. `FirstAvailableStrategy` and `MinimaxStrategy` are stateless; `ThreatBuilderStrategy` is stateful (it holds an injected `random.Random`, like the learners) and plays a fast win → block → fork → build heuristic with randomized tie-breaks, so an RL learner trained against it faces diverse threats and learns to block rather than overfitting to one fixed opponent.
- `learning.py` holds the `ReinforcementLearner` protocol (structural, like `Strategy`) and `PolicyLearner`, a **stateful** behavior class (mutable policy weights and a per-state value map) — not a frozen dataclass, like the strategies. `Experience` is a frozen, slotted dataclass. The learner is player-relative: features and rewards are computed for the player to move, so one instance can serve either seat.
- `neural.py` holds `NeuralPolicyLearner`, a **stateful** behavior class (a hand-rolled feedforward net — mutable weight matrices — plus the same per-state value baseline as `PolicyLearner`) — not a frozen dataclass, like the learners. It implements the same `ReinforcementLearner` protocol, so it plugs into the `Trainer` unchanged. The net is a `9 → 16 (tanh) → 9` policy: cells are encoded relative to the player to move (+1/−1/0), occupied cells are masked before softmax, and it trains by policy gradient (`advantage · (one_hot(chosen) − π)`) backpropagated through the net. Pure-Python (`math` + injected `random`), no I/O.
- `trainer.py` holds the `Trainer` application service: `train(learner, seat, opponent, episodes)` plays full games where the learner drives one `seat` against a fixed `Strategy` opponent, records an `Experience` for each of the learner's moves, and returns a learner-relative `TrainingSummary(wins, draws, losses)`. It drives the `Game` aggregate directly (no engine, no bus, no `uuid`), so the "only main.py uses uuid" rule holds.
- Policy-gradient credit assignment uses a per-state value baseline (actor-critic): `learn` scores each move by `reward - V(board)` and updates `V` toward the terminal reward. This keeps updates low-variance; a plain reward (no baseline) makes the policy oscillate and unlearn.
- An RL learner only learns to block against opponents that actually build threats: trained against a naive (first-available) opponent, both the tabular and the deep learner overfit to it and never learn to block a two-in-a-row. Self-play does not fix this (the first-mover advantage dominates and the O-seat only ever draws or loses), and `MinimaxStrategy` is too slow in pure Python to use as a training opponent (seconds per move). The deep learners are therefore trained against `ThreatBuilderStrategy`, which forces blocking to be learned while staying fast and diverse.
