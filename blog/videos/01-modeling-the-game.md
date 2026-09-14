# Episode 1: The Parts of the Game

## 1. Header

- **Series:** Who Decides the Next Move?
- **Episode number:** 1 of 6
- **Title:** The Parts of the Game
- **Target length:** 10 minutes 10 seconds (12 scenes)
- **Source files:**
  - `src/tictactoe/value_objects.py`
  - `src/tictactoe/game.py`
  - `src/tictactoe/errors.py`
- **Source article:** `blog/articles/01-modeling-the-game.md`, from the start up to the section "Asking for changes: commands" (that section is not in this episode). The sections are:
  - "Who decides the next move?"
  - "The whole game is one small package"
  - "The raw facts: value objects"
  - "A board that can't be in a bad state"
  - "The aggregate: the one place the rules live"
  - "Immutability, gently: we produce the next version, never edit"
- **Demo data:** The example game in scene E1S10 is the first game of the output of `uv run main.py` (`FirstAvailableStrategy (X) vs MinimaxStrategy (O)`).

## 2. Goal

After the video, the viewer can name the parts of the tic-tac-toe domain model and tell what each part does. The viewer can explain these items: a value object checks its invariant in `__post_init__` and raises a `DomainError` for a bad value; the `Board` checks only that it has exactly nine cells; the `Game` aggregate is the one place where the rules of play live; `Game.place_mark` gives a `Transition` (the next `Game` plus a list of what happened); and `Board.with_mark` and `Game.place_mark` make a new object and do not change the old object.

## 3. Recap from the last video

Video 1 has no last video. Scene E1S1 is a short series introduction (target 35 seconds). It gives the series question, "Who decides the next move?", and the six video titles from `blog/videos/README.md`:

| # | Title |
|---|-------|
| 1 | The Parts of the Game |
| 2 | How a Move Happens |
| 3 | The Naive Opponent |
| 4 | The Perfect Player |
| 5 | Learning from Rewards |
| 6 | A Neural Network Policy |

The README gives a maximum of 20 seconds for a recap. A series introduction with six titles needs more time, so E1S1 has 35 seconds.

## 4. Terms

- **Domain:** The subject that the program models. In this project, the domain is the game of tic-tac-toe.
- **Value object:** A small, frozen object that holds data and checks its data when Python makes it.
- **Invariant:** A rule about a value that must always be true, for example "a `Board` has exactly nine cells".
- **`__post_init__`:** A method that a Python dataclass runs immediately after it sets the fields. The value objects check their invariants here.
- **`DomainError`:** The base class of all errors that the domain raises when a rule is broken.
- **Frozen dataclass:** A dataclass with `frozen=True`. Python does not let code change its fields after Python makes the object.
- **`Player`:** A value object for one of the two players. Its `symbol` is `"X"` or `"O"`.
- **`Position`:** A value object for one cell location, as a `row` and a `column` from 0 to 2.
- **Cell index:** A number from 0 to 8 for a cell. Index 0 is top left. Index 8 is bottom right.
- **`Cell`:** A value object for the contents of one cell: a `Player` or `None`.
- **`Board`:** A value object that holds a tuple of exactly nine `Cell` objects.
- **`GameStatus`:** An enum with four values: `IN_PROGRESS`, `X_WON`, `O_WON`, `DRAW`.
- **Winning line:** Three cell indices in a row, a column, or a diagonal. The tuple `WINNING_LINES` holds all eight.
- **Aggregate:** The one object that owns a group of related data and the rules that change it. In this project, the aggregate is `Game`.
- **`Transition`:** The result of `Game.start` or `Game.place_mark`: the next `Game` plus a list of what happened (the events).
- **Immutability:** The rule that no domain object changes. A change makes a new object.

## 5. Source facts

### 5.1 Spoken forms of code names

The narration text uses these spoken forms, so that the text-to-speech voice reads them correctly. The screen always shows the code name exactly.

| Code name on screen | Spoken form in narration |
|---------------------|--------------------------|
| `__post_init__` | post init |
| `WINNING_LINES` | winning lines |
| `InvalidPlayerError` | Invalid Player Error |
| `InvalidPositionError` | Invalid Position Error |
| `InvalidBoardError` | Invalid Board Error |
| `PositionOccupiedError` | Position Occupied Error |
| `GameAlreadyOverError` | Game Already Over Error |
| `GameNotFoundError` | Game Not Found Error |
| `GameAlreadyExistsError` | Game Already Exists Error |
| `DomainError` | Domain Error |
| `FrozenInstanceError` | Frozen Instance Error |
| `GameStatus` | Game Status |
| `IN_PROGRESS`, `X_WON`, `O_WON`, `DRAW` | in progress, X won, O won, draw |
| `with_mark` | with mark |
| `place_mark` | place mark |
| `winning_line` | winning line |
| `is_full` | is full |
| `from_index` | from index |
| `current_player` | current player |
| `MarkPlaced`, `GameWon`, `GameStarted` | Mark Placed, Game Won, Game Started |
| `errors.py` | errors dot py |

### 5.2 Code snippets

Copy each snippet exactly. Keep the leading spaces. Each snippet has an ID. The scenes use the IDs.

**S-WINNING-LINES** (`value_objects.py`)

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

**S-PLAYER** (`value_objects.py`)

```python
@dataclass(frozen=True, slots=True)
class Player:
    symbol: str

    def __post_init__(self) -> None:
        if self.symbol not in ("X", "O"):
            raise InvalidPlayerError(self.symbol)

    @property
    def opponent(self) -> "Player":
        return Player("O" if self.symbol == "X" else "X")


X = Player("X")
O = Player("O")
```

**S-POSITION-CHECK** (`value_objects.py`)

```python
SIZE = 3

@dataclass(frozen=True, slots=True)
class Position:
    row: int
    column: int

    def __post_init__(self) -> None:
        if not 0 <= self.row < SIZE or not 0 <= self.column < SIZE:
            raise InvalidPositionError(self.row, self.column)
```

Note: in the source file, `SIZE = 3` is at the top of the file and other code is between it and `Position`. The snippet puts the two parts together. Do not change the lines.

**S-POSITION-INDEX** (`value_objects.py`)

```python
    @property
    def index(self) -> int:
        return self.row * SIZE + self.column

    @classmethod
    def from_index(cls, index: int) -> "Position":
        if not 0 <= index < SIZE * SIZE:
            raise InvalidPositionError(index // SIZE, index % SIZE)
        return cls(index // SIZE, index % SIZE)
```

**S-CELL** (`value_objects.py`)

```python
@dataclass(frozen=True, slots=True)
class Cell:
    player: Player | None

    @property
    def display(self) -> str:
        return self.player.symbol if self.player is not None else " "
```

**S-BOARD** (`value_objects.py`)

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

**S-WITH-MARK** (`value_objects.py`)

```python
    def with_mark(self, position: Position, player: Player) -> "Board":
        if self.is_occupied(position):
            raise PositionOccupiedError(position.row, position.column)
        cells = list(self.cells)
        cells[position.index] = Cell(player)
        return Board(tuple(cells))
```

**S-WINNING-LINE** (`value_objects.py`)

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

**S-IS-FULL** (`value_objects.py`)

```python
    def is_full(self) -> bool:
        return all(cell.player is not None for cell in self.cells)
```

**S-ERRORS** (`errors.py`, cut to the base class and two examples)

```python
class DomainError(Exception):
    pass


class InvalidPlayerError(DomainError):
    def __init__(self, symbol: str) -> None:
        super().__init__(f"invalid player symbol {symbol!r}")


class InvalidBoardError(DomainError):
    def __init__(self) -> None:
        super().__init__("a board must have exactly 9 cells")
```

**S-GAME-FIELDS** (`game.py`)

```python
@dataclass(frozen=True, slots=True)
class Game:
    id: str
    board: Board
    current_player: Player
    status: GameStatus
```

**S-GAME-STATUS** (`value_objects.py`)

```python
class GameStatus(Enum):
    IN_PROGRESS = "in_progress"
    X_WON = "x_won"
    O_WON = "o_won"
    DRAW = "draw"
```

