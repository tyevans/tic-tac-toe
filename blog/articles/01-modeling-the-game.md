# How We Model Tic-Tac-Toe: A Domain Model in Plain Python

## Who decides the next move?

Every article in this four-part series, *From Rules to Neurons*, answers the same question: **who decides the next move?** — and each one swaps in a smarter answer. This first one has the most boring answer on purpose: *nobody*. There is no player yet. There is just the game — the part that knows whose turn it is, which cells are free, and the moment it's over. Everything that plays it later (a hand-coded strategy, a learning table, a hand-rolled neural net) plugs into this game without touching its rules.

Think of it as the foundation of a house. Articles 2 through 4 are the floors above it; if the foundation is sloppy, the whole house leans. This article is the ground floor — a small domain model in plain Python that keeps the rules correct.

## The whole game is one small package

The entire *game* — the rules, not the players — is one small package of pure standard-library Python, no third-party dependencies:

```text
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

This article covers only the first seven files — the model itself. The files at the bottom (strategies, learners, a trainer) are the "brains" of the next three articles; they live in separate files on purpose, so the model never has to know they exist.

The last file is the door. `__init__.py` re-exports every public name, so `main.py` can import the whole system from the package root:

```python
from tictactoe.commands import Command, PlaceMark, StartGame
from tictactoe.engine import GameEngine
from tictactoe.event_bus import EventBus, EventHandler, SimpleEventBus
from tictactoe.events import DomainEvent, GameDrawn, GameStarted, GameWon, MarkPlaced
from tictactoe.game import Game, Transition
from tictactoe.value_objects import O, X, Board, Cell, GameStatus, Player, Position
```

(elided: the four lines that pull in the brains from the later articles.)

## The raw facts: value objects

Domain-Driven Design — DDD — is a name for a style of structuring code so the rules of your game live in one place and are hard to get wrong. Its smallest building block is a **value object**: *a piece of data that checks itself the moment it's created*. If the data is invalid, the object simply can't be built — it raises an error right at the door.

The analogy is an ID-card form that refuses to print if a required field is blank. Once the card is in your hand, the mistake is already impossible.

In this codebase, every domain object that stores data is a `@dataclass(frozen=True, slots=True)` — with one exception, `GameStatus`, a fixed list of named states we'll meet with `Game`. `frozen` means the fields can't change after creation; `slots` is a memory detail you can ignore. The self-check happens in `__post_init__`, a hook Python runs right after the fields are set. Here is `Player`:

```python
@dataclass(frozen=True, slots=True)
class Player:
    symbol: str

    def __post_init__(self) -> None:
        if self.symbol not in ("X", "O"):
            raise InvalidPlayerError(self.symbol)
```

A `Player` must prove its symbol is `"X"` or `"O"` at creation — `Player("Q")` raises `InvalidPlayerError` (a small `opponent` property is omitted). The two players that exist are module-level constants, which is why the code just writes `X` and `O`:

```python
X = Player("X")
O = Player("O")
```

Next, `Position` — a square on the board, as a row and a column. The board is 3×3 (`SIZE` is 3), so the check is a range check:

```python
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
```

`Position(5, 0)` is rejected at the door. The `index` property and the `from_index` method convert between a (row, column) pair and a flat 0–8 number.

`Cell` is the smallest fact of all: empty, or holding exactly one of the two players that made it through the door:

```python
@dataclass(frozen=True, slots=True)
class Cell:
    player: Player | None

    @property
    def display(self) -> str:
        return self.player.symbol if self.player is not None else " "
```

There is no way to put a `"Q"` in a cell, because there is no `Player("Q")`. Invalid data isn't just caught; it cannot exist.

Finally, the `Board` constructor: a board is exactly nine cells — nothing else can be built:

```python
@dataclass(frozen=True, slots=True)
class Board:
    cells: tuple[Cell, ...]

    def __post_init__(self) -> None:
        if len(self.cells) != SIZE * SIZE:
            raise InvalidBoardError()

    @classmethod
    def empty(cls) -> "Board":
        return cls(tuple(Cell(None) for _ in range(SIZE * SIZE)))
