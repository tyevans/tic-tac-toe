# Episode 2: How a Move Happens

## 1. Header

- **Title:** How a Move Happens
- **Number:** 2 of 6
- **Target length:** 10 minutes 20 seconds (620 seconds, 13 scenes)
- **Source files:**
  - `src/tictactoe/commands.py`
  - `src/tictactoe/events.py`
  - `src/tictactoe/errors.py`
  - `src/tictactoe/game.py` (the guards in `place_mark` only)
  - `src/tictactoe/engine.py`
  - `src/tictactoe/event_bus.py`
  - `main.py` (`print_event`, the three wiring lines in `main`, the loop in `run_match`)
- **Source article sections:** `blog/articles/01-modeling-the-game.md`, from "Asking for changes: commands" to the end:
  - "Asking for changes: commands"
  - "Reporting what happened: domain events"
  - "The front desk and the announcement board"
  - "The one-way flow, shown in the demo"
  - "Who decides the next move? (Not yet)"
- **Real demo output:** the first match of `uv run main.py`, `FirstAvailableStrategy` (X) against `MinimaxStrategy` (O).

## 2. Goal

After the video, the viewer can explain how one move goes through the program. The viewer can tell the difference between a command (a request that the program can refuse) and a domain event (a fact about the past). The viewer can name the four steps of the `GameEngine`: find the game, ask the aggregate, store the new state, publish the events. The viewer can explain why a handler on `DomainEvent` gets every event and a handler on `GameWon` gets only wins. The viewer can say what happens when the program refuses a move: an error, no new state, no event.

## 3. Recap from the last video

Scene `E2S1` has the recap. The recap narration is 20 seconds or less. It names: value objects that check their own rules, the `Board` invariants, the `Game` aggregate, the `Transition`, and immutability.

## 4. Terms

- **Command.** A frozen object that asks for a change. The program can refuse it. The project has two commands: `StartGame` and `PlaceMark`.
- **Domain event.** A frozen object that records a fact that already happened. Its name is in the past tense. The project has four domain events: `GameStarted`, `MarkPlaced`, `GameWon`, `GameDrawn`. In the narration, "event" always means "domain event".
- **Domain error.** An exception of a subclass of `DomainError`. The code raises it when it refuses a command.
- **`GameEngine`.** The application service. It is the "front desk": it finds the game, asks the aggregate, stores the new state, and publishes the events.
- **Application service.** An object that does the steps around the rules. It does not hold the game rules.
- **Event bus.** The "announcement board". Handlers subscribe to an event type. The bus publishes each event to the handlers that match.
- **`EventBus`.** A `typing.Protocol` with two methods: `subscribe` and `publish`. Any object with the two methods can be the event bus.
- **`SimpleEventBus`.** The one event bus in the project. It keeps a dictionary from event type to a list of handlers.
- **Handler.** A function that takes one event and returns nothing. The code calls this type `EventHandler`.
- **Subscribe.** Add a handler for one event type.
- **Publish.** Give one event to every handler whose event type matches.
- **Dispatch by type, including subtypes.** The bus uses `isinstance`. A handler on a base class also gets the events of all its subclasses.
- **One-way flow.** The path of every change: command → engine → aggregate → `Transition` → engine stores state → bus publishes → handlers react.

## 5. Source facts

### 5.1 Code snippets

Copy these snippets exactly. The scenes repeat each snippet that they use. Keep the leading spaces.

**SF1. `src/tictactoe/commands.py` (all classes)**

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

**SF2. `src/tictactoe/events.py` (part A)**

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
```

**SF3. `src/tictactoe/events.py` (part B)**

```python
@dataclass(frozen=True, slots=True)
class GameWon(DomainEvent):
    game_id: str
    winner: Player
    winning_line: tuple[Position, Position, Position]


@dataclass(frozen=True, slots=True)
class GameDrawn(DomainEvent):
    game_id: str
```

**SF4. `src/tictactoe/game.py` (the guards in `place_mark`)**

```python
    def place_mark(self, position: Position) -> "Transition":
        if self.status is not GameStatus.IN_PROGRESS:
            raise GameAlreadyOverError(self.id)
        if self.board.is_occupied(position):
            raise PositionOccupiedError(position.row, position.column)
```

**SF5. `src/tictactoe/engine.py` (constructor and `start_game`)**

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
```

**SF6. `src/tictactoe/engine.py` (`place_mark`)**

```python
    def place_mark(self, command: PlaceMark) -> Game:
        game = self._require(command.game_id)
        transition = game.place_mark(command.position)
        self._games[command.game_id] = transition.game
        self._publish(transition.events)
        return transition.game
```

**SF7. `src/tictactoe/engine.py` (`_require` and `_publish`)**

```python
    def _require(self, game_id: str) -> Game:
        try:
            return self._games[game_id]
        except KeyError:
            raise GameNotFoundError(game_id) from None

    def _publish(self, events: Sequence[DomainEvent]) -> None:
        for event in events:
            self._event_bus.publish(event)
```

**SF8. `src/tictactoe/event_bus.py` (the protocol)**

```python
EventHandler = Callable[[DomainEvent], None]


class EventBus(Protocol):
    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        ...

    def publish(self, event: DomainEvent) -> None:
        ...
```

**SF9. `src/tictactoe/event_bus.py` (`SimpleEventBus`)**

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

**SF10. `main.py` (wiring in `main`)**

```python
    bus = SimpleEventBus()
    bus.subscribe(DomainEvent, print_event)
    engine = GameEngine(bus)
```

**SF11. `main.py` (`print_event`)**

```python
def print_event(event: DomainEvent) -> None:
    print(type(event).__name__)
```

**SF12. `main.py` (the loop in `run_match`)**

```python
    while game.status is GameStatus.IN_PROGRESS:
        position = pick(agents[game.current_player], game, explore)
        game = engine.place_mark(PlaceMark(game_id, position))
        print(game.board.render())
        print()
```

### 5.2 The domain errors in this video

All four classes are in `src/tictactoe/errors.py`. All four are subclasses of `DomainError`. The message text is exact.

| Error class | Raised by | When | Message |
|-------------|-----------|------|---------|
| `GameAlreadyExistsError` | `GameEngine.start_game` | a game with the ID is already stored | `game <id> already exists` |
| `GameNotFoundError` | `GameEngine._require` (used by `place_mark` and `get_game`) | no game has the ID | `game <id> not found` |
| `GameAlreadyOverError` | `Game.place_mark` | the status is not `IN_PROGRESS` | `game <id> is already over` |
| `PositionOccupiedError` | `Game.place_mark` (also `Board.with_mark`) | the cell has a mark | `cell (<row>, <column>) is already occupied` |

`errors.py` has three more errors (`InvalidPositionError`, `InvalidPlayerError`, `InvalidBoardError`). The value objects raise them. This video does not show them.

### 5.3 The real game (first match of `uv run main.py`)

Header line: `FirstAvailableStrategy (X) vs MinimaxStrategy (O)`.

Cell index = row × 3 + column. Index 0 is top left. Index 8 is bottom right.

| Step | Command | Player | Position (row, column) | Cell index | Events published, in order |
|------|---------|--------|------------------------|------------|---------------------------|
| 0 | `StartGame` | none | none | none | `GameStarted` |
| 1 | `PlaceMark` | X | (0, 0) | 0 | `MarkPlaced` |
| 2 | `PlaceMark` | O | (1, 1) | 4 | `MarkPlaced` |
| 3 | `PlaceMark` | X | (0, 1) | 1 | `MarkPlaced` |
| 4 | `PlaceMark` | O | (0, 2) | 2 | `MarkPlaced` |
| 5 | `PlaceMark` | X | (1, 0) | 3 | `MarkPlaced` |
| 6 | `PlaceMark` | O | (2, 0) | 6 | `MarkPlaced`, then `GameWon` |