**S-GAME-START** (`game.py`)

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

**S-TRANSITION** (`game.py`)

```python
@dataclass(frozen=True, slots=True)
class Transition:
    game: Game
    events: tuple[DomainEvent, ...]
```

**S-PLACE-MARK-GUARDS** (`game.py`)

```python
    def place_mark(self, position: Position) -> "Transition":
        if self.status is not GameStatus.IN_PROGRESS:
            raise GameAlreadyOverError(self.id)
        if self.board.is_occupied(position):
            raise PositionOccupiedError(position.row, position.column)

        marked_board = self.board.with_mark(position, self.current_player)
        line = marked_board.winning_line(self.current_player)
```

**S-PLACE-MARK-WIN** (`game.py`)

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

**S-PLACE-MARK-REST** (`game.py`)

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

### 5.3 Facts and numbers

These facts were checked by a run of the code (`uv run python -c ...`).

- `SIZE` is 3. A board has `SIZE * SIZE` = 9 cells.
- `WINNING_LINES` has 8 lines: 3 rows `(0, 1, 2)`, `(3, 4, 5)`, `(6, 7, 8)`; 3 columns `(0, 3, 6)`, `(1, 4, 7)`, `(2, 5, 8)`; 2 diagonals `(0, 4, 8)`, `(2, 4, 6)`.
- Cell index grid:

  ```text
  0 | 1 | 2
  3 | 4 | 5
  6 | 7 | 8
  ```

- `Position.index` is `row * 3 + column`. `Position(1, 2).index` is 5. `Position.from_index(5)` is `Position(row=1, column=2)`. `Position(2, 1).index` is 7.
- Error messages (exact text from a run):
  - `Player("Q")` raises `InvalidPlayerError: invalid player symbol 'Q'`
  - `Position(5, 0)` raises `InvalidPositionError: invalid position (5, 0)`
  - `Position.from_index(9)` raises `InvalidPositionError: invalid position (3, 0)`
  - A `Board` with 8 cells raises `InvalidBoardError: a board must have exactly 9 cells`
  - `with_mark` on an occupied center cell raises `PositionOccupiedError: cell (1, 1) is already occupied`
  - `place_mark` on a finished game with id `g1` raises `GameAlreadyOverError: game g1 is already over`
  - An assignment `board.cells = ()` raises `FrozenInstanceError: cannot assign to field 'cells'`
- `DomainError` has 7 subclasses in `errors.py`: `InvalidPositionError`, `InvalidPlayerError`, `InvalidBoardError`, `PositionOccupiedError`, `GameAlreadyOverError`, `GameNotFoundError`, `GameAlreadyExistsError`. `GameNotFoundError` and `GameAlreadyExistsError` are for the `GameEngine` (video 2).
- `errors.py` imports nothing from other domain modules. Its constructors take only `str` and `int` values.
- `X.opponent == O` is `True`. `X.opponent is O` is `False`: `opponent` makes a new `Player("O")` that is equal to `O`.
- `Game.start("g1")` gives a `Transition` with `current_player` `X`, status `IN_PROGRESS`, an empty board, and one event: `GameStarted(game_id='g1')`.
- After `place_mark`, the old `Game` does not change. Test: after `t.game.place_mark(Position(0, 0))`, `t.game.board.is_occupied(Position(0, 0))` is `False`.
- `Board.empty().with_mark(Position(1, 1), X)` gives a new board. The old board is still empty. `old is new` is `False`.
- Two boards with the same marks are equal and have the same hash. A `Board` can be a dictionary key. `PolicyLearner` and `NeuralPolicyLearner` use `dict[Board, float]` for their value tables (videos 5 and 6).
- **Demo game** (first game in `/tmp/ttt_main_output.txt`, X is `FirstAvailableStrategy`, O is `MinimaxStrategy`). Moves by cell index: X 0, O 4, X 1, O 2, X 3, O 6. O wins on line `(2, 4, 6)`. The final status is `GameStatus.O_WON`. The last move gives two events: `MarkPlaced` and `GameWon`. The `winning_line` result is `(Position(0, 2), Position(1, 1), Position(2, 0))`. Board before the last move:

  ```text
   X | X | O
  ---+---+---
   X | O |
  ---+---+---
     |   |
  ```

  Board after the last move:

  ```text
   X | X | O
  ---+---+---
   X | O |
  ---+---+---
   O |   |
  ```

- In the demo, `main.py` uses a `uuid` for the game id. This episode shows the id `g1` to keep the screen simple.

### 5.4 Layout conventions for all scenes

- Manim frame: 14.2 units wide, 8 units high. The center is (0, 0).
- **Title:** `Text`, font size 40, color `TEXT_COLOR`, at the top edge (`to_edge(UP, buff=0.4)`).
- **Left area:** center at (−3.6, −0.3). Put the board or diagram here.
- **Right area:** center at (3.4, −0.3). Put the code panel here. Scale the code panel so that its width is 6.6 units or less and its height is 6.2 units or less.
- **Board:** `make_board()` from `common.board`, center in the left area unless the scene says a different position. Show cell indices only when the scene says so.
- **Error label:** `Text` in `ERROR_COLOR`, font size 26, below the object that failed, 0.4 units under it.
- **Rule box:** a `RoundedRectangle` with stroke `RULE_COLOR`, stroke width 3, no fill, around the checked code line or text.
- **Highlight of a code line:** a `SurroundingRectangle` around the line, color `RULE_COLOR` for a check, `ERROR_COLOR` for a raise, `EVENT_COLOR` for events, stroke width 3.
- **Rejection animation ("reject"):** color the bad object `ERROR_COLOR`, play `Wiggle` on it, show the error label, then `FadeOut` the bad object with a shift of 0.5 units down. The error label stays until the next step.
- The helper `draw_mark()` in `common/board.py` draws a mark. It is not the method `Game.place_mark`. Do not confuse the two.

### 5.5 Duration summary

| Scene | Class | Target |
|-------|-------|--------|
| E1S1 | `E1S1SeriesIntro` | 35 s |
| E1S2 | `E1S2GameRules` | 60 s |
| E1S3 | `E1S3DomainWords` | 45 s |
| E1S4 | `E1S4Player` | 45 s |
| E1S5 | `E1S5Position` | 55 s |
| E1S6 | `E1S6CellAndBoard` | 60 s |
| E1S7 | `E1S7BoardQueries` | 50 s |
| E1S8 | `E1S8ErrorFamily` | 30 s |
| E1S9 | `E1S9GameAggregate` | 60 s |
| E1S10 | `E1S10PlaceMark` | 75 s |
| E1S11 | `E1S11Immutability` | 65 s |
| E1S12 | `E1S12ClosingHook` | 30 s |
| **Total** | | **610 s (10 min 10 s)** |

### 5.6 Differences between the article and the code

The code is correct. The narration follows the code.

1. **`Cell` does not check its value.** The article says: "There is no way to put a `"Q"` in a cell, because there is no `Player("Q")`." `Cell` has no `__post_init__`, and Python does not check type hints at run time. `Cell("Q")` runs with no error (checked by a run). The narration says only that `Cell` "uses the Player type".
2. **`Board` checks only the number of cells.** The article section title is "A board that can't be in a bad state". The only `Board` invariant is `len(self.cells) == 9`. A `Board` of nine X marks, or a `Board` of nine strings, is accepted (checked by a run). Turn order is kept by `Game`, not by `Board`. The narration says this in E1S6.
3. **Duplicate occupied check.** `Game.place_mark` checks `is_occupied` and raises `PositionOccupiedError`. Then `Board.with_mark` checks the same thing again. The narration shows the check in both places and does not say that one is missing.
4. **`opponent` makes a new object.** `X.opponent` is equal to `O`, but it is not the same object as the constant `O`. The narration says "The opponent of X is O", which is correct for equality.
5. **Board keys.** The article says that "the learners in articles 3 and 4" use `Board` keys. In the video series, the learners are in videos 5 and 6. The narration uses the video numbers.

## 6. Scenes

### E1S1: Series introduction