```

`Board.empty()` is how a fresh game gets its board. The board also has small readers — `cell_at`, `player_at`, and `is_occupied` — for the questions everything else asks of it.

One pattern before we move on: every rule violation gets its own error type. Each is a `DomainError` subclass, all living in one small `errors.py` that imports nothing from the rest of the domain. That's what lets the front desk reject a request later with a precise reason.

If the facts can't be bad, the rules have something safe to reason about. That is the first of the three jobs everything in this series has: keep the program *correct*, make it *playable*, and make it *improve*.

## A board that can't be in a bad state

A value object here is not inert data. It answers questions *and* enforces its own rules.

The analogy is a chess piece that cannot move onto an occupied square: the rule is built into the move itself, so you never have to remember to check it later.

The method that places a mark is `with_mark`:

```python
    def with_mark(self, position: Position, player: Player) -> "Board":
        if self.is_occupied(position):
            raise PositionOccupiedError(position.row, position.column)
        cells = list(self.cells)
        cells[position.index] = Cell(player)
        return Board(tuple(cells))
```

First, the guard: placing a mark on an occupied cell raises `PositionOccupiedError` — the rule is enforced inside the fact, not remembered by whoever calls it.

Second — the heart of this article — it does not edit the board. It copies the cells, swaps in one, and returns a **brand-new `Board`**, leaving the original untouched.

Win detection lives on the board, too. The eight winning lines are plain data:

```python
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
```

The query loops over them:

```python
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
```

Give it a player; it hands back the three winning positions, or `None`. And whether the board is full:

```python
    def is_full(self) -> bool:
        return all(cell.player is not None for cell in self.cells)
```

Why does it matter that win detection lives *on the facts*? Because none of the later brains re-implements the rules. Win checking, turn order, and occupancy all stay in this model; the brains just read it, at different depths. The unbeatable search leans hardest, calling `with_mark`, `winning_line`, and `is_full` to look ahead. The near-blind strategy only asks `is_occupied`. The two learners read the marks — one through the `player_at` and `is_occupied` queries, the other straight from the board's nine cells. Either way, the model does the work; the brains just ask it.

## The aggregate: the one place the rules live

The facts are safe. Now for the rules that change them.

In DDD, an **aggregate root** is the single object that owns a cluster of related state and is the *only door* into it. Think of it as the referee — the only person allowed to call the state of play. The demo's printer, the strategies, the learners: nobody changes the score on their own.

Our referee is `Game`:

```python
@dataclass(frozen=True, slots=True)
class Game:
    id: str
    board: Board
    current_player: Player
    status: GameStatus
```

Four facts: which game this is, the board, whose turn it is, and whether the game is still going. `GameStatus` is a plain enum — a fixed list of named choices, like the states of a traffic light — with four values: `IN_PROGRESS`, `X_WON`, `O_WON`, and `DRAW`.

Starting a game is a classmethod:

```python
    @classmethod
    def start(cls, game_id: str) -> "Transition":
        game = cls(
            id=game_id,
            board=Board.empty(),
            current_player=X,
            status=GameStatus.IN_PROGRESS,
        )
        return Transition(game, (GameStarted(game_id),))
```

X always starts. Note the return type: not a `Game`, but a `Transition` — *the next state* plus *the events that just happened*.

The core method, the only way a move gets applied, is `place_mark`. It's long, so we'll read it in three pieces. First, the two guards and the setup:

```python
    def place_mark(self, position: Position) -> "Transition":
        if self.status is not GameStatus.IN_PROGRESS:
            raise GameAlreadyOverError(self.id)
        if self.board.is_occupied(position):
            raise PositionOccupiedError(position.row, position.column)

        marked_board = self.board.with_mark(position, self.current_player)
        line = marked_board.winning_line(self.current_player)
```

Two guards come first: no moves in a finished game, no moves on an occupied cell. Then it builds the marked board and asks, "did that make a line?"

Every branch from here does the same three things: build a fresh `Game`, assemble its events, and hand back the pair. The win branch:

```python
        if line is not None:
            status = GameStatus.X_WON if self.current_player == X else GameStatus.O_WON
            game = Game(self.id, marked_board, self.current_player, status)
            events: tuple[DomainEvent, ...] = (
                MarkPlaced(self.id, self.current_player, position),
                GameWon(self.id, self.current_player, line),
            )
            return Transition(game, events)
```

A new `Game` with status `X_WON` or `O_WON`, and two events: `MarkPlaced` and `GameWon`. The draw branch has the same shape with a different second event; the continue branch is whatever's left:

```python
        if marked_board.is_full():
            game = Game(self.id, marked_board, self.current_player, GameStatus.DRAW)
            events = (
                MarkPlaced(self.id, self.current_player, position),
                GameDrawn(self.id),
            )
            return Transition(game, events)

        game = Game(self.id, marked_board, self.current_player.opponent, GameStatus.IN_PROGRESS)
        events = (MarkPlaced(self.id, self.current_player, position),)
        return Transition(game, events)