- `GameWon.winner` is O. `GameWon.winning_line` is `(Position(row=0, column=2), Position(row=1, column=1), Position(row=2, column=0))`, cells 2, 4, 6, in that order.
- The last line that the match prints is `GameStatus.O_WON`.
- 8 events in total: 1 `GameStarted`, 6 `MarkPlaced`, 1 `GameWon`.
- The demo prints each event name before the board of that move. The reason: `engine.place_mark` publishes the events before it returns, and the loop prints the board after it returns.
- The final board, exactly as printed (trailing spaces removed):

```text
 X | X | O
---+---+---
 X | O |
---+---+---
 O |   |
```

- `main.py` uses `str(uuid.uuid4())` for the game ID. The cards in this video show `game_id: "game-1"` as a short label.

### 5.4 The refused move (not in the demo)

This command does not occur in `main.py`. The author checked it with a small script:

- Start game `game-1`. Place X at (0, 0). Place O at (1, 1). Now it is the turn of X.
- Send `PlaceMark("game-1", Position(1, 1))`.
- Result: `PositionOccupiedError`, message `cell (1, 1) is already occupied`.
- After the error: the bus published 0 events. The stored game did not change. `current_player` is still X. `status` is still `GameStatus.IN_PROGRESS`.
- `GameEngine` does not catch the error. The error goes to the code that sent the command.

## 6. Scenes

Scene durations: E2S1 25 s, E2S2 50 s, E2S3 50 s, E2S4 45 s, E2S5 60 s, E2S6 45 s, E2S7 45 s, E2S8 85 s, E2S9 40 s, E2S10 60 s, E2S11 45 s, E2S12 45 s, E2S13 25 s. Total 620 s. The word counts assume about 130 to 135 spoken words per minute, plus short holds for the animations.

### Rules for all scenes in this episode

The production LLM gets one scene section at a time. Thus each scene repeats the rules that it needs. These rules apply to every scene:

- Frame coordinates: x from −7.1 (left) to 7.1 (right), y from −4 (bottom) to 4 (top).
- Background `BG_COLOR`. Labels in `TEXT_COLOR`. Secondary labels in `MUTED_COLOR`.
- **Command card:** use `make_command_card`. A rounded rectangle (corner radius 0.15), stroke `COMMAND_COLOR`, stroke width 3, fill `COMMAND_COLOR` at opacity 0.15. The class name in bold `TEXT_COLOR`, font size 30, at the top. Each field on its own line below, font size 22, `TEXT_COLOR`.
- **Event card:** use `make_event_card`. The same shape, with `EVENT_COLOR` in place of `COMMAND_COLOR`.
- **Station box:** a rounded rectangle (corner radius 0.15), stroke `TEXT_COLOR`, stroke width 3, no fill, with a label in `TEXT_COLOR`, font size 28, at the center. The `Game` station box uses stroke `RULE_COLOR`, because the rules live there.
- **Code panel:** use `make_code_panel(code_string)`. Put the center at (3.6, −0.3). Scale it so that its width is 6.6 or less and its height is 6.4 or less. To mark one code line, draw a rectangle with stroke `TEXT_COLOR`, stroke width 2, no fill, around that line. Line numbers in this file start at 1 at the first line of the snippet. In Manim CE 0.19 the lines of a `Code` object are in `code.code_lines`. Check the attribute name in the installed version before use.
- Narration text: speak class names as one word, as written ("PlaceMark", "GameEngine"). Do not add backticks to the narration.

---

### E2S1: Recap and title

- **Scene ID:** `E2S1`
- **Manim class name:** `E2S1RecapTitle`
- **Target duration:** 25 seconds (about 55 words; the recap blocks 1 and 2 are about 42 words, 20 seconds or less)

#### Narration

Block 1:

> <bookmark mark='board'/>Last time, we built the parts of the game. Value objects check their own rules. A Board cannot hold a bad state.

Block 2:

> <bookmark mark='game'/>The Game aggregate holds the game rules. <bookmark mark='transition'/>Each move gives a Transition: a new game and its events. Nothing changes in place.

Block 3:

> <bookmark mark='title'/>Today, we follow one move from the request to the printed result.

#### Visuals

- Left: an empty board from `make_board()`, center (−3.5, 0), with cell indices 0 to 8 in `MUTED_COLOR`.
- Right: a station box labeled `Game`, stroke `RULE_COLOR`, width 3.0, height 1.2, center (3.0, 1.5).
- Right, below: a box labeled `Transition`, stroke `TEXT_COLOR`, width 4.4, height 2.2, center (3.0, −1.5). Inside, on its left: a small board (scale 0.35) with an X in cell 0. Inside, on its right: a small event card `MarkPlaced` (title only, scale 0.6).
- Title card: text `How a Move Happens`, font size 64, `TEXT_COLOR`, center (0, 0.4). Subtitle `Episode 2`, font size 32, `MUTED_COLOR`, at (0, −0.5).

#### Animation steps

1. `board`: Create the board on the left (Create, 1 s). Then flash the outline of the board in `RULE_COLOR` one time (Indicate with color `RULE_COLOR`).
2. `game`: FadeIn the `Game` station box.
3. `transition`: Draw an arrow in `TEXT_COLOR` from the bottom of the `Game` box to the top of the `Transition` box. FadeIn the `Transition` box with the small board and the small `MarkPlaced` event card.
4. `title`: FadeOut all objects. Write the title and the subtitle. Wait 1 second at the end.

#### Accuracy notes

- `Game.place_mark` and `Game.start` return a `Transition`, not a `Game`.
- A `Transition` holds `game` (the next `Game`) and `events` (a tuple of domain events).
- All domain objects are frozen dataclasses. Nothing changes in place.

---

### E2S2: Commands

- **Scene ID:** `E2S2`
- **Manim class name:** `E2S2Commands`
- **Target duration:** 50 seconds (about 105 words)

#### Narration

Block 1:

> <bookmark mark='request'/>Code outside the game cannot change a Game directly. It sends a command. A command is a request for a change. It is not the change.

Block 2:

> <bookmark mark='desk'/>Think of a form that you give to a front desk. The desk reads the form. The desk can do the work, or it can refuse.

Block 3:

> <bookmark mark='code'/>The project has two commands. Both get a game ID from the base class, Command. <bookmark mark='start'/>StartGame adds nothing more. <bookmark mark='place'/>PlaceMark adds a position: a row and a column.

Block 4:

> <bookmark mark='paper'/>A command holds no rules. It does not know whose turn it is. It does not know if the cell is free. It is only a form.

#### Visuals

- Left: a command card `PlaceMark` with fields `game_id: "game-1"` and `position: (1, 1)`. Width 3.6, height 1.6, center (−3.5, 1.2).
- Left: a station box labeled `front desk`, width 3.0, height 1.2, center (−3.5, −1.6).
- Right: code panel with snippet SF1.

Code panel string (SF1, `src/tictactoe/commands.py`):

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

#### Animation steps

1. `request`: FadeIn the `PlaceMark` command card at (−3.5, 1.2).
2. `desk`: FadeIn the `front desk` box. Move the command card down until its bottom edge is 0.1 above the top edge of the box (1 s). Then show two small labels below the box: `✓ do the work` in `TEXT_COLOR` at (−4.6, −2.8) and `✗ refuse` in `ERROR_COLOR` at (−2.4, −2.8), font size 24.
3. `code`: FadeIn the code panel on the right. Mark lines 1 to 3 (`Command`).
4. `start`: Move the line mark to lines 6 to 8 (`StartGame`).
5. `place`: Move the line mark to lines 11 to 13 (`PlaceMark`). Indicate the `position` field on the command card.
6. `paper`: Remove the line mark. On the left, FadeOut the two labels below the box. Show the text `no rules inside` in `MUTED_COLOR`, font size 26, below the box at (−3.5, −2.8).

#### Accuracy notes

- There are exactly two commands: `StartGame` and `PlaceMark`. Both are subclasses of `Command`.
- `Command` has one field: `game_id: str`. `StartGame` adds no field. `PlaceMark` adds `position: Position`.
- All three classes are `@dataclass(frozen=True, slots=True)`.
- `Position` has `row` and `column`, each from 0 to 2.
- The code panel shows no imports. Do not add them.