- **Scene ID:** E1S1
- **Class name:** `E1S1SeriesIntro`
- **Target duration:** 35 seconds (about 83 words)

**Narration**

Block 1:
> This series asks one question. <bookmark mark='question'/>Who decides the next move? Each video gives a different answer.

Block 2:
> <bookmark mark='roadmap'/>Video one shows the parts of the game. Video two shows how a move happens. <bookmark mark='players'/>Videos three and four show a naive opponent and a perfect player. <bookmark mark='learners'/>Videos five and six show two players that learn. One learns from rewards. One uses a neural network.

Block 3:
> <bookmark mark='today'/>In this video, the answer is: nobody. We build only the game, and we make sure that its rules are always correct.

**Visuals**

- Center: the question text "Who decides the next move?", font size 56, color `TEXT_COLOR`.
- Left area (x = −4.2): a small empty board, `make_board()` scaled to 0.6.
- Right area (x = 2.4): a vertical list of six rows, font size 28. Each row is "N  Title" with the titles from section 3. Color `MUTED_COLOR`. Align the rows on the left edge, 0.6 units apart.
- Highlight: row 1 changes to `TEXT_COLOR` and gets a `RULE_COLOR` rounded rectangle around it.

**Animation steps**

1. Before `question`: start with an empty frame.
2. `question`: `Write` the question text at the center.
3. `roadmap`: move the question text to the top (title position, font size 40). `FadeIn` the small board on the left. `FadeIn` rows 1 and 2 of the list on the right, one after the other.
4. `players`: `FadeIn` rows 3 and 4.
5. `learners`: `FadeIn` rows 5 and 6.
6. `today`: color row 1 `TEXT_COLOR`. `Create` the rounded rectangle around row 1. Change rows 2 to 6 to opacity 0.4. `Indicate` the small board.
7. End: hold for 1 second.

**Accuracy notes**

- Use the six titles exactly as in section 3.
- Do not name the classes of the later videos in this scene.
- "Nobody" is correct: this episode has no strategy and no learner.

---

### E1S2: The rules of tic-tac-toe

- **Scene ID:** E1S2
- **Class name:** `E1S2GameRules`
- **Target duration:** 60 seconds (about 135 words)

**Narration**

Block 1:
> Tic-tac-toe has two players, X and O. <bookmark mark='grid'/>They play on a grid of three rows and three columns. That makes nine cells. <bookmark mark='indices'/>The code gives each cell a number from 0 to 8. Cell 0 is at the top left. Cell 8 is at the bottom right.

Block 2:
> <bookmark mark='turns'/>X plays first. Then the players take turns. In each turn, a player puts one mark in one empty cell.

Block 3:
> <bookmark mark='lines'/>A player wins with three marks in a line. There are eight lines: three rows, three columns, and two diagonals. <bookmark mark='code'/>The code keeps the eight lines as plain data, in a tuple with the name winning lines. <bookmark mark='line_example'/>Each line is three cell numbers. For example, 0, 4, 8 is a diagonal.

Block 4:
> <bookmark mark='draw'/>If all nine cells are full and no player has a line, the game is a draw.

**Visuals**

- Title: "The rules".
- Left area: `make_board()`.
- Cell indices: small `MUTED_COLOR` text, font size 22, at the top left corner of each cell.
- X marks in `X_COLOR`, O marks in `O_COLOR`.
- Winning line: a `Line` from the center of the first cell to the center of the third cell, stroke width 8. Use `RULE_COLOR` for the eight-line demonstration.
- Right area: code panel with snippet **S-WINNING-LINES**.
- Line counter: `Text` "8 lines", font size 32, `RULE_COLOR`, below the board (0.5 units under it).

**Animation steps**

1. Before `grid`: show the title. Show an X mark and an O mark side by side in the left area (use `make_x()` and `make_o()`), scaled to 0.8.
2. `grid`: `FadeOut` the two marks. `Create` the board in the left area.
3. `indices`: `FadeIn` the nine index labels in order 0 to 8, with a lag ratio of 0.1. `Indicate` label 0, then `Indicate` label 8.
4. `turns`: place X in cell 4, then O in cell 0, then X in cell 8. Wait 0.5 seconds between marks. Then `FadeOut` the three marks.
5. `lines`: draw each of the eight winning lines on the board, one at a time, in the order of **S-WINNING-LINES**. Each line appears (`Create`, 0.4 seconds) and fades out (0.2 seconds) before the next line. After the last line, `FadeIn` the "8 lines" counter.
6. `code`: `FadeIn` the code panel in the right area.
7. `line_example`: put a `RULE_COLOR` `SurroundingRectangle` around the line `    (0, 4, 8),` in the code panel. At the same time, draw the line from cell 0 to cell 8 on the board and keep it.
8. `draw`: `FadeOut` the line and the rectangle. Fill the board with the draw position from the accuracy notes, cell by cell, fast (0.15 seconds each): X in cells 0, 1, 5, 6, 8 and O in cells 2, 3, 4, 7. Then show the text "DRAW" in `NEUTRAL_COLOR`, font size 40, below the board in place of the counter.
9. End: hold for 1 second.

**Accuracy notes**

- Exactly 8 winning lines. The order in the code is rows, then columns, then diagonals.
- Index 0 is top left, index 8 is bottom right. Index = row × 3 + column.
- The draw position for step 8 is X in 0, 1, 5, 6, 8 and O in 2, 3, 4, 7:

  ```text
   X | X | O
   O | O | X
   X | O | X
  ```

  It has 5 X marks and 4 O marks and no line for X or O.
- X plays first. This fact is in `Game.start` (`current_player=X`).

---

### E1S3: Words for the domain

- **Scene ID:** E1S3
- **Class name:** `E1S3DomainWords`
- **Target duration:** 45 seconds (about 104 words)

**Narration**

Block 1:
> Before we read the code, we need six words. <bookmark mark='domain'/>The domain is the subject of the program. Here, the domain is tic-tac-toe.

Block 2:
> <bookmark mark='value_object'/>A value object is a small piece of data. It checks itself when Python makes it. <bookmark mark='invariant'/>An invariant is a rule that must always be true. For example: a board has nine cells.

Block 3:
> <bookmark mark='domain_error'/>If a value breaks an invariant, the code raises a Domain Error. <bookmark mark='aggregate'/>An aggregate is the one object that owns the rules for a group of data. Here, the aggregate is Game. <bookmark mark='transition'/>A Transition is the result of a move: the next Game, and a list of what happened.

**Visuals**

- Title: "Six words".
- A vertical list of six term cards, centered at x = 0, from y = 2.3 down to y = −2.7, 1.0 unit apart.
- Each card: a `RoundedRectangle` 10 units wide, 0.8 units high, stroke color as below, no fill. Inside, on the left: the term in bold, font size 30. On the right: a short definition, font size 24, `MUTED_COLOR`.
- Cards and stroke colors:
  1. "Domain" — "the subject: tic-tac-toe" — stroke `TEXT_COLOR`
  2. "Value object" — "data that checks itself" — stroke `TEXT_COLOR`
  3. "Invariant" — "a rule that is always true" — stroke `RULE_COLOR`
  4. "DomainError" — "raised when a rule breaks" — stroke `ERROR_COLOR`
  5. "Aggregate" — "Game: owns the rules" — stroke `TEXT_COLOR`
  6. "Transition" — "next Game + what happened" — stroke `EVENT_COLOR`

**Animation steps**

1. Before `domain`: show the title.
2. `domain`: `FadeIn` card 1 with a shift of 0.3 units to the right.
3. `value_object`: `FadeIn` card 2.
4. `invariant`: `FadeIn` card 3.
5. `domain_error`: `FadeIn` card 4.
6. `aggregate`: `FadeIn` card 5.
7. `transition`: `FadeIn` card 6. Then `Indicate` all six cards together.
8. End: hold for 1 second.

**Accuracy notes**

- "Transition" is a class in `game.py` with two fields: `game` and `events`.
- The events are a tuple in the code. The narration says "a list of what happened". Do not explain events in this video. Video 2 explains them.
- Use the exact card text above. Do not add the word "entity" or "repository"; the code has neither.

---