```

If the board is full: a `DRAW`, with `MarkPlaced` and `GameDrawn`. Otherwise the game continues: a fresh `Game` with `current_player` flipped to the opponent, and a single `MarkPlaced`.

In every case the old `Game` is untouched. The method hands back a **Transition** — a frozen pair of the next state and the events that occurred:

```python
@dataclass(frozen=True, slots=True)
class Transition:
    game: Game
    events: tuple[DomainEvent, ...]
```

"Rules in one place" is the core DDD promise, and it's kept here: because `place_mark` is the only door into the rules, a game cannot drift into an inconsistent state — no skipped turns, no missed wins.

## Immutability, gently: we produce the next version, never edit

Every transformation returns a *new* instance instead of editing the old one in place. The house rule: **we never mutate; we produce the next version.**

The analogy is a photo album. Every move is a fresh snapshot; you never pencil a mark onto an old photo. It's "Save As", not "Save".

The mechanism is the `frozen=True` you've seen on every domain object: fields become read-only after creation, so Python itself rejects any later assignment. Every "transformation" is phrased as "give me a version of myself with one thing changed" — `Board.with_mark` builds a fresh `cells` tuple and returns a new `Board`, and every branch of `place_mark` constructs a fresh `Game`.

Why bother? Three reasons.

1. **History is free.** A whole game can be a list of `Game` objects, every move a snapshot; nothing can retroactively change the past.
2. **Readers are safe.** Anyone can hold an old board or game and read it at any time; it cannot change out from under them.
3. **States can be keys.** Frozen objects get a Python "fingerprint" for free, which lets them be dictionary keys — and the learners in articles 3 and 4 use whole `Board`s as keys into a table of position values, a running guess at how good each position is.

The cost is a little allocation per move — for a game with nine cells, nothing.

One contrast for later: the engine and the bus we meet next are *not* frozen. The rule applies to the *domain* objects — facts and rules never change in place.

## Asking for changes: commands

The outside world cannot reach into a `Game` and poke it. It sends a **command** — a *request* for a change, not the change itself.

The analogy is a work-order form at a front desk: you fill out a form saying what you want, and the office decides whether and how to do it. It can even say no.

There are exactly two commands, and they're tiny:

```python
@dataclass(frozen=True, slots=True)
class Command:
    game_id: str


@dataclass(frozen=True, slots=True)
class StartGame(Command):
    pass


@dataclass(frozen=True, slots=True)
class PlaceMark(Command):
    position: Position
```

That is the entire body of `commands.py` (imports aside). `StartGame` adds nothing to the base; `PlaceMark` adds a `position`: "for game X, play this position". No turn logic, no win checking — it's a piece of paper.

Why separate the *request* from the *rule*? Because the front desk gets a single, checkable entry point. "Game not found" and "game already exists" are rejections of a *request*, not violations of the game.

## Reporting what happened: domain events

Commands go in; **events** come out. A **domain event** is a record of something that *already happened*. If a command is a request, an event is a receipt.

The analogy is a news ticker: "a mark was placed at (0,0)", "the game was won" — facts about the past that other parts of the program can react to, without the game knowing who's listening.

```python
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
```

`DomainEvent` is an empty base class, so that "some domain event" is a type you can subscribe to and dispatch on. The four concrete events carry exactly the facts of what happened.

Remember the win branch of `place_mark`? It emitted `MarkPlaced` and `GameWon` together — the only place events are *created*, inside the aggregate. Everything downstream merely reacts.

## The front desk and the announcement board

Now the two pieces that connect the outside world to the aggregate.

**`GameEngine`** is the front desk. In DDD vocabulary it's an *application service*: it doesn't own the rules, it orchestrates around them — check the request, ask the aggregate, store the result, and deal with the fallout.

```python
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

    def _require(self, game_id: str) -> Game:
        try:
            return self._games[game_id]
        except KeyError:
            raise GameNotFoundError(game_id) from None

    def _publish(self, events: Sequence[DomainEvent]) -> None:
        for event in events:
            self._event_bus.publish(event)