---

### E2S3: Domain events

- **Scene ID:** `E2S3`
- **Manim class name:** `E2S3DomainEvents`
- **Target duration:** 50 seconds (about 105 words)

#### Narration

Block 1:

> <bookmark mark='intro'/>Commands go in. Domain events come out. A domain event is a fact about something that already happened. Its name is in the past tense.

Block 2:

> <bookmark mark='compare'/>A command says: please place a mark. An event says: a mark was placed. The program can refuse a request. A fact does not change.

Block 3:

> <bookmark mark='code_a'/>DomainEvent is an empty base class. GameStarted records the game ID. <bookmark mark='markplaced'/>MarkPlaced records the game ID, the player, and the position.

Block 4:

> <bookmark mark='code_b'/>GameWon records the winner and the three positions of the winning line. GameDrawn records only the game ID.

Block 5:

> <bookmark mark='source'/>Only the Game aggregate makes events. On a winning move, it makes two events: MarkPlaced, then GameWon.

#### Visuals

- Left, top: a command card `PlaceMark` (fields `game_id: "game-1"`, `position: (0, 0)`), width 3.6, height 1.4, center (−3.5, 2.0). Label above it: `request` in `MUTED_COLOR`, font size 24.
- Left, middle: an event card `MarkPlaced` (fields `game_id: "game-1"`, `player: X`, `position: (0, 0)`), width 3.6, height 1.8, center (−3.5, −0.6). Label above it: `fact` in `MUTED_COLOR`, font size 24.
- Left, bottom (step `source`): a station box `Game`, stroke `RULE_COLOR`, width 2.4, height 1.0, center (−5.2, −3.0). Two small event cards, title only, width 2.0, height 0.6: `MarkPlaced` at (−2.6, −2.6) and `GameWon` at (−2.6, −3.4).
- Right: code panel. First snippet SF2, then snippet SF3.

Code panel string A (SF2, `src/tictactoe/events.py`):

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
```

Code panel string B (SF3, `src/tictactoe/events.py`):

```python
@dataclass(frozen=True, slots=True)
class GameWon(DomainEvent):
    game_id: str
    winner: Player
    winning_line: tuple[Position, Position, Position]


@dataclass(frozen=True, slots=True)
class GameDrawn(DomainEvent):
    game_id: str
```

#### Animation steps

1. `intro`: FadeIn the command card and its label. Draw an arrow in `TEXT_COLOR` down from the command card to the event card position. FadeIn the event card and its label.
2. `compare`: Indicate the command card (1 s). Then Indicate the event card (1 s).
3. `code_a`: FadeIn code panel A on the right. Mark lines 1 to 3, then (after 2 s) lines 6 to 8.
4. `markplaced`: Move the line mark to lines 11 to 15. Indicate the three fields on the `MarkPlaced` event card.
5. `code_b`: Transform code panel A into code panel B. Mark lines 1 to 5, then (after 2.5 s) lines 8 to 10.
6. `source`: Remove the line mark. FadeOut the command card, the arrow, and the labels. Move the big event card up to (−3.5, 1.5). FadeIn the `Game` station box. Draw a `TEXT_COLOR` arrow from the box to the small `MarkPlaced` card, then a second arrow to the small `GameWon` card, 0.5 s apart.

#### Accuracy notes

- There are exactly four concrete events: `GameStarted`, `MarkPlaced`, `GameWon`, `GameDrawn`. All four are subclasses of `DomainEvent`.
- `DomainEvent` has no fields.
- `GameStarted` and `GameDrawn` have only `game_id`. `MarkPlaced` has `game_id`, `player`, `position`. `GameWon` has `game_id`, `winner`, `winning_line`.
- `winning_line` is a tuple of exactly three `Position` objects.
- Events are made only in `game.py` (`Game.start` and `Game.place_mark`). The engine and the bus do not make events.
- On a winning move, the order is `MarkPlaced`, then `GameWon`. On a drawing move, the order is `MarkPlaced`, then `GameDrawn`.

---

### E2S4: Domain errors

- **Scene ID:** `E2S4`
- **Manim class name:** `E2S4DomainErrors`
- **Target duration:** 45 seconds (about 100 words)

#### Narration

Block 1:

> <bookmark mark='intro'/>Sometimes the answer is no. Then the code raises a domain error. Each error in this video is a subclass of DomainError.

Block 2:

> <bookmark mark='engine_errors'/>The engine checks the game ID. GameAlreadyExistsError means that a game with that ID exists. GameNotFoundError means that no game has that ID.

Block 3:

> <bookmark mark='game_errors'/>The Game aggregate checks the game rules. GameAlreadyOverError means that the game is over. PositionOccupiedError means that the cell already has a mark.

Block 4:

> <bookmark mark='guards'/>Here are the two guards in place_mark. They run before the aggregate makes a new board. <bookmark mark='nothing'/>When a guard raises an error, there is no new game and no event.

#### Visuals

- Left, top: a heading `DomainError` in `ERROR_COLOR`, font size 34, at (−3.5, 3.0).
- Left: two group labels and four error names. Error names in `ERROR_COLOR`, font size 26. Group labels in `MUTED_COLOR`, font size 24.
  - Group label `GameEngine checks` at (−3.5, 2.1).
  - `GameAlreadyExistsError` at (−3.5, 1.5).
  - `GameNotFoundError` at (−3.5, 0.9).
  - Group label `Game checks` in `RULE_COLOR` at (−3.5, −0.2). (The aggregate checks the rules, so this label uses `RULE_COLOR`.)
  - `GameAlreadyOverError` at (−3.5, −0.8).
  - `PositionOccupiedError` at (−3.5, −1.4).
- Left, bottom (step `nothing`): the text `no new game` and `no event`, each with a red cross `✗` before it, `ERROR_COLOR`, font size 26, at (−3.5, −2.6) and (−3.5, −3.2).
- Right: code panel with snippet SF4 (step `guards`).

Code panel string (SF4, `src/tictactoe/game.py`):

```python
    def place_mark(self, position: Position) -> "Transition":
        if self.status is not GameStatus.IN_PROGRESS:
            raise GameAlreadyOverError(self.id)
        if self.board.is_occupied(position):
            raise PositionOccupiedError(position.row, position.column)