### E1S4: The Player value object

- **Scene ID:** E1S4
- **Class name:** `E1S4Player`
- **Target duration:** 45 seconds (about 100 words)

**Narration**

Block 1:
> Our first value object is Player. <bookmark mark='code'/>Player has one field: symbol. Player is a frozen dataclass. Frozen means that its fields cannot change.

Block 2:
> <bookmark mark='post_init'/>Python runs the method post init immediately after it sets the fields. Here, post init checks the invariant: the symbol must be X or O.

Block 3:
> <bookmark mark='bad'/>Now we try to make a Player with the symbol Q. <bookmark mark='reject'/>The check fails. Python raises Invalid Player Error, and no Player object exists.

Block 4:
> <bookmark mark='constants'/>Only two players are possible, so the module makes two constants, X and O. <bookmark mark='opponent'/>The opponent property gives the other player. The opponent of X is O.

**Visuals**

- Title: "Player".
- Right area: code panel with snippet **S-PLAYER**.
- Left area: an "object factory" diagram. A `RoundedRectangle` 3.6 wide and 1.2 high at (−3.6, 1.2), stroke `RULE_COLOR`, with the text `symbol in ("X", "O")` inside (font size 24, `RULE_COLOR`). This is the rule box.
- Input tokens: `Text` in a small rounded rectangle, at (−3.6, 2.9), above the rule box. Tokens: `Player("X")` in `X_COLOR`, `Player("Q")` in `TEXT_COLOR` (it turns `ERROR_COLOR` on rejection).
- Output: an X mark (`make_x()`, scale 0.7) at (−4.6, −1.2) and an O mark (`make_o()`, scale 0.7) at (−2.6, −1.2).
- Error label: `InvalidPlayerError: invalid player symbol 'Q'`, `ERROR_COLOR`, font size 24, at (−3.6, 0.0).

**Animation steps**

1. Before `code`: show the title.
2. `code`: `FadeIn` the code panel. Put a `TEXT_COLOR` `SurroundingRectangle` around the line `@dataclass(frozen=True, slots=True)`, then around `    symbol: str`.
3. `post_init`: move the rectangle to the three lines of `__post_init__` and change its color to `RULE_COLOR`. `Create` the rule box on the left.
4. `bad`: `FadeIn` the token `Player("Q")` above the rule box. Move it down onto the top edge of the rule box (0.8 seconds).
5. `reject`: do the rejection animation on the token (section 5.4). Show the error label. Put an `ERROR_COLOR` `SurroundingRectangle` around the line `            raise InvalidPlayerError(self.symbol)`.
6. `constants`: `FadeOut` the error label and the red rectangle. Put a `TEXT_COLOR` rectangle around the two lines `X = Player("X")` and `O = Player("O")`. Move a token `Player("X")` through the rule box (down, 1 second); at the bottom it becomes the X mark. Do the same with a token `Player("O")` in `O_COLOR`; it becomes the O mark.
7. `opponent`: move the rectangle to the `opponent` property lines. Draw a curved `Arrow` (`CurvedArrow`) from the X mark to the O mark, color `TEXT_COLOR`, with the label `opponent` (font size 22) above the arrow.
8. End: hold for 1 second.

**Accuracy notes**

- The only invariant of `Player` is `symbol in ("X", "O")`.
- The error message is exactly `invalid player symbol 'Q'` (with single quotes, from `{symbol!r}`).
- `X` and `O` are module-level constants, not class attributes.
- `X.opponent` makes a new `Player("O")`. It is equal to `O`. Do not say that it "is the same object".

---

### E1S5: The Position value object

- **Scene ID:** E1S5
- **Class name:** `E1S5Position`
- **Target duration:** 55 seconds (about 124 words)

**Narration**

Block 1:
> A Position is one cell on the board, as a row and a column. <bookmark mark='code'/>SIZE is 3, so a row and a column must each be 0, 1, or 2.

Block 2:
> <bookmark mark='good'/>Position with row 1 and column 2 is correct. It is the cell in the middle row, on the right. <bookmark mark='bad'/>Now we try row 5, column 0. <bookmark mark='reject'/>Row 5 is not on the board. Python raises Invalid Position Error.

Block 3:
> <bookmark mark='index_code'/>The index property changes a row and a column into one cell number. The cell number is the row times 3, plus the column. <bookmark mark='index_example'/>Row 1, column 2 gives 1 times 3, plus 2. That is 5. <bookmark mark='from_index'/>The method from index does the opposite. It changes cell number 5 back into row 1, column 2.

**Visuals**

- Title: "Position".
- Left area: `make_board()` with cell indices shown (`MUTED_COLOR`, font size 22).
- Row labels "row 0", "row 1", "row 2" to the left of the board, font size 22, `MUTED_COLOR`. Column labels "col 0", "col 1", "col 2" above the board, same style.
- Right area: code panel with snippet **S-POSITION-CHECK** first. At `index_code`, replace it with **S-POSITION-INDEX**.
- A token `Position(1, 2)` in `TEXT_COLOR`, font size 28, below the board.
- A token `Position(5, 0)` in `TEXT_COLOR`, font size 28, below the board.
- A ghost cell for `Position(5, 0)`: a dashed square (side 1.2, `ERROR_COLOR`) placed where row 5, column 0 would be. If it does not fit in the frame, put it just below the board (row 3 place) with the text "row 5" in `ERROR_COLOR` and a downward `Arrow`.
- Error label: `InvalidPositionError: invalid position (5, 0)`.
- Formula text: `1 × 3 + 2 = 5`, font size 32, `TEXT_COLOR`, below the board.

**Animation steps**

1. Before `code`: show the title, the board, the indices, and the row and column labels.
2. `code`: `FadeIn` the **S-POSITION-CHECK** code panel. Put a `RULE_COLOR` `SurroundingRectangle` around the line `        if not 0 <= self.row < SIZE or not 0 <= self.column < SIZE:`.
3. `good`: `FadeIn` the token `Position(1, 2)`. Fill cell 5 with `TEXT_COLOR` at opacity 0.3. `Indicate` the "row 1" and "col 2" labels.
4. `bad`: `FadeOut` the `Position(1, 2)` token. Remove the fill of cell 5. `FadeIn` the token `Position(5, 0)`. `Create` the dashed ghost cell and its arrow.
5. `reject`: do the rejection animation on the token and the ghost cell. Show the error label below the board. Put an `ERROR_COLOR` rectangle around the line `            raise InvalidPositionError(self.row, self.column)`.
6. `index_code`: `FadeOut` the error label and the rectangle. `Transform` the code panel into the **S-POSITION-INDEX** code panel. Put a `TEXT_COLOR` rectangle around `        return self.row * SIZE + self.column`.
7. `index_example`: fill cell 5 with `TEXT_COLOR` at opacity 0.3. `Write` the formula text `1 × 3 + 2 = 5` below the board. `Indicate` the index label "5" in the cell.
8. `from_index`: move the rectangle to the `from_index` lines. Draw an `Arrow` from the index label "5" to the labels "row 1" and "col 2" (two arrows, `TEXT_COLOR`).
9. End: hold for 1 second.

**Accuracy notes**

- `SIZE` is 3. The check is `0 <= row < 3` and `0 <= column < 3`.
- The exact error message for `Position(5, 0)` is `invalid position (5, 0)`.
- `Position(1, 2).index` is 5. `Position.from_index(5)` is `Position(row=1, column=2)`.
- `from_index` also checks its input: `Position.from_index(9)` raises `InvalidPositionError` with the message `invalid position (3, 0)`. The narration does not say this. Do not add it.

---

### E1S6: Cell and Board

- **Scene ID:** E1S6
- **Class name:** `E1S6CellAndBoard`
- **Target duration:** 60 seconds (about 135 words)

**Narration**

Block 1:
> A Cell holds one Player, or None when the cell is empty. <bookmark mark='cell_code'/>Cell has no post init check of its own. It uses the Player type, and a real Player can only be X or O.

Block 2:
> <bookmark mark='board_code'/>A Board is a tuple of cells. The Board has one invariant: the tuple must have exactly nine cells. <bookmark mark='bad'/>Now we try to make a Board with eight cells. <bookmark mark='reject'/>The check fails. Python raises Invalid Board Error.