```

(There's also a one-line `get_game` getter.) The shape of `place_mark` is the whole pattern:

1. **Check preconditions.** `_require` raises `GameNotFoundError` for an unknown id, and `start_game` raises `GameAlreadyExistsError` on a duplicate — the request is rejected *before* it ever reaches the rules.
2. **Ask the aggregate.** `game.place_mark(command.position)` is where the rules run — and only there.
3. **Store the new state.** The `Transition`'s new `Game` replaces the old one in `self._games` — even the engine's storage honors the no-mutation rule.
4. **Publish the events.** `_publish` forwards each event on the bus.

**`SimpleEventBus`** is the announcement board — a public place where anyone pins a listener for the announcements they care about.

```python
class SimpleEventBus:
    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[EventHandler]] = {}

    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: DomainEvent) -> None:
        for event_type, handlers in self._handlers.items():
            if isinstance(event, event_type):
                for handler in handlers:
                    handler(event)
```

The interesting line is `if isinstance(event, event_type)`: dispatch is by type, **including subtypes**. A handler on `GameWon` sees only wins; a handler on the base `DomainEvent` sees *everything*. The engine never knows who is listening. That's the decoupling: *what changed* is separated from *what reacts to it*. (`EventHandler` is just a name for a function that takes one event, and `setdefault` pulls out the list for a type or starts an empty one.)

There's also an `EventBus` contract — two methods, `subscribe` and `publish` — and any object with those two methods works as a bus.

## The one-way flow, shown in the demo

Every change travels exactly one path, in one direction:

**command → engine → aggregate → Transition (new state + events) → engine stores state → bus publishes → handlers react**

The analogy is a conveyor belt that only moves one way: nothing reaches back. A handler can read an event, but it cannot edit a game or stop the belt.

The demo entry point, `main.py`, wires it up in three lines:

```python
    bus = SimpleEventBus()
    bus.subscribe(DomainEvent, print_event)
    engine = GameEngine(bus)
```

`print_event` is a catch-all handler:

```python
def print_event(event: DomainEvent) -> None:
    print(type(event).__name__)
```

Subscribed to the base `DomainEvent`, and because dispatch includes subtypes, it sees all four kinds of event.

The match loop also prints the board after every move, built by `Board.render` — the most readable code in the package:

```python
    def render(self) -> str:
        rows = []
        for row in range(SIZE):
            marks = [self.cell_at(Position(row, column)).display for column in range(SIZE)]
            rows.append(f" {marks[0]} | {marks[1]} | {marks[2]} ")
        return "\n---+---+---\n".join(rows)
```

Three lines of text joined with a separator — the familiar box.

Two names before the loop: `agents` maps each player to its "brain" — whatever object sits in that seat — and `explore` is a knob the later learners use to choose between a random move and their best one (the hand-written strategies ignore it). `pick` hands the game to the brain to move:

```python
    while game.status is GameStatus.IN_PROGRESS:
        position = pick(agents[game.current_player], game, explore)
        game = engine.place_mark(PlaceMark(game_id, position))
        print(game.board.render())
        print()
```

That `pick(...)` line is the whole question of this series — *who decides the next move?* — sitting in an empty seat that the next article fills. (The final `print()` leaves the blank line between boards.)

Here is a real run — the first match of the demo, trimmed to the first two moves and the ending (the trailing whitespace `render` leaves at each line's end is removed):

```text
FirstAvailableStrategy (X) vs MinimaxStrategy (O)
GameStarted
MarkPlaced
 X |   |
---+---+---
   |   |
---+---+---
   |   |

MarkPlaced
 X |   |
---+---+---
   | O |
---+---+---
   |   |

... three more moves ...

MarkPlaced
GameWon
 X | X | O
---+---+---
 X | O |
---+---+---
 O |   |

GameStatus.O_WON
```

Trace one move through the belt. The command arrives at the front desk, which checks the game exists, then asks the aggregate: `Game.place_mark` enforces the guards, builds the new board, checks for a line, and returns a `Transition`. The engine stores it; the bus publishes; the handler prints `MarkPlaced` — which is why the event name and the fresh board appear together.

On the final move the belt carries *two* events — `MarkPlaced` then `GameWon` — which is why those names appear back to back: O's diagonal completed the game, and the model reported both facts.

You can run it yourself with `uv run main.py`. The demo does more, but this first match is the ground floor working end to end: every board is a `Transition`'s new state, and every event name was published on the bus.

## Who decides the next move? (Not yet)

Look back at that match loop one last time. The model knows everything — whose turn it is, which cells are free, who won — and it still never picks a single cell. That `pick(...)` line is the empty seat this whole series keeps circling, and the first of the three jobs — *correct* — is done. In the next article we finally put something in it: two hand-written "brains", one that plays almost blindly and one that is mathematically unbeatable — and we'll see exactly what each one costs.