```

#### Animation steps

1. `intro`: Write the heading `DomainError`.
2. `engine_errors`: FadeIn the label `GameEngine checks`. Then FadeIn `GameAlreadyExistsError`, and after 2.5 s FadeIn `GameNotFoundError`.
3. `game_errors`: FadeIn the label `Game checks`. Then FadeIn `GameAlreadyOverError`, and after 2 s FadeIn `PositionOccupiedError`.
4. `guards`: FadeIn the code panel on the right. Mark lines 2 to 3. After 2 s, move the mark to lines 4 to 5. Draw a thin `ERROR_COLOR` line from `GameAlreadyOverError` on the left to line 3 of the code, and one from `PositionOccupiedError` to line 5.
5. `nothing`: FadeOut the two connecting lines. FadeIn `✗ no new game` and `✗ no event`.

#### Accuracy notes

- The engine raises `GameAlreadyExistsError` (in `start_game`) and `GameNotFoundError` (in `_require`).
- The aggregate `Game.place_mark` raises `GameAlreadyOverError` and `PositionOccupiedError`.
- The first guard checks the status. The second guard checks the cell. The order is fixed.
- `errors.py` also has `InvalidPositionError`, `InvalidPlayerError`, and `InvalidBoardError`. Do not show them in this scene.
- The narration "a game with that ID exists" means "is already stored in the engine".

---

### E2S5: The GameEngine, the front desk

- **Scene ID:** `E2S5`
- **Manim class name:** `E2S5GameEngine`
- **Target duration:** 60 seconds (about 130 words)

#### Narration

Block 1:

> <bookmark mark='intro'/>The GameEngine is the front desk. It does not hold the game rules. It takes a command and does the steps around the rules.

Block 2:

> <bookmark mark='init'/>The engine keeps a reference to an event bus. It also keeps a dictionary of games, with one entry for each game ID.

Block 3:

> <bookmark mark='start'/>start_game first checks that the ID is new. Then it asks Game.start for a Transition. It stores the new game and publishes the events.

Block 4:

> <bookmark mark='place'/>place_mark has the same shape. <bookmark mark='step1'/>Step one: find the game, or refuse. <bookmark mark='step2'/>Step two: ask the aggregate to place the mark. <bookmark mark='step3'/>Step three: store the new game in place of the old game. <bookmark mark='step4'/>Step four: publish the events.

Block 5:

> <bookmark mark='helpers'/>The require helper raises GameNotFoundError for an unknown ID. The publish helper gives each event to the bus, one at a time.

#### Visuals

- Left, top: a station box `GameEngine`, width 3.4, height 1.0, center (−3.5, 3.0).
- Left, below it: a dictionary picture labeled `_games` in `MUTED_COLOR`, font size 24, at (−3.5, 2.0). Below the label, one row: the text `"game-1"` in `TEXT_COLOR` (font size 24) at (−4.6, 1.4), an arrow in `MUTED_COLOR`, and a small board (scale 0.3) at (−2.6, 1.4).
- Left, lower: a numbered list of four steps, font size 28, `TEXT_COLOR`, left-aligned at x = −6.6:
  - `1. find the game` at y = 0.2
  - `2. ask the aggregate` at y = −0.6
  - `3. store the new game` at y = −1.4
  - `4. publish the events` at y = −2.2
  - To the right of step 1, a small `✗ refuse` in `ERROR_COLOR`, font size 22, at (−1.3, 0.2).
  - The word `aggregate` in step 2 uses `RULE_COLOR`.
- Right: code panel. First SF5, then SF6, then SF7.

Code panel string A (SF5, `src/tictactoe/engine.py`):

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
```

Code panel string B (SF6, `src/tictactoe/engine.py`):

```python
    def place_mark(self, command: PlaceMark) -> Game:
        game = self._require(command.game_id)
        transition = game.place_mark(command.position)
        self._games[command.game_id] = transition.game
        self._publish(transition.events)
        return transition.game
```

Code panel string C (SF7, `src/tictactoe/engine.py`):

```python
    def _require(self, game_id: str) -> Game:
        try:
            return self._games[game_id]
        except KeyError:
            raise GameNotFoundError(game_id) from None

    def _publish(self, events: Sequence[DomainEvent]) -> None:
        for event in events:
            self._event_bus.publish(event)
```

#### Animation steps

1. `intro`: FadeIn the `GameEngine` station box on the left.
2. `init`: FadeIn code panel A on the right. Mark lines 2 to 4. FadeIn the `_games` label and the dictionary row on the left.
3. `start`: Mark lines 7 to 8. After 2 s, mark line 9. After 2 s, mark lines 10 to 11.
4. `place`: Transform code panel A into code panel B. Remove the line mark.
5. `step1`: Mark line 2. FadeIn step `1. find the game` and the `✗ refuse` label.
6. `step2`: Mark line 3. FadeIn step `2. ask the aggregate`.
7. `step3`: Mark line 4. FadeIn step `3. store the new game`. On the dictionary row, replace the small board with a new small board that has an X in cell 0 (FadeOut old, FadeIn new, 0.5 s).
8. `step4`: Mark line 5. FadeIn step `4. publish the events`.
9. `helpers`: Transform code panel B into code panel C. Mark lines 1 to 5. After 3 s, mark lines 7 to 9.

#### Accuracy notes

- `GameEngine` stores games in `self._games`, a `dict[str, Game]` from game ID to `Game`.
- `start_game` raises `GameAlreadyExistsError` if the ID is in `self._games`. It does not call `_require`.
- `place_mark` calls `_require` first. `_require` raises `GameNotFoundError` for an unknown ID.
- Step 3 replaces the dictionary entry with the new `Game`. The old `Game` object does not change.
- `_publish` calls `self._event_bus.publish(event)` one time for each event, in order.
- Both methods return `transition.game`.
- The engine also has a one-line `get_game` method. It calls `_require`. This scene does not show it.
- The narration says "require helper" and "publish helper" for `_require` and `_publish`, so that the voice can read them.

---

### E2S6: The event bus, the announcement board

- **Scene ID:** `E2S6`
- **Manim class name:** `E2S6EventBus`
- **Target duration:** 45 seconds (about 95 words)

#### Narration

Block 1:

> <bookmark mark='intro'/>The event bus is an announcement board. A handler subscribes to one type of event. When an event arrives, the bus calls each handler that matches.

Block 2:

> <bookmark mark='protocol'/>EventBus is a protocol with two methods: subscribe and publish. Any object with these two methods can be the event bus. <bookmark mark='handler'/>An EventHandler is a function that takes one event.

Block 3:

> <bookmark mark='simple'/>SimpleEventBus keeps a dictionary. Each key is an event type. Each value is a list of handlers.

Block 4:

> <bookmark mark='subscribe'/>subscribe adds a handler to the list for its event type. <bookmark mark='decouple'/>The engine does not know who listens. It only publishes.

#### Visuals

- Left: an "announcement board": a rectangle, width 5.6, height 4.4, center (−3.6, 0.2), stroke `TEXT_COLOR`, fill `TEXT_COLOR` at opacity 0.05. Title `SimpleEventBus` above it, font size 30, at (−3.6, 2.8).
- Inside the board, two rows (step `simple`). Each row is a key box and a list of handler chips.
  - Row 1 at y = 1.0: key text `DomainEvent` in `EVENT_COLOR`, font size 24, at (−5.0, 1.0). An arrow in `MUTED_COLOR`. A handler chip at (−2.3, 1.0): a small rounded rectangle, stroke `TEXT_COLOR`, label `print_event`, font size 22.
  - Row 2 at y = −0.4: key text `GameWon` in `EVENT_COLOR`, font size 24, at (−5.0, −0.4). An arrow in `MUTED_COLOR`. A handler chip at (−2.3, −0.4) labeled `handler`.
- Left, below the board (step `decouple`): a station box `GameEngine`, width 2.8, height 0.9, center (−3.6, −3.1). A `TEXT_COLOR` arrow from its top to the bottom of the board. A label `publish(event)` in `MUTED_COLOR`, font size 22, to the right of the arrow.
- Right: code panel. First SF8, then SF9.

Code panel string A (SF8, `src/tictactoe/event_bus.py`):

```python
EventHandler = Callable[[DomainEvent], None]


class EventBus(Protocol):
    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        ...

    def publish(self, event: DomainEvent) -> None:
        ...
```

Code panel string B (SF9, `src/tictactoe/event_bus.py`):

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

#### Animation steps

1. `intro`: FadeIn the board rectangle and its title.
2. `protocol`: FadeIn code panel A on the right. Mark lines 4 to 6 (`subscribe`). After 2.5 s, mark lines 8 to 9 (`publish`).
3. `handler`: Mark line 1.
4. `simple`: Transform code panel A into code panel B. Mark line 3. FadeIn the two key texts and their arrows inside the board (no handler chips yet).
5. `subscribe`: Mark lines 5 to 6. Move the `print_event` chip from outside the board (start at (−3.6, 3.6)) to its place in row 1 (1 s). Then move the `handler` chip from (−3.6, 3.6) to its place in row 2 (1 s).
6. `decouple`: Remove the line mark. FadeIn the `GameEngine` box, the arrow, and the `publish(event)` label.

#### Accuracy notes

- `EventBus` is a `typing.Protocol`. `SimpleEventBus` does not inherit from it. It matches by its two methods.
- `EventHandler` is `Callable[[DomainEvent], None]`.
- `SimpleEventBus._handlers` is a `dict[type[DomainEvent], list[EventHandler]]`.
- `subscribe` uses `setdefault` to get the list for the type, or to start an empty list, and then appends the handler.
- The `GameWon` row and its `handler` chip are an example for this video. `main.py` subscribes only `print_event` to `DomainEvent`.
- The engine calls only `publish`. It never reads `_handlers`.