Block 3:
> <bookmark mark='empty'/>The method empty makes the start board. It has nine cells, and each cell holds None.

Block 4:
> <bookmark mark='limits'/>Be careful here. The Board checks only the number of cells. It does not count turns. A board with nine X marks passes the check. <bookmark mark='game_guard'/>The Game object prevents such a board in play, because Game gives the turns to X and O in order.

**Visuals**

- Title: "Cell and Board".
- Right area: code panel with snippet **S-CELL** first. At `board_code`, replace it with **S-BOARD**.
- Left area, for `cell_code`: three single cells in a row at y = 0.5 (squares, side 1.2, stroke `TEXT_COLOR`, 0.4 units apart). Cell 1 is empty with the label `Cell(None)` below it. Cell 2 has an X mark with the label `Cell(X)`. Cell 3 has an O mark with the label `Cell(O)`. Labels are font size 22, `MUTED_COLOR`.
- Left area, for `board_code` and `bad`: a row of 8 small squares (side 0.55, 0.08 units apart), centered at (−3.6, 0.8), stroke `TEXT_COLOR`. A counter text "8 cells" below the row, font size 28.
- Error label: `InvalidBoardError: a board must have exactly 9 cells`, font size 22 (fit it inside the left half).
- Left area, for `empty`: `make_board()` with nine empty cells. Label `Board.empty()` below it, font size 26.
- Left area, for `limits`: `make_board()` with an X mark in all nine cells. Do not use green here (green means event or reward). Use the text `len(cells) == 9  ✓` in `RULE_COLOR`, font size 26, below the board.
- For `game_guard`: the text "Game gives turns: X, O, X, O …" in `TEXT_COLOR`, font size 26, below the `RULE_COLOR` text.

**Animation steps**

1. Before `cell_code`: show the title. `FadeIn` the three single cells and their labels.
2. `cell_code`: `FadeIn` the **S-CELL** code panel. Put a `TEXT_COLOR` rectangle around `    player: Player | None`.
3. `board_code`: `FadeOut` the three single cells. `Transform` the code panel into **S-BOARD**. Put a `RULE_COLOR` rectangle around the two lines `        if len(self.cells) != SIZE * SIZE:` and `            raise InvalidBoardError()`.
4. `bad`: `FadeIn` the row of 8 small squares, one by one (lag ratio 0.1). `Write` the "8 cells" counter.
5. `reject`: do the rejection animation on the row of squares and the counter. Show the error label. Change the code rectangle color to `ERROR_COLOR`.
6. `empty`: `FadeOut` the error label. Change the code rectangle to `TEXT_COLOR` and move it to the `empty` method lines. `Create` the empty board in the left area. `Write` the label `Board.empty()`.
7. `limits`: `FadeOut` the label. Put an X mark (`X_COLOR`) in all nine cells, fast (lag ratio 0.05). `Write` the text `len(cells) == 9  ✓` below the board. Move the code rectangle back to the `len(self.cells)` line, color `RULE_COLOR`.
8. `game_guard`: `Write` the "Game gives turns" text. Then change the nine X marks to opacity 0.3.
9. End: hold for 1 second.

**Accuracy notes**

- `Board` has exactly one invariant in `__post_init__`: `len(self.cells) != SIZE * SIZE` raises `InvalidBoardError`. Do not add other invariants. The Board does not check turn order, mark counts, or the type of each cell.
- `Cell` has no `__post_init__`. The narration must not say that `Cell` checks its value.
- The message is exactly `a board must have exactly 9 cells`.
- A `Board` of nine `Cell(X)` is accepted by the constructor. This was checked by a run.
- `Board.empty()` makes nine `Cell(None)`.

---

### E1S7: The Board answers questions

- **Scene ID:** E1S7
- **Class name:** `E1S7BoardQueries`
- **Target duration:** 50 seconds (about 115 words)

**Narration**

Block 1:
> The Board also answers questions about itself. <bookmark mark='with_mark'/>The method with mark puts a player's mark in one cell. <bookmark mark='guard'/>First, it checks that the cell is empty.

Block 2:
> <bookmark mark='occupied'/>Here, the center cell already holds an X. We try to put an O there. <bookmark mark='reject'/>The cell is occupied, so the Board raises Position Occupied Error. The board does not change.

Block 3:
> <bookmark mark='winning_line'/>The method winning line checks the eight lines for one player. It gives back the three positions of a line, or None. <bookmark mark='is_full'/>The method is full tells if all nine cells hold a mark.

Block 4:
> <bookmark mark='why'/>These rules are part of the Board. Other code asks the Board. It does not keep its own copy of the rules.

**Visuals**

- Title: "The Board answers questions".
- Left area: `make_board()` with an X mark in cell 4.
- Right area: code panel with **S-WITH-MARK**. At `winning_line`, replace it with **S-WINNING-LINE**. At `is_full`, replace it with **S-IS-FULL**.
- The O mark that tries to enter: `make_o()` in `O_COLOR`, first at (−3.6, 2.6) above the board.
- Error label: `PositionOccupiedError: cell (1, 1) is already occupied`, font size 22, below the board.
- For `winning_line`: a second board state in the left area: X in cells 0, 4, 8, O in cells 1, 2. A `Line` from cell 0 to cell 8 in `X_COLOR`, stroke width 8. A result text `(Position(0, 0), Position(1, 1), Position(2, 2))`, font size 20, below the board.
- For `is_full`: a result text `False` below the board, `NEUTRAL_COLOR`, font size 28.
- For `why`: three small grey labels on the left edge of the left area, stacked: "strategies", "learners", "demo printer", each with an `Arrow` (`MUTED_COLOR`) that points to the board.

**Animation steps**

1. Before `with_mark`: show the title and the board with X in cell 4.
2. `with_mark`: `FadeIn` the **S-WITH-MARK** code panel.
3. `guard`: put a `RULE_COLOR` rectangle around the lines `        if self.is_occupied(position):` and `            raise PositionOccupiedError(position.row, position.column)`.
4. `occupied`: `FadeIn` the O mark above the board. Move it down to cell 4 (1 second). Stop when it overlaps the X.
5. `reject`: do the rejection animation on the O mark. Show the error label. Change the code rectangle to `ERROR_COLOR`. `Indicate` the X mark in cell 4 (it stays).
6. `winning_line`: `FadeOut` the error label. `Transform` the code panel into **S-WINNING-LINE**. Add marks to the board: X in 0 and 8, O in 1 and 2. `Create` the line from cell 0 to cell 8. `Write` the result text below the board.
7. `is_full`: `Transform` the code panel into **S-IS-FULL**. `FadeOut` the line and the result text. Fill the four empty cells (3, 5, 6, 7) with `MUTED_COLOR` at opacity 0.3 for 1 second, then remove the fill. `Write` the result text `False`.
8. `why`: `FadeOut` the result text. `FadeIn` the three grey labels and their arrows.
9. End: hold for 1 second.

**Accuracy notes**

- The message is exactly `cell (1, 1) is already occupied`. The center cell is `Position(1, 1)`, index 4.
- `winning_line` returns a tuple of three `Position` objects, or `None`. For X in 0, 4, 8 it returns `(Position(0, 0), Position(1, 1), Position(2, 2))`.
- `is_full` returns `True` only when all nine cells hold a player.
- In the state for `is_full`, five cells hold a mark and four cells are empty, so the result is `False`.
- `with_mark` does not change the old board. Scene E1S11 shows this. Do not show the copy step here.

---

### E1S8: A family of errors

- **Scene ID:** E1S8
- **Class name:** `E1S8ErrorFamily`
- **Target duration:** 30 seconds (about 72 words)

**Narration**

Block 1:
> Each broken rule has its own error class. <bookmark mark='base'/>All of them come from one base class, Domain Error.

Block 2:
> <bookmark mark='seen'/>We saw four of them: Invalid Player Error, Invalid Position Error, Invalid Board Error, and Position Occupied Error. <bookmark mark='game_over'/>Game uses a fifth, Game Already Over Error. <bookmark mark='engine'/>Video two uses the last two.