---

### E2S7: Dispatch by type, including subtypes

- **Scene ID:** `E2S7`
- **Manim class name:** `E2S7DispatchBySubtype`
- **Target duration:** 45 seconds (about 85 words)

#### Narration

Block 1:

> <bookmark mark='line'/>Look at one line in publish. It checks if the event is an instance of the event type. <bookmark mark='tree'/>This check includes subtypes. MarkPlaced is a DomainEvent. GameWon is a DomainEvent too.

Block 2:

> <bookmark mark='two_handlers'/>Now subscribe two handlers. The first handler is on DomainEvent. The second handler is on GameWon.

Block 3:

> <bookmark mark='markplaced'/>A MarkPlaced event arrives. Only the first handler gets it, because MarkPlaced is not a GameWon.

Block 4:

> <bookmark mark='gamewon'/>A GameWon event arrives. Both handlers get it.

Block 5:

> <bookmark mark='rule'/>So a handler on DomainEvent gets every event. A handler on GameWon gets only wins.

#### Visuals

- Right: code panel with the `publish` method, cut from SF9. Center (3.6, 2.2), width 6.6 or less.

Code panel string (cut from SF9, `src/tictactoe/event_bus.py`):

```python
    def publish(self, event: DomainEvent) -> None:
        for event_type, handlers in self._handlers.items():
            if isinstance(event, event_type):
                for handler in handlers:
                    handler(event)
```

- Right, below the code (step `tree`): a type tree. `DomainEvent` in a box (stroke `EVENT_COLOR`, font size 26) at (3.6, −0.4). Four child labels at y = −1.8, font size 22, `EVENT_COLOR`: `GameStarted` at (1.2, −1.8), `MarkPlaced` at (2.8, −1.8), `GameWon` at (4.4, −1.8), `GameDrawn` at (6.0, −1.8). Lines in `MUTED_COLOR` from the parent box to each child.
- Left (step `two_handlers`): two handler boxes (stroke `TEXT_COLOR`, width 3.4, height 1.0):
  - Handler 1 at (−3.5, 1.2), label `handler on DomainEvent`, font size 24.
  - Handler 2 at (−3.5, −1.8), label `handler on GameWon`, font size 24.
- Left, event entry point: event cards start at (−6.5, −0.3) and move right to (−5.3, −0.3). Event card size: width 2.4, height 0.8, title only.
- Received marks: a `✓` in `EVENT_COLOR`, font size 36, right of a handler box at x = −1.4. A `—` in `MUTED_COLOR`, font size 36, at the same place for "not received".

#### Animation steps

1. `line`: FadeIn the code panel. Mark line 3.
2. `tree`: FadeIn the type tree. Indicate `MarkPlaced` in the tree, then `GameWon`, 1 s apart.
3. `two_handlers`: FadeIn handler 1, then handler 2, 0.5 s apart.
4. `markplaced`: FadeIn a `MarkPlaced` event card at (−6.5, −0.3) and move it to (−5.3, −0.3). Make a copy of the card. Move the original to handler 1 (0.8 s). Move the copy toward handler 2, stop it at (−3.5, −0.9), and color its stroke `MUTED_COLOR` and FadeOut it. Show `✓` next to handler 1 and `—` next to handler 2. Hold 1 s, then FadeOut the card, the `✓`, and the `—`.
5. `gamewon`: FadeIn a `GameWon` event card at (−6.5, −0.3) and move it to (−5.3, −0.3). Make a copy. Move the original to handler 1 and the copy to handler 2 at the same time (0.8 s). Show `✓` next to both handlers.
6. `rule`: Show two lines of text at the bottom center, font size 28: `DomainEvent → every event` at (0, −3.0) and `GameWon → only wins` at (0, −3.6), in `TEXT_COLOR`.

#### Accuracy notes

- The check is `isinstance(event, event_type)`. It is true for the class and for all its subclasses.
- All four concrete events are direct subclasses of `DomainEvent`.
- A handler on `GameWon` does not get `GameStarted`, `MarkPlaced`, or `GameDrawn`.
- `publish` walks the subscribed types in the order of their first subscription. For each matching type, it calls the handlers in the order that they subscribed.
- The two-handler setup is an example. `main.py` subscribes only one handler, `print_event`, to `DomainEvent`.

---

### E2S8: The one-way flow

- **Scene ID:** `E2S8`
- **Manim class name:** `E2S8OneWayFlow`
- **Target duration:** 85 seconds (about 175 words)

This is the central scene of the episode.

#### Narration

Block 1:

> <bookmark mark='intro'/>Now put all the parts together. Each change goes along one path, in one direction.

Block 2:

> <bookmark mark='command'/>X wants cell zero, at row zero and column zero. The caller makes a PlaceMark command and gives it to the engine.

Block 3:

> <bookmark mark='engine'/>The engine looks for the game ID in its dictionary. The game exists, so the engine does not refuse.

Block 4:

> <bookmark mark='aggregate'/>The engine asks the Game aggregate to place the mark. The game is in progress, and the cell is free. So the guards pass, and the aggregate makes a new board.

Block 5:

> <bookmark mark='transition'/>The aggregate returns a Transition. It holds the new game and one event, MarkPlaced. The old game does not change.

Block 6:

> <bookmark mark='store'/>The engine stores the new game under the game ID.

Block 7:

> <bookmark mark='publish'/>Then the engine publishes the event on the bus. The bus finds the handlers that match.

Block 8:

> <bookmark mark='handler'/>The print_event handler is on DomainEvent, so it matches. It prints the name of the event class: MarkPlaced.

Block 9:

> <bookmark mark='oneway'/>Think of a conveyor belt that moves in one direction. Each station does its work and passes the result on. No arrow goes back.

#### Visuals

Eight stations in two rows. Row 1 goes left to right. Row 2 goes right to left. All station boxes are width 2.8, height 1.1, corner radius 0.15, label font size 26, unless the list says a different value.

- Row 1, y = 2.2:
  - S1 `PlaceMark` command card, center (−5.3, 2.2), fields `game_id: "game-1"`, `position: (0, 0)`, font size 20 for fields.
  - S2 station box `GameEngine`, stroke `TEXT_COLOR`, center (−1.8, 2.2). Small label under the box, `MUTED_COLOR`, font size 20: `find the game`.
  - S3 station box `Game`, stroke `RULE_COLOR`, center (1.8, 2.2). Small label under the box, `RULE_COLOR`, font size 20: `guards pass`.
  - S4 station box `Transition`, stroke `TEXT_COLOR`, width 2.8, height 1.6, center (5.3, 2.0). The label `Transition` is at the top inside the box. Inside the box, bottom left: a small board (scale 0.25) with an X in cell 0. Inside the box, bottom right: a small event card `MarkPlaced`, title only, width 1.3, height 0.45.
- Row 2, y = −1.0:
  - S5 station box `GameEngine`, center (5.3, −1.0). Small label under the box: `store`, `MUTED_COLOR`, font size 20.
  - S6 station box `SimpleEventBus`, center (1.8, −1.0). Small label under the box: `publish`, `MUTED_COLOR`, font size 20.
  - S7 station box `print_event`, center (−1.8, −1.0). Small label under the box: `react`, `MUTED_COLOR`, font size 20.
  - S8 terminal box, stroke `MUTED_COLOR`, fill black at opacity 0.4, center (−5.3, −1.0). Inside, in monospace font (use `Text` with `font="Monospace"`), font size 26, `TEXT_COLOR`: the text `MarkPlaced`.