Block 3:
> <bookmark mark='no_imports'/>The file errors dot py imports nothing from the other domain files. Each error takes only simple values, like text and numbers.

**Visuals**

- Title: "One base class: DomainError".
- Left area: a tree. Root box at (−3.6, 2.2): `DomainError`, `RoundedRectangle` with stroke `ERROR_COLOR`, font size 26. Seven child boxes below, in two columns (4 on the left at x = −5.2, 3 on the right at x = −2.0), from y = 1.0 down, 0.75 units apart. Font size 20. Each child box has a thin `MUTED_COLOR` `Line` to the root.
  - Left column: `InvalidPlayerError`, `InvalidPositionError`, `InvalidBoardError`, `PositionOccupiedError`
  - Right column: `GameAlreadyOverError`, `GameNotFoundError`, `GameAlreadyExistsError`
- Child box stroke: `ERROR_COLOR` at opacity 1.0 when highlighted, `MUTED_COLOR` otherwise.
- Tag texts, font size 18, `MUTED_COLOR`, to the right of the right-column boxes: "Game" next to `GameAlreadyOverError`; "video 2" next to the two last boxes.
- Right area: code panel with **S-ERRORS**.
- For `no_imports`: a text `import` with a red `Cross` over it, at (3.4, −3.2), font size 28. The text is `TEXT_COLOR`; the cross is `ERROR_COLOR`.

**Animation steps**

1. Before `base`: show the title. `FadeIn` the code panel.
2. `base`: `Create` the root box. Put a `TEXT_COLOR` rectangle around `class DomainError(Exception):`.
3. `seen`: `FadeIn` the four left-column boxes with their lines, one by one. Set their stroke to `ERROR_COLOR`.
4. `game_over`: `FadeIn` the box `GameAlreadyOverError` with its line and the tag "Game".
5. `engine`: `FadeIn` the boxes `GameNotFoundError` and `GameAlreadyExistsError` with their lines, stroke `MUTED_COLOR`, and the tag "video 2".
6. `no_imports`: move the code rectangle to cover the whole panel, color `MUTED_COLOR`. `FadeIn` the `import` text and `Create` the cross.
7. End: hold for 1 second.

**Accuracy notes**

- There are exactly 7 subclasses of `DomainError`. Their names are in the visuals list.
- `GameNotFoundError` and `GameAlreadyExistsError` are for the `GameEngine`. Do not explain the engine here.
- `errors.py` has no import statements at all. Its constructor parameters are `str` and `int` values. This prevents import cycles.
- `FrozenInstanceError` (scene E1S11) is not a `DomainError`. It comes from the Python `dataclasses` module. Do not put it in this tree.

---

### E1S9: The Game aggregate

- **Scene ID:** E1S9
- **Class name:** `E1S9GameAggregate`
- **Target duration:** 60 seconds (about 135 words)

**Narration**

Block 1:
> Now the data is safe. Next, we need the rules that change it. <bookmark mark='fields'/>The Game aggregate has four fields: an id, a board, the current player, and a status.

Block 2:
> <bookmark mark='status'/>Game Status is an enum with four values: in progress, X won, O won, and draw. <bookmark mark='one_place'/>Game is the one place where the rules of play live. Only the methods of Game make a new Game.

Block 3:
> <bookmark mark='start_code'/>The method start makes a new game. <bookmark mark='start_values'/>It uses an empty board. It sets the current player to X. It sets the status to in progress.

Block 4:
> <bookmark mark='transition'/>But start does not give back a Game. It gives back a Transition. <bookmark mark='transition_fields'/>A Transition holds two things: the next Game, and a list of what happened. Here, the list has one item: Game Started. Video two tells more about these items.

**Visuals**

- Title: "Game: the aggregate".
- Left area: a "Game card". A `RoundedRectangle` 5.4 wide and 3.6 high at (−3.6, 0.3), stroke `TEXT_COLOR`. Header "Game" in bold, font size 32. Four rows inside, font size 24:
  - `id: "g1"`
  - `board:` followed by a small board (`make_board()` scaled to 0.35)
  - `current_player:` followed by an X mark (scaled to 0.3, `X_COLOR`)
  - `status: IN_PROGRESS`
- Status chips for `status`: four small rounded rectangles in a row under the Game card, at y = −2.4, font size 20: `IN_PROGRESS` (`TEXT_COLOR`), `X_WON` (`X_COLOR`), `O_WON` (`O_COLOR`), `DRAW` (`NEUTRAL_COLOR`).
- Right area: code panel with **S-GAME-FIELDS**. At `status`, replace it with **S-GAME-STATUS**. At `start_code`, replace it with **S-GAME-START**. At `transition_fields`, replace it with **S-TRANSITION**.
- For `one_place`: a `RULE_COLOR` rounded rectangle around the Game card with the label "rules of play" in `RULE_COLOR`, font size 24, above the card.
- For `transition`: a "Transition box": a larger `RoundedRectangle` (6.4 wide, 5.6 high) at (−3.6, −0.3), stroke `TEXT_COLOR`, dashed, with the label "Transition" at the top. The Game card moves inside it (scale 0.8, upper part). An event card below the Game card, inside the box: `make_event_card("GameStarted", ["game_id: g1"])`, `EVENT_COLOR`.

**Animation steps**

1. Before `fields`: show the title.
2. `fields`: `FadeIn` the **S-GAME-FIELDS** code panel. `Create` the Game card outline and header. `FadeIn` the four rows one by one, while a `TEXT_COLOR` rectangle moves over the matching field lines in the code (`    id: str`, `    board: Board`, `    current_player: Player`, `    status: GameStatus`).
3. `status`: `Transform` the code panel into **S-GAME-STATUS**. `FadeIn` the four status chips.
4. `one_place`: `FadeOut` the status chips. `Create` the `RULE_COLOR` rectangle and label around the Game card.
5. `start_code`: `FadeOut` the rule rectangle and label. `Transform` the code panel into **S-GAME-START**.
6. `start_values`: put a `TEXT_COLOR` rectangle in the code around `            board=Board.empty(),`, then `            current_player=X,`, then `            status=GameStatus.IN_PROGRESS,` (0.8 seconds each). At each rectangle, `Indicate` the matching row of the Game card.
7. `transition`: `Create` the dashed Transition box. Scale the Game card to 0.8 and move it into the upper part of the box. Put a `TEXT_COLOR` rectangle around `        return Transition(game, (GameStarted(game_id),))`.
8. `transition_fields`: `Transform` the code panel into **S-TRANSITION**. `FadeIn` the `GameStarted` event card below the Game card, inside the box. Put an `EVENT_COLOR` rectangle around `    events: tuple[DomainEvent, ...]`.
9. End: hold for 1 second.

**Accuracy notes**

- `Game` has exactly four fields, in this order: `id`, `board`, `current_player`, `status`.
- `GameStatus` has exactly four values: `IN_PROGRESS`, `X_WON`, `O_WON`, `DRAW`. `GameStatus` is an `Enum`, not a dataclass.
- `Game.start` returns a `Transition`, not a `Game`. X always starts.
- `Game` has no `__post_init__`. Do not say that `Game` checks invariants in `__post_init__`. `Game` enforces its rules in `place_mark`.
- In the source code, only `Game.start` and `Game.place_mark` make `Game` objects. Python does not block other code from a call to the `Game` constructor; the project follows this rule by design. The narration "Only the methods of Game make a new Game" describes the project code. Do not say that Python enforces it.
- The game id `g1` is an example. The demo uses a `uuid`.
- The `events` field is a `tuple`. The narration calls it "a list of what happened".

---

### E1S10: Place a mark

- **Scene ID:** E1S10
- **Class name:** `E1S10PlaceMark`
- **Target duration:** 75 seconds (about 170 words)

**Narration**

Block 1:
> The method place mark applies one move. We read it in three parts. <bookmark mark='guards'/>Part one has two guards. First, the game must be in progress. Second, the cell must be empty. <bookmark mark='marked'/>Then Game asks the Board for a marked board. Game also asks if the current player now has a line.