- Arrows, `TEXT_COLOR`, stroke width 4, with tips: S1→S2, S2→S3, S3→S4 (row 1, pointing right). S4→S5 (down). S5→S6, S6→S7, S7→S8 (row 2, pointing left).
- Bottom caption, font size 24, at (0, −3.2), `MUTED_COLOR`, one line: `command → engine → aggregate → Transition → engine stores → bus publishes → handler reacts`. When a station is active, color the matching part of the caption `TEXT_COLOR`. If the caption is wider than 13.6 units, scale it down to 13.6.
- Moving token: a copy of the S1 command card at scale 0.5 moves along row 1 until S3. At S4 the token changes into the small `MarkPlaced` event card (`EVENT_COLOR`). The event card token moves along row 2.
- At step `oneway`: a curved arrow from S7 back to S3 in `ERROR_COLOR`, with a large `✗` in `ERROR_COLOR` on its middle.

#### Animation steps

1. `intro`: FadeIn all eight stations with no content in S8 and no content in S4 except its label. FadeIn the arrows in order, 0.2 s apart. FadeIn the caption in `MUTED_COLOR`.
2. `command`: Indicate S1. Color `command` in the caption `TEXT_COLOR`. Move a 0.5-scale copy of S1 (the token) along the arrow to S2 (1 s).
3. `engine`: Indicate S2. FadeIn the label `find the game`. Color `engine` in the caption. Move the token to S3 (1 s).
4. `aggregate`: Indicate S3 with color `RULE_COLOR`. FadeIn the label `guards pass`. Color `aggregate` in the caption. FadeOut the token.
5. `transition`: FadeIn the small board and the small `MarkPlaced` event card inside S4. Color `Transition` in the caption.
6. `store`: Move a copy of the small board from S4 to S5 (1 s). Place it inside S5 and FadeIn the label `store`. Color `engine stores` in the caption.
7. `publish`: Move a copy of the small `MarkPlaced` event card from S4 to S5, then to S6 (1.5 s in total). FadeIn the label `publish`. Color `bus publishes` in the caption.
8. `handler`: Move the event card from S6 to S7 (1 s). Indicate S7. FadeIn the label `react`. Then Write the text `MarkPlaced` in the terminal box S8. Color `handler reacts` in the caption.
9. `oneway`: Flash all seven arrows in order, left to right on row 1, then right to left on row 2 (0.2 s apart). Then create the red curved arrow from S7 to S3 with the `✗`. Hold 1.5 s. FadeOut the red arrow and the `✗`.

#### Accuracy notes

- The order of the flow is exact: command → engine → aggregate → `Transition` (new state + events) → engine stores state → bus publishes → handlers react.
- The engine stores the new game before it publishes the events (`engine.py`: line `self._games[...] = transition.game` comes before `self._publish(...)`).
- For this move, the `Transition` holds exactly one event, `MarkPlaced(game_id, X, Position(0, 0))`.
- `print_event` prints `type(event).__name__`, so the terminal shows only `MarkPlaced`. It does not show the fields.
- The `Game` aggregate makes the event. The engine and the bus only pass it on.
- In the first move of the real demo, X plays cell 0 (row 0, column 0). This scene uses that move.
- The red arrow means "a handler does not send anything back to the aggregate". The handler returns `None`.

---

### E2S9: The wiring in main.py

- **Scene ID:** `E2S9`
- **Manim class name:** `E2S9Wiring`
- **Target duration:** 40 seconds (about 85 words)

#### Narration

Block 1:

> <bookmark mark='wire'/>The demo file, main dot py, connects the parts in three lines. It makes a SimpleEventBus. It subscribes print_event to DomainEvent. It gives the bus to a new GameEngine.

Block 2:

> <bookmark mark='handler'/>print_event prints only the class name of the event. It is on DomainEvent, so it gets all four types of event.

Block 3:

> <bookmark mark='loop'/>The match loop runs while the game is in progress. It picks a position, sends a PlaceMark command, and prints the board. <bookmark mark='order'/>The engine publishes before it returns. So each event name prints before its board.

#### Visuals

- Right: a code panel that changes three times. Center (3.6, 1.8) for panels A and B. Center (3.6, −0.3) for panel C.
- Left: a terminal box, width 5.4, height 5.6, center (−3.6, −0.2), stroke `MUTED_COLOR`, fill black at opacity 0.4. Text inside uses `Text` with `font="Monospace"`, font size 22, `TEXT_COLOR`, left-aligned, starting at the top-left inside corner.
- Left, top of the terminal (step `order`): the text lines, in this order:

```text
GameStarted
MarkPlaced
 X |   |
---+---+---
   |   |
---+---+---
   |   |
```

Color the event names (`GameStarted`, `MarkPlaced`) `EVENT_COLOR`. Color the `X` `X_COLOR`.

Code panel string A (SF10, `main.py`):

```python
    bus = SimpleEventBus()
    bus.subscribe(DomainEvent, print_event)
    engine = GameEngine(bus)
```

Code panel string B (SF11, `main.py`):

```python
def print_event(event: DomainEvent) -> None:
    print(type(event).__name__)
```

Code panel string C (SF12, `main.py`):

```python
    while game.status is GameStatus.IN_PROGRESS:
        position = pick(agents[game.current_player], game, explore)
        game = engine.place_mark(PlaceMark(game_id, position))
        print(game.board.render())
        print()
```

#### Animation steps

1. `wire`: FadeIn code panel A. Mark line 1, then line 2, then line 3, each 2.5 s apart.
2. `handler`: Transform code panel A into code panel B. Mark line 2.
3. `loop`: Transform code panel B into code panel C and move it to its center (3.6, −0.3). FadeIn the empty terminal box on the left. Mark line 2, then line 3, then line 4, each 1.5 s apart.
4. `order`: Mark line 3. In the terminal, Write `GameStarted`, then `MarkPlaced`, then the five board lines, 0.4 s apart. Indicate the `MarkPlaced` line, then the board lines.

#### Accuracy notes

- The three wiring lines are in `main()`, in this order.
- `main.py` subscribes exactly one handler: `print_event` on `DomainEvent`.
- `pick(...)` asks the strategy for the player to move. Video 3 explains strategies. Do not explain `pick` further here.
- The loop condition is `game.status is GameStatus.IN_PROGRESS`.
- `engine.place_mark` returns the new `Game`. The loop stores it in `game`.
- The event names print before the board because `engine.place_mark` publishes inside the call, and `print(game.board.render())` runs after the call returns.
- Before the loop, `run_match` calls `engine.start_game(StartGame(game_id))`. That publishes `GameStarted`, so `GameStarted` is the first line after the match header.
- `render()` puts spaces at the end of lines. The terminal in this scene does not show the trailing spaces.

---

### E2S10: A real game, part 1

- **Scene ID:** `E2S10`
- **Manim class name:** `E2S10RealGamePart1`
- **Target duration:** 60 seconds (about 120 words)

#### Narration

Block 1:

> <bookmark mark='intro'/>Here is a real game from the demo. FirstAvailableStrategy plays X. It always takes the first free cell. MinimaxStrategy plays O. It searches for the best move.

Block 2:

> <bookmark mark='start'/>The demo sends StartGame. The bus publishes GameStarted. The board is empty, and X moves first.

Block 3:

> <bookmark mark='move1'/>X takes cell zero. The bus publishes one event: MarkPlaced, for player X at row zero, column zero.

Block 4:

> <bookmark mark='move2'/>O takes the center, cell four. MarkPlaced, for player O at row one, column one.

Block 5:

> <bookmark mark='move3'/>X takes cell one, because it is the first free cell. MarkPlaced, for player X at row zero, column one.

Block 6:

> <bookmark mark='count'/>A move that does not end the game makes exactly one event. Each board that you see is the new game from a Transition.

#### Visuals

- Top, full width: header text `FirstAvailableStrategy (X) vs MinimaxStrategy (O)`, font size 30, at (0, 3.5). Color `FirstAvailableStrategy (X)` with `X_COLOR` and `MinimaxStrategy (O)` with `O_COLOR`. Color `vs` `TEXT_COLOR`.
- Left: board from `make_board()`, center (−3.5, −0.3), with cell indices 0 to 8 in `MUTED_COLOR`.
- Left, above the board: a turn label at (−3.5, 2.5), font size 26: `turn: X` in `X_COLOR` or `turn: O` in `O_COLOR`.
- Right: the event log. Event cards from `make_event_card`, width 4.2, height 0.9. Title on the first line (font size 26), fields on one line below (font size 20). Card centers, top to bottom: (3.6, 2.4), (3.6, 1.3), (3.6, 0.2), (3.6, −0.9).
- Small command chip for each command: a command card, title only, width 2.2, height 0.6, that appears at (0, 2.5) and moves to the board before the mark appears. Title `StartGame` or `PlaceMark`.

The four event cards in this scene:

| Card | Title | Fields line |
|------|-------|-------------|
| 1 | `GameStarted` | `game_id: "game-1"` |
| 2 | `MarkPlaced` | `player: X   position: (0, 0)` |
| 3 | `MarkPlaced` | `player: O   position: (1, 1)` |
| 4 | `MarkPlaced` | `player: X   position: (0, 1)` |

(Cards 2 to 4 do not show `game_id`, so that they fit on one line.)

#### Animation steps

1. `intro`: Write the header. FadeIn the empty board with indices.
2. `start`: FadeIn a `StartGame` command chip at (0, 2.5), move it to the board center, and FadeOut it (1 s). FadeIn event card 1 at its place. FadeIn the label `turn: X` in `X_COLOR`.
3. `move1`: FadeIn a `PlaceMark` command chip at (0, 2.5), move it to cell 0, and FadeOut it (0.8 s). Create an X in cell 0 (`X_COLOR`). FadeIn event card 2. Change the turn label to `turn: O` in `O_COLOR`.
4. `move2`: Same pattern for cell 4: command chip, O mark in cell 4 (`O_COLOR`), event card 3. Change the turn label to `turn: X`.
5. `move3`: Same pattern for cell 1: command chip, X mark in cell 1, event card 4. Change the turn label to `turn: O`.
6. `count`: Indicate event cards 2, 3, and 4, 0.5 s apart. Then Indicate the board.

#### Accuracy notes

- The moves are exact and come from the real demo output: X at cell 0, O at cell 4, X at cell 1.
- Cell index = row × 3 + column. Cell 4 is (1, 1). Cell 1 is (0, 1).
- `FirstAvailableStrategy` returns the free cell with the lowest index.
- `MinimaxStrategy` searches the game tree. Video 4 explains it. Do not explain it here.
- X always moves first (`Game.start` sets `current_player=X`).
- `GameStarted` has only `game_id`. `MarkPlaced` has `game_id`, `player`, `position`.
- The demo game ID is a random UUID. `"game-1"` is a short label for the video.

---

### E2S11: A real game, part 2

- **Scene ID:** `E2S11`
- **Manim class name:** `E2S11RealGamePart2`
- **Target duration:** 45 seconds (about 90 words)

#### Narration

Block 1:

> <bookmark mark='move4'/>O takes cell two, at row zero, column two. This blocks the top row for X.

Block 2:

> <bookmark mark='move5'/>X takes cell three, the first free cell. Now X has two marks in the left column.

Block 3:

> <bookmark mark='move6'/>O takes cell six. That blocks the left column. It also completes a diagonal for O.

Block 4:

> <bookmark mark='two_events'/>This move makes two events. First MarkPlaced, then GameWon. GameWon records the winner, O, and the winning line: cells two, four, and six.

Block 5:

> <bookmark mark='status'/>The status is not in progress now, so the loop stops. The demo prints GameStatus dot O underscore WON.

#### Visuals

- Top, full width: the same header as E2S10: `FirstAvailableStrategy (X) vs MinimaxStrategy (O)`, font size 30, at (0, 3.5), with `X_COLOR` and `O_COLOR` as in E2S10.
- Left: board, center (−3.5, −0.3), cell indices in `MUTED_COLOR`. At the start of the scene the board has: X in cells 0 and 1 (`X_COLOR`), O in cell 4 (`O_COLOR`).
- Left, above the board: turn label at (−3.5, 2.5), font size 26. At the start: `turn: O` in `O_COLOR`.
- Right: the event log, a new empty list. Event cards width 4.2, height 0.9, title font size 26, fields font size 20. Card centers, top to bottom: (3.6, 2.4), (3.6, 1.3), (3.6, 0.2), (3.6, −0.9).
- Right, bottom (step `status`): a terminal line box, width 4.2, height 0.8, center (3.6, −2.6), stroke `MUTED_COLOR`, fill black at opacity 0.4. Monospace text `GameStatus.O_WON`, font size 24, `O_COLOR`.
- A winning-line highlight (step `two_events`): a thick line (stroke width 10) in `O_COLOR` through the centers of cells 2, 4, and 6.
- Threat hints: a dashed outline in `X_COLOR` around cell 2 (step `move4`, before the O appears) and around cell 6 (step `move5`).

The four event cards in this scene:

| Card | Title | Fields line |
|------|-------|-------------|
| 5 | `MarkPlaced` | `player: O   position: (0, 2)` |
| 6 | `MarkPlaced` | `player: X   position: (1, 0)` |
| 7 | `MarkPlaced` | `player: O   position: (2, 0)` |
| 8 | `GameWon` | `winner: O   line: (0, 2) (1, 1) (2, 0)` |

#### Animation steps

1. `move4`: Show the dashed `X_COLOR` outline around cell 2 (0.5 s). FadeIn a `PlaceMark` command chip (command card, title only, width 2.2, height 0.6) at (0, 2.5), move it to cell 2, and FadeOut it. Create an O in cell 2. FadeOut the dashed outline. FadeIn event card 5. Change the turn label to `turn: X` in `X_COLOR`.
2. `move5`: Command chip to cell 3. Create an X in cell 3. FadeIn event card 6. Show the dashed `X_COLOR` outline around cell 6. Change the turn label to `turn: O`.
3. `move6`: Command chip to cell 6. Create an O in cell 6. FadeOut the dashed outline. FadeIn event card 7.
4. `two_events`: FadeIn event card 8 directly after card 7. Create the winning-line highlight through cells 2, 4, 6. Indicate cards 7 and 8 together. FadeOut the turn label.
5. `status`: FadeIn the terminal line box with `GameStatus.O_WON`.

#### Accuracy notes

- The moves are exact: O at cell 2, X at cell 3, O at cell 6. O wins.
- The final board is: row 0 `X X O`, row 1 `X O _`, row 2 `O _ _` (underscore means an empty cell).
- The winning move publishes two events in this order: `MarkPlaced`, then `GameWon`.
- `GameWon.winner` is O. `GameWon.winning_line` is `(Position(0, 2), Position(1, 1), Position(2, 0))`, in that order.
- The match publishes 8 events in total: 1 `GameStarted`, 6 `MarkPlaced`, 1 `GameWon`.
- After a win, `Game.place_mark` does not change `current_player`. The status becomes `GameStatus.O_WON`.
- The demo prints `GameStatus.O_WON` exactly.
- The narration "blocks the top row" and "blocks the left column" describe the board. They do not describe how `MinimaxStrategy` chose the move.

---

### E2S12: A refused move

- **Scene ID:** `E2S12`
- **Manim class name:** `E2S12RefusedMove`
- **Target duration:** 45 seconds (about 100 words)

#### Narration

Block 1:

> <bookmark mark='setup'/>Now go back to the board after move two. X is in cell zero. O is in cell four. It is the turn of X.

Block 2:

> <bookmark mark='bad'/>Imagine a command for cell four. The demo never sends this command. We send it only to see a refusal.

Block 3:

> <bookmark mark='engine'/>The engine finds the game. <bookmark mark='guard'/>The aggregate checks the cell. The cell has a mark, so the aggregate raises PositionOccupiedError.

Block 4:

> <bookmark mark='nothing'/>There is no Transition. The engine stores nothing, and the bus publishes nothing. The board does not change, and it is still the turn of X.

Block 5:

> <bookmark mark='caller'/>The error goes back to the code that sent the command.

#### Visuals