Block 2:
> <bookmark mark='example'/>Here is a real game from the demo. X has cells 0, 1, and 3. O has cells 2 and 4. Now O plays cell 6.

Block 3:
> <bookmark mark='win_code'/>Part two is the win branch. <bookmark mark='win_line'/>Cells 2, 4, and 6 make a diagonal line for O. The new Game gets the status O won. <bookmark mark='win_events'/>The list of what happened has two items: Mark Placed and Game Won.

Block 4:
> <bookmark mark='rest_code'/>Part three has two more branches. If the board is full and there is no line, the status is draw. <bookmark mark='continue'/>If not, the game continues. The new Game gives the turn to the opponent.

Block 5:
> <bookmark mark='over'/>Our game is over now. We try to play cell 8. <bookmark mark='reject'/>The first guard fails. Game raises Game Already Over Error.

**Visuals**

- Title: "Game.place_mark".
- Left area: `make_board()` scaled to 0.8, center at (−3.6, 0.6). Cell indices shown.
- Start marks (demo board before the last move): X (`X_COLOR`) in cells 0, 1, 3; O (`O_COLOR`) in cells 2, 4.
- Status text under the board at (−3.6, −1.6): `status: IN_PROGRESS`, font size 24, `TEXT_COLOR`. It changes to `status: O_WON` in `O_COLOR`.
- Turn text under the status text at (−3.6, −2.1): `current_player: O`, font size 24, `O_COLOR`.
- Event cards at (−3.6, −3.0), side by side, scale so both fit in the left half: `make_event_card("MarkPlaced", ["player: O", "position: (2, 0)"])` and `make_event_card("GameWon", ["winner: O", "line: 2, 4, 6"])`, `EVENT_COLOR`.
- Right area: code panel with **S-PLACE-MARK-GUARDS**. At `win_code`, replace it with **S-PLACE-MARK-WIN**. At `rest_code`, replace it with **S-PLACE-MARK-REST**. At `over`, replace it with **S-PLACE-MARK-GUARDS** again.
- Winning line: a `Line` from the center of cell 2 to the center of cell 6, `O_COLOR`, stroke width 8.
- Try mark for `over`: an X mark (`X_COLOR`) above cell 8, at (−2.6, 2.8).
- Error label: `GameAlreadyOverError: game g1 is already over`, font size 22, `ERROR_COLOR`. It replaces the event cards at (−3.6, −3.0).

**Animation steps**

1. Before `guards`: show the title. `FadeIn` the **S-PLACE-MARK-GUARDS** code panel.
2. `guards`: put a `RULE_COLOR` rectangle around the two lines `        if self.status is not GameStatus.IN_PROGRESS:` and `            raise GameAlreadyOverError(self.id)`. After 2 seconds, move it to the two lines `        if self.board.is_occupied(position):` and `            raise PositionOccupiedError(position.row, position.column)`.
3. `marked`: move the rectangle to the two lines that start with `        marked_board =` and `        line =`. Change its color to `TEXT_COLOR`.
4. `example`: `FadeIn` the board with the start marks, the status text, and the turn text. Then `FadeIn` an O mark above cell 6 and move it down into cell 6 (1 second).
5. `win_code`: `Transform` the code panel into **S-PLACE-MARK-WIN**. Put a `TEXT_COLOR` rectangle around `        if line is not None:`.
6. `win_line`: `Create` the winning line from cell 2 to cell 6. Move the rectangle to the lines `            status = GameStatus.X_WON if self.current_player == X else GameStatus.O_WON` and `            game = Game(self.id, marked_board, self.current_player, status)`. `Transform` the status text into `status: O_WON` in `O_COLOR`.
7. `win_events`: move the rectangle to the two event lines (`MarkPlaced(...)` and `GameWon(...)`) and change its color to `EVENT_COLOR`. `FadeIn` the two event cards, first `MarkPlaced`, then `GameWon`.
8. `rest_code`: `Transform` the code panel into **S-PLACE-MARK-REST**. Put a `NEUTRAL_COLOR` rectangle around the first 7 lines (the `is_full` branch).
9. `continue`: move the rectangle to the last 3 lines and change its color to `TEXT_COLOR`. Put a small `TEXT_COLOR` rectangle around `self.current_player.opponent` if the code mobject lets you select part of a line; if not, keep the rectangle around the whole line.
10. `over`: `Transform` the code panel back into **S-PLACE-MARK-GUARDS**. `FadeIn` the try mark (X) above cell 8. Move it down toward cell 8 (0.8 seconds).
11. `reject`: do the rejection animation on the try mark. `FadeOut` the event cards. Show the error label in their place. Put an `ERROR_COLOR` rectangle around the lines `        if self.status is not GameStatus.IN_PROGRESS:` and `            raise GameAlreadyOverError(self.id)`.
12. End: hold for 1 second.

**Accuracy notes**

- The demo game moves are: X 0, O 4, X 1, O 2, X 3, O 6. O wins on `(2, 4, 6)`. Final status `O_WON`. Checked in `/tmp/ttt_main_output.txt` and by a run.
- Cell 6 is `Position(2, 0)`. The `MarkPlaced` event for the last move has `player` O and `position` `Position(row=2, column=0)`.
- The `GameWon` event has `winner` O and `winning_line` `(Position(0, 2), Position(1, 1), Position(2, 0))`, which is cells 2, 4, 6. The event card text "line: 2, 4, 6" uses cell indices for a simple screen.
- In a win, the new `Game` keeps `current_player` as the winner (O). The turn does not pass. Do not change the turn text in steps 6 and 7.
- Order of checks in `place_mark`: first the status guard, then the occupied guard, then `with_mark`, then `winning_line`, then `is_full`. A win is checked before a draw. So a move that fills the board and makes a line gives a win, not a draw.
- Continue branch: the new `Game` has `current_player.opponent` and status `IN_PROGRESS`, with one event, `MarkPlaced`.
- Draw branch: status `DRAW`, events `MarkPlaced` and `GameDrawn`. The narration does not name `GameDrawn`; the code panel shows it.
- The error message is exactly `game g1 is already over`.
- Do not explain what the events do. Video 2 explains them.

---

### E1S11: Nothing changes in place

- **Scene ID:** E1S11
- **Class name:** `E1S11Immutability`
- **Target duration:** 65 seconds (about 151 words)

**Narration**

Block 1:
> Look again at the method with mark. It does not change the board. <bookmark mark='old'/>Here is a board with an X in cell 0. <bookmark mark='call'/>We call with mark for cell 4 and player O.

Block 2:
> <bookmark mark='copy'/>The method copies the cells, puts an O in cell 4, and makes a new Board. <bookmark mark='compare'/>The old board still has only one mark. The new board has two marks.

Block 3:
> <bookmark mark='frozen'/>Frozen dataclasses make this a rule. If code tries to set a field, Python raises Frozen Instance Error. <bookmark mark='game'/>The method place mark works the same way. Each branch makes a new Game. The old Game does not change.

Block 4:
> <bookmark mark='history'/>This has three good results. First, a game history is simply a list of Game objects. <bookmark mark='readers'/>Second, code can read an old board at any time, and the board stays the same. <bookmark mark='keys'/>Third, a frozen Board can be a dictionary key. The learners in videos five and six use this.

**Visuals**