- Left: board, center (−3.5, −0.3), cell indices in `MUTED_COLOR`. X in cell 0 (`X_COLOR`). O in cell 4 (`O_COLOR`).
- Left, above the board: turn label `turn: X` in `X_COLOR`, font size 26, at (−3.5, 2.5).
- Right, top: a command card `PlaceMark`, fields `game_id: "game-1"` and `position: (1, 1)`, width 3.8, height 1.5, center (3.6, 2.6).
- Right, middle: a small row of three station boxes, width 1.9, height 0.8, label font size 22, at y = 0.6: `GameEngine` at (1.6, 0.6), `Game` (stroke `RULE_COLOR`) at (3.6, 0.6), `SimpleEventBus` at (5.6, 0.6). `TEXT_COLOR` arrows between them.
- Right, below: an error box, rounded rectangle, stroke `ERROR_COLOR`, fill `ERROR_COLOR` at opacity 0.15, width 5.6, height 1.3, center (3.6, −1.2). Title `PositionOccupiedError` in bold, font size 28. Below it, the message in monospace, font size 22: `cell (1, 1) is already occupied`.
- Right, bottom (step `nothing`): three lines, font size 24, `ERROR_COLOR`, left-aligned at x = 1.4: `✗ no Transition` at y = −2.4, `✗ nothing stored` at y = −2.9, `✗ no event` at y = −3.4.
- A ghost O: a red outline circle (`ERROR_COLOR`, stroke width 4, no fill) in cell 4, drawn over the existing O. (A command card does not have a player. The ghost uses `ERROR_COLOR`, not `X_COLOR`, because it shows a refused move.)

#### Animation steps

1. `setup`: FadeIn the board with the X in cell 0 and the O in cell 4. FadeIn the turn label.
2. `bad`: FadeIn the command card on the right. FadeIn the three small station boxes and their arrows (with no highlight).
3. `engine`: Move a 0.4-scale copy of the command card (the token) to the `GameEngine` box (0.8 s). Indicate the `GameEngine` box. Move the token to the `Game` box (0.8 s).
4. `guard`: Draw the ghost outline in cell 4. Color the stroke of the token and the stroke of the big command card `ERROR_COLOR` (0.5 s). Color the stroke of the `Game` box `ERROR_COLOR`. FadeIn the error box.
5. `nothing`: FadeOut the token. Draw a red `✗` (`ERROR_COLOR`) over the arrow from `Game` to `SimpleEventBus`. FadeIn the three `✗` lines, 0.6 s apart. Indicate the turn label `turn: X` (it does not change).
6. `caller`: Move a copy of the error box, at scale 0.5, from its place up to the command card (1 s). FadeOut the ghost outline. Hold 1 s.

#### Accuracy notes

- This command does not occur in `main.py`. `FirstAvailableStrategy` and `MinimaxStrategy` choose only free cells. The narration must say that the demo never sends it.
- The board and turn match the real game after move 2: X at (0, 0), O at (1, 1), turn of X.
- The command is `PlaceMark("game-1", Position(1, 1))`.
- The engine finds the game with `_require`, so `GameNotFoundError` does not occur.
- The status is `IN_PROGRESS`, so the first guard passes. The second guard raises `PositionOccupiedError(1, 1)`.
- The exact message is `cell (1, 1) is already occupied`.
- The error comes from `Game.place_mark`, before `Board.with_mark` runs.
- After the error: no `Transition`, the stored game does not change, the bus publishes 0 events, `current_player` is still X.
- `GameEngine` does not catch the error. The error goes to the caller of `engine.place_mark`.
- The command card turns red because the command was refused. Red means "error or illegal state".

---

## 7. Closing and hook

### E2S13: Closing and hook

- **Scene ID:** `E2S13`
- **Manim class name:** `E2S13ClosingHook`
- **Target duration:** 25 seconds (about 45 words)

#### Narration

Block 1:

> <bookmark mark='summary'/>Now you know how a move happens. A command goes in. The rules give a Transition. The engine stores the new game, and the bus publishes the events.

Block 2:

> <bookmark mark='seat'/>But each move came from somewhere. <bookmark mark='question'/>Who decides the next move?

Block 3:

> <bookmark mark='next'/>Next: the simplest possible opponent.

#### Visuals

- Center, top: a compact one-way flow row at y = 2.2, five items, width 2.2, height 0.8, label font size 20: command card `PlaceMark` (title only) at (−5.6, 2.2), station box `GameEngine` at (−2.8, 2.2), station box `Game` (stroke `RULE_COLOR`) at (0, 2.2), station box `SimpleEventBus` at (2.8, 2.2), event card `MarkPlaced` (title only) at (5.6, 2.2). `TEXT_COLOR` arrows between them, pointing right.
- Center, middle (step `seat`): the loop line from `main.py` in a code panel at center (0, 0), scale so that the width is 10 or less:

```python
        position = pick(agents[game.current_player], game, explore)
```

- The word `pick` gets a rectangle, stroke `TEXT_COLOR`, stroke width 2.
- Center, bottom (step `question`): text `Who decides the next move?`, font size 48, `TEXT_COLOR`, at (0, −2.0).
- Step `next`: text `Next: The Naive Opponent`, font size 36, `MUTED_COLOR`, at (0, −3.1).

#### Animation steps

1. `summary`: FadeIn the five flow items from left to right, 0.4 s apart, with the arrows.
2. `seat`: FadeIn the one-line code panel. Draw the rectangle around `pick`.
3. `question`: Write `Who decides the next move?`.
4. `next`: FadeIn `Next: The Naive Opponent`. Hold 1.5 s. FadeOut all objects.

#### Accuracy notes

- The code line is copied exactly from `run_match` in `main.py`, with its 8 leading spaces.
- The series question is "Who decides the next move?". Do not change the words.
- The next video is episode 3, "The Naive Opponent". It shows `FirstAvailableStrategy`.
- The compact row is a short summary of E2S8. It does not show the `Transition` and the store step. Do not add arrows that go back.

## 8. Checks

Answer each question with yes or no. A "no" is a problem to correct.

1. Does the video say that there are exactly two commands, `StartGame` and `PlaceMark`?
2. Does the video say that a command is a request that the program can refuse, and that a domain event is a fact about the past?
3. Does the video name exactly four domain events: `GameStarted`, `MarkPlaced`, `GameWon`, `GameDrawn`?
4. Does the video show that the `GameEngine` raises `GameAlreadyExistsError` and `GameNotFoundError`, and that `Game.place_mark` raises `GameAlreadyOverError` and `PositionOccupiedError`?
5. Does the video show the four steps of `GameEngine.place_mark` in this order: find the game, ask the aggregate, store the new game, publish the events?
6. Does the video say that only the `Game` aggregate makes events?
7. Does the video say that `EventBus` is a protocol with the two methods `subscribe` and `publish`?
8. Does the video show that a handler on `DomainEvent` gets every event and a handler on `GameWon` gets only wins?
9. Does E2S8 show the flow in this order: command → engine → aggregate → `Transition` → engine stores → bus publishes → handler reacts, with no arrow that goes back?
10. Does the terminal in E2S8 show only the class name `MarkPlaced`, and no fields?
11. Does the real game show these moves in order: X 0, O 4, X 1, O 2, X 3, O 6?
12. Does the winning move show two event cards, `MarkPlaced` then `GameWon`, with the winning line at cells 2, 4, 6?
13. Does E2S11 show the final status text `GameStatus.O_WON` exactly?
14. Does E2S12 say that the demo never sends the refused command?
15. Does E2S12 show the exact message `cell (1, 1) is already occupied`, no event, no stored change, and the turn still with X?
16. Is every code panel the same, character for character, as the snippet in the episode file?
17. Do command cards use `COMMAND_COLOR`, event cards `EVENT_COLOR`, rule parts `RULE_COLOR`, and errors `ERROR_COLOR`, with no other use of these colors?
18. Is each scene between 20 and 90 seconds, and is the total between 8 and 12 minutes?
19. Is all text inside the frame, with no overlap, in every extracted frame?
20. Does the recap in E2S1 take 20 seconds or less?