- Title: "Nothing changes in place".
- Left area, old board: `make_board()` scaled to 0.7 at (−4.8, 0.6). X in cell 0. Label "old board" below it, font size 24, `MUTED_COLOR`.
- New board (appears at `copy`): `make_board()` scaled to 0.7 at (−1.6, 0.6). X in cell 0 and O in cell 4. Label "new board" below it, font size 24, `TEXT_COLOR`.
- An `Arrow` from the old board to the new board, `TEXT_COLOR`, with the label `with_mark(Position(1, 1), O)` above it, font size 20.
- Right area: code panel with **S-WITH-MARK**.
- For `frozen`: a text `old.cells = ()` in `TEXT_COLOR`, font size 26, at (−3.2, −2.0). Error label `FrozenInstanceError: cannot assign to field 'cells'`, font size 22, `ERROR_COLOR`, under it.
- For `game`: replace the two boards with two small Game cards (as in E1S9, scale 0.6) at the same positions, labels "old Game" and "new Game", and an arrow with the label `place_mark(...)`.
- For `history`: a horizontal "film strip" at y = 0.5 across the full width: five small boards (scale 0.35), 2.6 units apart, from x = −5.2 to x = 5.2. They show the demo game from E1S10 after moves 1, 2, 3, 4, 5: (X0), (X0, O4), (X0, O4, X1), (X0, O4, X1, O2), (X0, O4, X1, O2, X3). Put the code panel away (`FadeOut`) before this step.
- For `readers`: an eye symbol is not required. Use the text "read at any time" in `TEXT_COLOR`, font size 24, under the first board of the film strip, and `Indicate` that board.
- For `keys`: a dictionary drawing at (0, −2.4): the text `{ board: 0.5 }`, font size 32, where `board` is replaced by a small board image (scale 0.3) with X in cell 0 and O in cell 4. The value `0.5` is in `NEUTRAL_COLOR`.

**Animation steps**

1. Before `old`: show the title. `FadeIn` the **S-WITH-MARK** code panel.
2. `old`: `Create` the old board with X in cell 0 and its label.
3. `call`: `GrowArrow` the arrow toward the right. `Write` the arrow label.
4. `copy`: put a `TEXT_COLOR` rectangle around `        cells = list(self.cells)`. Make a copy of the old board (`old_board.copy()`) and move the copy to the new board position (1 second). Move the rectangle to `        cells[position.index] = Cell(player)`. Draw the O mark in cell 4 of the new board. Move the rectangle to `        return Board(tuple(cells))`. `Write` the "new board" label.
5. `compare`: `Indicate` cell 4 of the old board (it is still empty). Then `Indicate` cell 4 of the new board.
6. `frozen`: `Write` the text `old.cells = ()`. Do the rejection animation on this text. Show the `FrozenInstanceError` label.
7. `game`: `FadeOut` the error label, the boards, the arrow, and the labels. `FadeIn` the two small Game cards with their arrow and labels.
8. `history`: `FadeOut` the Game cards, the arrow, and the code panel. `FadeIn` the five film strip boards from left to right (lag ratio 0.2).
9. `readers`: `Write` the text "read at any time" under the first film strip board. `Indicate` the first board.
10. `keys`: `FadeIn` the dictionary drawing.
11. End: hold for 1 second.

**Accuracy notes**

- `with_mark` makes a list from `self.cells`, changes one item in the list, and returns `Board(tuple(cells))`. The old board is not changed. Checked by a run: after `new = old.with_mark(Position(1, 1), X)`, `old` is still empty.
- Cell 4 is `Position(1, 1)`.
- The exact message is `cannot assign to field 'cells'`. `FrozenInstanceError` comes from `dataclasses`. It is not a `DomainError`.
- Every branch of `place_mark` makes a new `Game` with `Game(...)`.
- The value `0.5` in the dictionary drawing is only an example value. Do not say that it is a real learned value.
- `PolicyLearner` (video 5) and `NeuralPolicyLearner` (video 6) each keep a `dict[Board, float]` value table. Do not explain the value table here.
- Do not say that immutability costs a lot of memory. For a nine-cell board, the cost is very small.

---

## 7. Closing and hook

### E1S12: Summary and next question

- **Scene ID:** E1S12
- **Class name:** `E1S12ClosingHook`
- **Target duration:** 30 seconds (about 67 words)

**Narration**

Block 1:
> Let us review. <bookmark mark='values'/>Value objects check their own invariants. Player, Position, and Board raise a Domain Error for a bad value. <bookmark mark='game'/>The Game aggregate keeps the rules of play. Each move gives a Transition. <bookmark mark='immutable'/>Nothing changes in place. Each move makes a new version.

Block 2:
> <bookmark mark='hook'/>Now we can hold a game. But how does a move request travel through the system? Video two shows how a move happens.

**Visuals**

- Title: "Summary".
- Three summary rows at the left side of the frame, x starting at −6.0, y = 1.8, 0.6, −0.6. Font size 30.
  1. A small `RULE_COLOR` square icon, then the text "Value objects check invariants"
  2. A small `TEXT_COLOR` square icon, then the text "Game keeps the rules → Transition"
  3. A small `MUTED_COLOR` square icon, then the text "A move makes a new version"
- Hook, at the bottom center (0, −2.4): the text "How does a move request travel through the system?", font size 34, `TEXT_COLOR`.
- Hook visual on the right (x = 4.0, y = −0.2): a command card `make_command_card("PlaceMark", ["position: ?"])` in `COMMAND_COLOR`, a `MUTED_COLOR` arrow to the right of it, and a question mark "?" in font size 60, `MUTED_COLOR`.
- Next title: "Next: How a Move Happens", font size 30, `MUTED_COLOR`, at the bottom edge.

**Animation steps**

1. Before `values`: show the title.
2. `values`: `FadeIn` row 1.
3. `game`: `FadeIn` row 2.
4. `immutable`: `FadeIn` row 3.
5. `hook`: change the three rows to opacity 0.4. `FadeIn` the command card, the arrow, and the question mark on the right. `Write` the hook text. Then `FadeIn` the next title at the bottom edge.
6. End: hold for 1.5 seconds.

**Accuracy notes**

- `PlaceMark` is a real command class in `commands.py` with the fields `game_id` and `position`. Video 2 explains it. This scene shows only its name and a `?` for the position. Do not explain it here.
- `Cell` is not in the list of value objects that raise a `DomainError`, because `Cell` has no check.

---

## 8. Checks

Answer each question with yes or no. Each "no" is a problem to record in `QUESTIONS.md`.

1. Does E1S1 show the question "Who decides the next move?" and all six titles exactly as in section 3?
2. Does E1S2 show exactly eight winning lines, in the order of `WINNING_LINES`, with index 0 at top left and index 8 at bottom right?
3. Is the draw position in E1S2 X in 0, 1, 5, 6, 8 and O in 2, 3, 4, 7?
4. Is every code panel an exact copy of its snippet in section 5.2, with no changed, added, or removed characters?
5. Is every code panel 15 lines or less and fully inside the right half of the frame?
6. Does E1S4 show `Player("Q")` in red, rejected, with the message `invalid player symbol 'Q'`?
7. Does E1S5 show `Position(5, 0)` rejected with the message `invalid position (5, 0)`, and `Position(1, 2).index` equal to 5?
8. Does E1S6 say that the `Board` has only one invariant (exactly nine cells) and not invent other `Board` invariants?
9. Does E1S6 avoid a claim that `Cell` checks its value?
10. Does E1S7 show the message `cell (1, 1) is already occupied` for an O on the X in the center cell?
11. Does E1S8 show exactly seven subclasses of `DomainError`, and not `FrozenInstanceError`?
12. Does E1S9 show four `Game` fields (`id`, `board`, `current_player`, `status`) and four `GameStatus` values?
13. Does E1S9 show that `Game.start` gives a `Transition` with one `GameStarted` event and `current_player` X?
14. Does E1S10 use the demo moves X 0, O 4, X 1, O 2, X 3, O 6, and show O win on cells 2, 4, 6 with the events `MarkPlaced` and `GameWon`?
15. In E1S10, does the turn text stay `current_player: O` after the win?
16. Does E1S10 show `GameAlreadyOverError` with the message `game g1 is already over` when a mark goes on a finished game?
17. Does E1S11 show the old board still with one mark while the new board has two marks?
18. Does E1S11 show `FrozenInstanceError` with the message `cannot assign to field 'cells'`?
19. Does the video describe events only as "a list of what happened", with no explanation of the event bus or handlers?
20. Does every color agree with the README color table (blue X, orange O, purple rules, red errors, green events, light blue commands)?
21. Does E1S12 end with the question "How does a move request travel through the system?" and name video 2?
22. Does the narration use the spoken forms in section 5.1, and does the screen show the exact code names?
23. Is every scene between 20 and 90 seconds, and is the total between 8 and 12 minutes?
