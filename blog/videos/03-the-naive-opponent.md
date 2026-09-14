# Episode 3: The Naive Opponent

## 1. Header

- **Title:** The Naive Opponent
- **Number:** 3 of 6
- **Target length:** 10 minutes 17 seconds (617 seconds, 12 scenes)
- **Source files:**
  - `src/tictactoe/strategies.py` (`Strategy`, `FirstAvailableStrategy`)
  - `src/tictactoe/value_objects.py` (`Position.from_index`, `Board.is_occupied`, `SIZE`)
  - `src/tictactoe/game.py` (`Game.place_mark` uses `self.current_player`)
  - `main.py` (`pick`, `run_match`, `main`)
- **Source article sections:** `blog/articles/02-writing-our-own-strategies.md`, from the start through the section "Show it loses".
- **Demo output:** the first match in the output of `uv run main.py` (`FirstAvailableStrategy (X) vs MinimaxStrategy (O)`).

## 2. Goal

After this video, the viewer can explain the `Strategy` seam: a strategy is one method, `choose_position(game) -> Position`. The viewer can explain that `Strategy` is a `typing.Protocol`, so any object with that method fits, with no inheritance. The viewer can explain that a strategy plays for `game.current_player`. The viewer can trace how `FirstAvailableStrategy` selects a cell. The viewer can show the exact move where it loses the demo match, and can tell why: it never looks for a win or a block, and it is fully predictable.

## 3. Recap from the last video

Maximum 20 seconds. Scene `E3S1` contains the recap. The recap has two facts:

1. Video 1 built the model: `Board`, `Game`, and the rules.
2. Video 2 showed the one-way flow: command → engine → game → events. The `GameEngine` accepts a `PlaceMark` command, but it does not choose the cell.

## 4. Terms

| Term | Definition |
|------|------------|
| `Strategy` | The protocol for an object that selects the next move with one method, `choose_position`. |
| `choose_position` | The one method of a strategy: it takes a `Game` and returns a `Position`. |
| `Protocol` | A class from the Python `typing` module that describes the methods an object must have. |
| Structural typing | A rule that says an object fits a type when it has the correct methods, not when it inherits from a base class. |
| Player-agnostic | A strategy that does not know its player; it plays for `game.current_player`. |
| `FirstAvailableStrategy` | The naive strategy: it returns the first free cell in index order, 0 to 8. |
| Stateless | An object that keeps no data between calls. |
| Predictable | The same board always gives the same move. |
| Baseline | A simple reference strategy; a better strategy must beat it. |
| Block | A move into the one free cell of a line where the opponent already has two marks. |

Use these names only. Do not say "interface", "bot", "AI", or "brain" for `Strategy`. Do not say "dumb strategy" in narration; say "naive strategy" or `FirstAvailableStrategy`.

## 5. Source facts

### 5.1 Code snippets

Copy these snippets exactly. Keep the indentation that the snippet shows.

**Snippet A: `Strategy`** (`src/tictactoe/strategies.py`, lines 2 and 8–9; the blank line between them is a cut)

```python
from typing import Protocol

class Strategy(Protocol):
    def choose_position(self, game: Game) -> Position: ...
```

**Snippet B: `FirstAvailableStrategy`** (`src/tictactoe/strategies.py`, lines 12–20, 9 lines)

```python
class FirstAvailableStrategy:
    def choose_position(self, game: Game) -> Position:
        board = game.board
        free = [
            Position.from_index(index)
            for index in range(SIZE * SIZE)
            if not board.is_occupied(Position.from_index(index))
        ]
        return free[0]
```

**Snippet C: two class headers** (`src/tictactoe/strategies.py`, line 12 and line 23)

```python
class FirstAvailableStrategy:

class MinimaxStrategy:
```

**Snippet D: `Position.from_index`** (`src/tictactoe/value_objects.py`, lines 57–61)

```python
    @classmethod
    def from_index(cls, index: int) -> "Position":
        if not 0 <= index < SIZE * SIZE:
            raise InvalidPositionError(index // SIZE, index % SIZE)
        return cls(index // SIZE, index % SIZE)
```

**Snippet E: `Board.is_occupied`** (`src/tictactoe/value_objects.py`, lines 91–92)

```python
    def is_occupied(self, position: Position) -> bool:
        return self.cell_at(position).player is not None
```

**Snippet F: the first match** (`main.py`, `main` function)

```python
    run_match(engine, FirstAvailableStrategy(), MinimaxStrategy())
```

**Snippet G: the match loop** (`main.py`, `run_match` function)

```python
    while game.status is GameStatus.IN_PROGRESS:
        position = pick(agents[game.current_player], game, explore)
        game = engine.place_mark(PlaceMark(game_id, position))
        print(game.board.render())
        print()
```

**Snippet H: `pick`** (`main.py`)

```python
def pick(agent: Strategy | PolicyLearner | NeuralPolicyLearner, game, explore: bool) -> Position:
    if isinstance(agent, (PolicyLearner, NeuralPolicyLearner)):
        return agent.choose_position(game, explore=explore)
    return agent.choose_position(game)
```

**Snippet I: the mark of the current player in `Game.place_mark`** (`src/tictactoe/game.py`, one line)

```python
        marked_board = self.board.with_mark(position, self.current_player)
```

### 5.2 Facts and numbers

- `SIZE = 3`, so `SIZE * SIZE` is 9. The cell indices are 0 to 8. Index 0 is top left. Index 8 is bottom right.
- `Position.from_index(index)` returns row `index // 3` and column `index % 3`. Example: index 5 is row 1, column 2.
- `FirstAvailableStrategy` checks all 9 indices. It does not stop at the first free cell. It builds the full list `free`, then returns `free[0]`.
- The list `free` holds `Position` objects. The screen shows each `Position` as its index number. Say "positions" or "cells", not "numbers".
- `FirstAvailableStrategy` has no `__init__` and no fields. It is stateless.
- `FirstAvailableStrategy` does not read `game.current_player`. `Game.place_mark` puts the mark of `self.current_player` (Snippet I).
- `Strategy` is not `@runtime_checkable`. Python does not check the protocol when the program runs. `isinstance(obj, Strategy)` raises a `TypeError`. A static type checker can check the fit. The project does not configure a type checker.
- In `main.py`, `FirstAvailableStrategy` plays X in the first match. In training, it plays O against the X `PolicyLearner`, and X against the O `PolicyLearner`.
- One call of `FirstAvailableStrategy.choose_position` on an empty board took about 67 microseconds on the machine that made this plan. Narration says only "a small part of a millisecond".

### 5.3 The real demo match: `FirstAvailableStrategy` (X) vs `MinimaxStrategy` (O)

The move order was checked with a Python replay of the two strategies on the `Game` aggregate. The replay gives the same boards as the demo output.

| Move | Player | Cell index | Cell name | Board after the move (indices 0–8, `.` is free) |
|------|--------|-----------|-----------|------|
| 1 | X | 0 | top left | `X . . / . . . / . . .` |
| 2 | O | 4 | center | `X . . / . O . / . . .` |
| 3 | X | 1 | top middle | `X X . / . O . / . . .` |
| 4 | O | 2 | top right | `X X O / . O . / . . .` |
| 5 | X | 3 | middle left | `X X O / X O . / . . .` |
| 6 | O | 6 | bottom left | `X X O / X O . / O . .` |

- After move 6, the status is `GameStatus.O_WON`. O wins on the diagonal 2, 4, 6.
- The events that the bus prints for move 6: `MarkPlaced`, then `GameWon`.
- The final board, as the demo prints it (trailing spaces removed):

```text
 X | X | O
---+---+---
 X | O |
---+---+---
 O |   |
```

- Both strategies are deterministic, so this match is the same on every run.

### 5.4 The missed block (checked with Python)

- Position before move 5: X in cells 0 and 1. O in cells 2 and 4. X to move. Free cells: 3, 5, 6, 7, 8.
- O threatens the diagonal 2, 4, 6. Cell 6 is the only free cell on it. A mark of X in cell 6 blocks it.
- X has no winning move in this position (the top row 0, 1, 2 has an O in cell 2).
- `FirstAvailableStrategy` builds `free = [3, 5, 6, 7, 8]` and returns cell 3.
- With perfect play by both players after move 5 (the `MinimaxStrategy._score` result for X):
  - X in cell 6: draw (score 0).
  - X in cell 3, 5, 7, or 8: X loses (score −10).
- Before move 3 (X in 0, O in 4), every free cell gives a draw with perfect play. Thus move 5 is the move that loses the game.
- After move 5, X has cells 0 and 3, so cell 6 also completes a line for X (0, 3, 6). O's move 6 blocks X and wins in the same move.

### 5.5 Exploitation number

- `main.py` trains a tabular O `PolicyLearner` against `FirstAvailableStrategy` for 6,000 episodes. The demo output line: `tabular O vs naive: won 5960, drew 11, lost 29`.
- Say "a learner in video five". Do not explain the learner in this video.

## 6. Scenes

### Layout constants for all scenes

- Background `#1E1E2E`. Main text `#E6E6E6`. Secondary text `#9A9AB0`.
- **Board position:** center of the board at `(-3.5, -0.3, 0)`. Cell side 1.2. Show cell indices in small grey text (`#9A9AB0`, font size 20) in the top-left corner of each cell when the scene says "indices on".
- **Code panel position:** right half. Center at `(3.3, 0, 0)`. Scale the panel so that its width is at most 6.2 units.
- **Title text:** top, `to_edge(UP, buff=0.4)`, font size 40, color `#E6E6E6`.
- **Caption text:** bottom, `to_edge(DOWN, buff=0.4)`, font size 28, color `#9A9AB0`.
- **Scan highlight:** a `Square(side_length=1.2)` with stroke `#E6E6E6`, stroke width 10, fill `#E6E6E6`, fill opacity 0.15. This is not a fixed-meaning color.
- **Line highlight in code:** a `SurroundingRectangle` around the code line, stroke `#E6E6E6`, stroke width 3, buff 0.05. If the code line has no separate mobject, use a rectangle with the width of the panel at the height of the line.
- **Free list text:** `Text("free = [ ]")` with font size 32, color `#E6E6E6`, below the board at `(-3.5, -2.6, 0)`. Each index added to the list uses `#E6E6E6`.
- X marks use `#4C9BE8`. O marks use `#F2A541`.

---

### Scene E3S1: Recap

- **Scene ID:** `E3S1`
- **Class name:** `E3S1Recap`
- **Target duration:** 18 seconds (narration: 36 words, about 15 seconds of speech; the rest is animation time)

#### Narration

Block 1:

> In video one, we built the model of the game. <bookmark mark='model'/> In video two, a move went one way: command, engine, game, events. <bookmark mark='engine'/> The engine accepts a PlaceMark command. But the engine does not choose the cell.

#### Visuals

- Left: an empty board at the board position, indices off.
- Right: a horizontal flow of four boxes at `y = 0`, from `x = 0.2` to `x = 6.2`: "command" (stroke `#61AFEF`), "engine" (stroke `#E6E6E6`), "game" (stroke `#C678DD`), "events" (stroke `#98C379`). Arrows between them in `#9A9AB0`. Box width 1.3, height 0.8, font size 24.
- Later: a command card `PlaceMark` (color `#61AFEF`) with the field `position` above the "command" box, at `(0.9, 1.5, 0)`.
- Later: a grey question mark `?` (font size 72, `#9A9AB0`) above the board at `(-3.5, 2.4, 0)`.

#### Animation steps

1. Start of block: `Create` the empty board (1 second).
2. `model`: `FadeIn` the four flow boxes and arrows, left to right, with `LaggedStart` (2 seconds).
3. `engine`: `FadeIn` the `PlaceMark` card. Then `Indicate` the "engine" box. Then `Write` the `?` above the board.
4. End of block: `FadeOut` all objects.

#### Accuracy notes

- The flow order is command → engine → game → events. Do not add the event bus as a separate box in this recap.
- Say "engine", not "game engine class" or "server".

---

### Scene E3S2: The empty seat

- **Scene ID:** `E3S2`
- **Class name:** `E3S2EmptySeat`
- **Target duration:** 55 seconds (narration: 119 words, about 51 seconds of speech; the rest is animation time)

#### Narration

Block 1:

> Look at the match loop in main dot py. <bookmark mark='loop'/> The game knows whose turn it is. It knows which cells are free. It knows when the game ends. <bookmark mark='pick'/> But one line asks something else for the move. That line calls pick.

Block 2:

> <bookmark mark='question'/> So, who decides the next move? This video puts the first answer in that seat. <bookmark mark='seam'/> The seat has a name: Strategy. <bookmark mark='method'/> A strategy is one method. Its name is choose position. It takes a Game. It gives back a Position.

Block 3:

> <bookmark mark='arrow'/> The game goes in. One cell comes out. Then the engine places the mark on that cell. <bookmark mark='nothing'/> A strategy does nothing more. It does not change the game, and it does not know the rules of a win.

#### Visuals

- Title (top): "Who decides the next move?" Hidden until `question`.
- Right: code panel with Snippet G (`run_match` loop).
- Left, from `seam`: code panel with Snippet A, scaled to width 5.5, center at `(-3.3, 1.5, 0)`.
- Left, from `arrow`: a diagram at `y = -1.5`: a small board icon (side 0.4 per cell) labeled "Game" at `x = -5.8`, an arrow to a box labeled `choose_position` (stroke `#E6E6E6`, width 2.6, height 0.8) at `x = -3.3`, an arrow to a single highlighted cell (one square, side 0.6, scan highlight style) labeled "Position" at `x = -0.9`.

#### Animation steps

1. `loop`: `FadeIn` the Snippet G code panel on the right.
2. `loop` (continued, while the narration lists the three facts): highlight the line `while game.status is GameStatus.IN_PROGRESS:`.
3. `pick`: move the highlight to the line `position = pick(agents[game.current_player], game, explore)`. `Indicate` the word `pick` area.
4. `question`: `Write` the title.
5. `seam`: `FadeIn` Snippet A on the left.
6. `method`: highlight the line `def choose_position(self, game: Game) -> Position: ...`.
7. `arrow`: `FadeOut` Snippet G. `Create` the diagram from left to right: "Game", arrow, `choose_position` box, arrow, "Position" (3 seconds).
8. `nothing`: `Indicate` the `choose_position` box. End of block: `FadeOut` all objects.

#### Accuracy notes

- `pick` is a function in `main.py`, not part of the `tictactoe` package.
- The `Strategy` protocol has exactly one method. Do not show other methods.
- In narration, "choose position" is the spoken form of `choose_position`. On screen, always write `choose_position`.
- The engine places the mark; the strategy only returns a `Position`.

---

### Scene E3S3: What a Protocol is

- **Scene ID:** `E3S3`
- **Class name:** `E3S3Protocol`
- **Target duration:** 62 seconds (narration: 137 words, about 59 seconds of speech; the rest is animation time)

#### Narration

Block 1:

> The Strategy class is a Protocol. Protocol comes from the typing module of Python. <bookmark mark='shape'/> A Protocol describes a shape. Any object with a choose position method fits, if the method takes a Game and gives back a Position.

Block 2:

> <bookmark mark='classes'/> Look at the two strategies in the first match. FirstAvailableStrategy has no base class. MinimaxStrategy has no base class. <bookmark mark='noinherit'/> Neither one inherits from Strategy. Both fit, because both have the method.

Block 3:

> <bookmark mark='socket'/> Think of a wall socket. The socket does not ask who made the plug. It only needs prongs of the correct shape. <bookmark mark='name'/> This idea has a name: structural typing. The methods of the object decide the fit, not its parent class.

Block 4:

> <bookmark mark='runtime'/> Python does not check a Protocol when the program runs. The code simply calls the method. A type checker can check the fit before the program runs.

#### Visuals

- Right: code panel with Snippet A, center `(3.3, 1.5, 0)`.
- Right, from `classes`: code panel with Snippet C, center `(3.3, -1.3, 0)`.
- Left, from `socket`: a socket diagram centered at `(-3.5, 0, 0)`:
  - A tall rectangle (width 2.4, height 3.0, stroke `#E6E6E6`, stroke width 4) labeled `Strategy` at its top (font size 28).
  - Inside it, a slot: a smaller rectangle (width 1.8, height 0.6, stroke `#9A9AB0`) labeled `choose_position` (font size 20).
  - Two plug cards at the left of the frame, at `(-6.0, 1.0, 0)` and `(-6.0, -1.0, 0)`: rounded rectangles (width 2.8, height 0.7, stroke `#E6E6E6`, fill opacity 0) labeled `FirstAvailableStrategy` and `MinimaxStrategy` (font size 20). Each plug has a small tab at its right edge labeled `choose_position` (font size 16, `#9A9AB0`).
- Bottom caption, from `name`: "structural typing: the methods decide the fit".
- Bottom caption, from `runtime` (replaces the last caption): "not checked at run time".

#### Animation steps

1. Start of block 1: `FadeIn` Snippet A. Highlight the line `class Strategy(Protocol):`.
2. `shape`: move the highlight to the line `def choose_position(self, game: Game) -> Position: ...`.
3. `classes`: `FadeIn` Snippet C below Snippet A.
4. `noinherit`: `Indicate` each of the two lines in Snippet C, one after the other (1 second each). Each header ends with a colon and has no base class in parentheses.
5. `socket`: `Create` the socket rectangle and slot on the left. `FadeIn` the two plugs.
6. `socket` (continued): move the `FirstAvailableStrategy` plug so that its tab touches the slot. Then move it back. Then do the same with the `MinimaxStrategy` plug.
7. `name`: `Write` the caption.
8. `runtime`: `Transform` the caption into the new caption. End of block: `FadeOut` all objects.

#### Accuracy notes

- `Strategy` is not decorated with `@runtime_checkable`. Do not show or say `isinstance(..., Strategy)` as a check that works. It raises a `TypeError`.
- Neither `FirstAvailableStrategy` nor `MinimaxStrategy` has a base class. Snippet C shows the real class headers.
- The project does not configure a type checker. Say "a type checker can check", not "the project checks".
- Do not use the word "interface" in narration.

---

### Scene E3S4: A strategy is player-agnostic

- **Scene ID:** `E3S4`
- **Class name:** `E3S4PlayerAgnostic`
- **Target duration:** 47 seconds (narration: 101 words, about 43 seconds of speech; the rest is animation time)

#### Narration

Block 1:

> Now look at what choose position does not take. <bookmark mark='noplayer'/> It takes no player. A strategy does not play for X, and it does not play for O. <bookmark mark='current'/> It plays for game dot current player: the player whose turn it is now.

Block 2:

> <bookmark mark='place'/> The strategy only gives back a cell. Then the Game puts the mark of the current player on that cell. <bookmark mark='seats'/> Thus one strategy class can sit in either seat. In the first demo match, FirstAvailableStrategy plays X. <bookmark mark='training'/> Later in main dot py, it trains learners from both seats. It plays O, and it plays X. The class does not change.

#### Visuals

- Right: code panel with Snippet A, center `(3.3, 1.8, 0)`.
- Right, from `place`: code panel with Snippet I, center `(3.3, -0.2, 0)`.
- Left: a board at the board position, indices off. Two seat labels: "X seat" (color `#4C9BE8`, font size 32) at `(-5.9, 1.2, 0)` and "O seat" (color `#F2A541`, font size 32) at `(-5.9, -1.2, 0)`.
- A card labeled `FirstAvailableStrategy` (rounded rectangle, stroke `#E6E6E6`, width 3.2, height 0.7, font size 22) that moves between the seats.
- Text `game.current_player` (font size 28, `#E6E6E6`) above the board at `(-3.5, 2.3, 0)`.

#### Animation steps

1. Start of block 1: `FadeIn` Snippet A and the board.
2. `noplayer`: highlight `(self, game: Game)` in Snippet A. Do not use a red cross (red means error). `Write` the grey text "no player parameter" (`#9A9AB0`, font size 24) under Snippet A.
3. `current`: `Write` the text `game.current_player` above the board.
4. `place`: `FadeIn` Snippet I. Highlight `self.current_player` in that line.
5. `seats`: `FadeIn` the seat labels. `FadeIn` the `FirstAvailableStrategy` card next to "X seat", at `(-3.5, 1.2, 0)`. Draw a blue X mark (`#4C9BE8`) in cell 0.
6. `training`: remove the X mark. Move the card to `(-3.5, -1.2, 0)` next to "O seat". Draw an orange O mark (`#F2A541`) in cell 4. Then move the card back to the X seat position, and back again to the O seat position (0.8 seconds each move).
7. End of block 2: `FadeOut` all objects.

#### Accuracy notes

- `FirstAvailableStrategy` never reads `game.current_player`. The `Game` aggregate uses `self.current_player` when it places the mark (Snippet I).
- In `main.py`, training uses `FirstAvailableStrategy()` as the opponent of the X `PolicyLearner` (so it plays O) and of the O `PolicyLearner` (so it plays X).
- The cell choices in step 5 and 6 are only a picture of a seat. They do not show a real game.

---

### Scene E3S5: The code of FirstAvailableStrategy

- **Scene ID:** `E3S5`
- **Class name:** `E3S5FirstAvailableCode`
- **Target duration:** 55 seconds (narration: 117 words, about 50 seconds of speech; the rest is animation time)

#### Narration

Block 1:

> Here is the first strategy: FirstAvailableStrategy. <bookmark mark='code'/> The class has nine lines. <bookmark mark='board'/> First, it reads the board from the game. <bookmark mark='range'/> Then it counts through the cell indices, from zero to eight. SIZE is three, so SIZE times SIZE is nine.

Block 2:

> <bookmark mark='fromindex'/> Position from index turns an index into a row and a column. Index five becomes row one, column two. <bookmark mark='occupied'/> Board is occupied asks one question: does this cell have a mark?

Block 3:

> <bookmark mark='free'/> Each free cell goes into a list with the name free. <bookmark mark='first'/> The method returns the first item of that list. <bookmark mark='rules'/> Note what the strategy does not do. It does not repeat a game rule. It asks the board one question and uses plain Python for the rest.

#### Visuals

- Right top: code panel with Snippet B, center `(3.3, 1.2, 0)`.
- Right bottom, from `fromindex`: a second code panel with Snippet D, center `(3.3, -2.2, 0)`, scaled to width 5.8. At `occupied`, replace it with Snippet E at the same position.
- Left: a board at the board position, indices on. Row labels `0`, `1`, `2` (font size 22, `#9A9AB0`) at the left of each row. Column labels `0`, `1`, `2` above each column.

#### Animation steps

1. Start of block 1: `FadeIn` Snippet B and the board.
2. `code`: `Indicate` the whole Snippet B panel.
3. `board`: highlight the line `board = game.board`.
4. `range`: highlight the line `for index in range(SIZE * SIZE)`. Flash each cell index 0 to 8 in order, 0.2 seconds each (`Indicate` the index text).
5. `fromindex`: highlight the line `Position.from_index(index)`. `FadeIn` Snippet D. Put the scan highlight on cell 5. `Write` the grey text "5 → row 1, column 2" (font size 26) under the board at `(-3.5, -2.6, 0)`. `Indicate` row label `1` and column label `2`.
6. `occupied`: `FadeOut` the "5 → row 1, column 2" text and the scan highlight. Replace Snippet D with Snippet E (`ReplacementTransform`). Highlight the line `if not board.is_occupied(Position.from_index(index))` in Snippet B.
7. `free`: highlight the line `free = [`.
8. `first`: highlight the line `return free[0]`.
9. `rules`: `FadeOut` Snippet E. `Indicate` the `board.is_occupied` part of Snippet B. End of block 3: `FadeOut` all objects.

#### Accuracy notes

- Snippet B has exactly 9 lines, from `class FirstAvailableStrategy:` to `return free[0]`.
- `SIZE` is 3. `range(SIZE * SIZE)` is `range(9)`: indices 0 to 8.
- Index 5 → row 1, column 2 (`5 // 3 = 1`, `5 % 3 = 2`). Rows and columns start at 0.
- The only question to the model is `board.is_occupied(...)`.

---

### Scene E3S6: Watch the scan

- **Scene ID:** `E3S6`
- **Class name:** `E3S6Scan`
- **Target duration:** 60 seconds (narration: 127 words, about 54 seconds of speech; the rest is animation time)

#### Narration

Block 1:

> Watch the strategy make one real move. <bookmark mark='position'/> X has a mark in cell zero. O has a mark in the center, cell four. It is the turn of X.

Block 2:

> <bookmark mark='scan0'/> The scan starts at index zero. Cell zero is occupied, so the scan skips it. <bookmark mark='scan1'/> Index one is free. It goes into the list. <bookmark mark='scan2'/> Index two is free. It goes into the list too. <bookmark mark='scan3'/> Index three is free. Index four is occupied. <bookmark mark='scanrest'/> Five, six, seven, and eight are free.

Block 3:

> <bookmark mark='all'/> Note that the scan does not stop at the first free cell. It checks all nine indices. Now the list holds seven positions. <bookmark mark='pickfirst'/> The method returns the first one: index one. <bookmark mark='place'/> X plays the top middle cell. This is the real second move of X in the demo match.

#### Visuals

- Left: board at the board position, indices on. Blue X (`#4C9BE8`) in cell 0. Orange O (`#F2A541`) in cell 4.
- Left bottom: the free list text `free = [ ]` at `(-3.5, -2.6, 0)`.
- Right: code panel with Snippet B at the code panel position.
- The scan highlight (see layout constants).
- Caption (bottom right, at `(3.3, -3.2, 0)`, font size 26, `#9A9AB0`): "occupied: skip" or "free: add". Change the caption text at each scan step.

#### Animation steps

1. Start of block 1: `FadeIn` the board, the marks, Snippet B, and the text `free = [ ]`.
2. `position`: `Indicate` the X in cell 0, then the O in cell 4.
3. `scan0`: move the scan highlight to cell 0 (0.5 seconds). Highlight the code line `if not board.is_occupied(Position.from_index(index))`. Caption: "occupied: skip".
4. `scan1`: move the scan highlight to cell 1. Caption: "free: add". Update the list text to `free = [1]`. Highlight the code line `Position.from_index(index)`.
5. `scan2`: move the scan highlight to cell 2. Update the list text to `free = [1, 2]`.
6. `scan3`: move the scan highlight to cell 3. Update the list to `free = [1, 2, 3]`. Then move the highlight to cell 4. Caption: "occupied: skip".
7. `scanrest`: move the scan highlight to cells 5, 6, 7, 8, 0.4 seconds each. After each cell, add its index to the list. Caption: "free: add". The final list text is `free = [1, 2, 3, 5, 6, 7, 8]`.
8. `all`: remove the scan highlight. `Indicate` the whole list text.
9. `pickfirst`: highlight the code line `return free[0]`. Draw a `SurroundingRectangle` (stroke `#4C9BE8`) around the `1` in the list text. Put the scan highlight on cell 1.
10. `place`: draw a blue X (`#4C9BE8`) in cell 1 (`Create`, 0.8 seconds). Remove the scan highlight. End of block 3: `FadeOut` all objects.

#### Accuracy notes

- Board before the move: X in 0, O in 4. Free: 1, 2, 3, 5, 6, 7, 8. The strategy returns cell 1. This is move 3 of the demo match (the second move of X).
- The list holds `Position` objects. The screen shows their indices as a simple picture. Do not write `Position(...)` text in the list.
- The scan visits all 9 indices. Do not stop the animation at index 1.

---

### Scene E3S7: Three properties and a baseline

- **Scene ID:** `E3S7`
- **Class name:** `E3S7Properties`
- **Target duration:** 52 seconds (narration: 117 words, about 50 seconds of speech; the rest is animation time)

#### Narration

Block 1:

> This strategy has three important properties. <bookmark mark='tiny'/> First, it is tiny: one list and one return statement. It runs in a small part of a millisecond. <bookmark mark='stateless'/> Second, it is stateless. The object has no fields. It keeps no memory of past moves or past games.

Block 2:

> <bookmark mark='predictable'/> Third, it is fully predictable. The same board always gives the same move. There is no random choice. <bookmark mark='blind'/> But it never looks at the shape of the board. It does not see a line of two marks. It does not prefer the center.

Block 3:

> <bookmark mark='baseline'/> Then why write it? It is a baseline: a simple reference point. <bookmark mark='measure'/> A strategy that beats it plays with some skill. A strategy that loses to it has no skill.

#### Visuals

- Title (top): `FirstAvailableStrategy`.
- Center: three property cards in a row at `y = 0.8`, at `x = -4.5`, `x = 0`, `x = 4.5`. Each card is a rounded rectangle (width 3.8, height 1.6, stroke `#E6E6E6`) with a bold label (font size 32) and a grey line below (font size 22, `#9A9AB0`):
  - "tiny" / "one list, one return"
  - "stateless" / "no fields, no memory"
  - "predictable" / "same board → same move"
- Below, from `blind`: a small board (cell side 0.6) at `(0, -2.2, 0)`, with X marks (`#4C9BE8`) in cells 0 and 1 and O marks (`#F2A541`) in cells 2 and 4. Next to it, the grey text "no look at lines" at `(2.8, -2.2, 0)`.
- From `baseline`: a horizontal scale line at `y = -2.2` from `x = -5` to `x = 5` (`#9A9AB0`) with a tick at `x = -3` labeled "baseline" (`#E6E6E6`) and the text "better →" at `x = 3.5`. This replaces the small board.

#### Animation steps

1. Start of block 1: `Write` the title.
2. `tiny`: `FadeIn` the "tiny" card.
3. `stateless`: `FadeIn` the "stateless" card.
4. `predictable`: `FadeIn` the "predictable" card.
5. `blind`: `FadeIn` the small board and the text "no look at lines".
6. `baseline`: `FadeOut` the small board and its text. `Create` the scale line and the "baseline" tick.
7. `measure`: `Write` "better →". `Indicate` the "baseline" tick. End of block 3: `FadeOut` all objects.

#### Accuracy notes

- `FirstAvailableStrategy` has no `__init__` and stores nothing. It is stateless.
- It uses no random numbers. `ThreatBuilderStrategy` uses random numbers; do not mention it in this scene.
- Do not give a number of microseconds in narration. The measured value depends on the machine.

---

### Scene E3S8: Set up the match

- **Scene ID:** `E3S8`
- **Class name:** `E3S8MatchSetup`
- **Target duration:** 42 seconds (narration: 90 words, about 39 seconds of speech; the rest is animation time)

#### Narration

Block 1:

> Now put it in a real match. <bookmark mark='main'/> In main dot py, the first match puts FirstAvailableStrategy in the X seat. MinimaxStrategy sits in the O seat. <bookmark mark='minimax'/> For now, think of MinimaxStrategy as a player that searches every future of the game. Video four shows how.

Block 2:

> <bookmark mark='loop'/> The loop runs while the game is in progress. <bookmark mark='pick'/> Each turn, pick gives the game to the strategy of the current player. For a strategy, pick simply calls choose position. <bookmark mark='place'/> The engine receives a PlaceMark command with that position. Then the loop prints the board.

#### Visuals

- Right top: code panel with Snippet F, center `(3.3, 2.4, 0)`.
- Right middle: code panel with Snippet G, center `(3.3, 0.3, 0)`, from `loop`.
- Right bottom: code panel with Snippet H, center `(3.3, -2.3, 0)`, scaled to width 6.2, from `pick`.
- Left: two seat labels. "X: FirstAvailableStrategy" (color `#4C9BE8`, font size 30) at `(-3.5, 1.5, 0)`. "O: MinimaxStrategy" (color `#F2A541`, font size 30) at `(-3.5, 0.7, 0)`.
- Left, from `minimax`: grey text "searches every future (video 4)" (font size 24, `#9A9AB0`) at `(-3.5, 0.1, 0)`.
- Left, from `place`: a command card `PlaceMark` (color `#61AFEF`) with the fields `game_id` and `position`, at `(-3.5, -1.8, 0)`.

#### Animation steps

1. Start of block 1: `FadeIn` Snippet F.
2. `main`: `Write` the two seat labels, X first.
3. `minimax`: `FadeIn` the grey text under the O label.
4. `loop`: `FadeIn` Snippet G. Highlight `while game.status is GameStatus.IN_PROGRESS:`.
5. `pick`: move the highlight to the `pick(...)` line. `FadeIn` Snippet H. Highlight its last line, `return agent.choose_position(game)`.
6. `place`: move the Snippet G highlight to `game = engine.place_mark(PlaceMark(game_id, position))`. `FadeIn` the `PlaceMark` card. End of block 2: `FadeOut` all objects.

#### Accuracy notes

- `main.py` runs `run_match(engine, FirstAvailableStrategy(), MinimaxStrategy())` first. The second argument is X. The third argument is O.
- `pick` calls `agent.choose_position(game)` for a strategy. The branch with `explore` is for the learners of videos 5 and 6. Do not explain it.
- Do not explain how minimax works. The only allowed description is "a player that searches every future of the game".

---

### Scene E3S9: Replay the real match

- **Scene ID:** `E3S9`
- **Class name:** `E3S9Replay`
- **Target duration:** 75 seconds (narration: 156 words, about 67 seconds of speech; the rest is animation time)

#### Narration

Block 1:

> Here is the real game from the demo, move by move. <bookmark mark='m1'/> Move one. X scans from index zero. Cell zero is free, so X plays the top left corner. <bookmark mark='m2'/> Move two. O plays the center, cell four.

Block 2:

> <bookmark mark='m3'/> Move three. For X, index zero is occupied. Index one is free, so X plays the top middle. <bookmark mark='m4'/> Move four. O plays cell two, the top right corner. Now O has two marks on a diagonal: cells two and four. Cell six completes that line.

Block 3:

> <bookmark mark='m5'/> Move five. X scans again. Zero, one, and two are occupied. Index three is free, so X plays the middle left. <bookmark mark='m6'/> Move six. O plays cell six, and the diagonal two, four, six is complete. This move also blocks X, because X has cells zero and three.

Block 4:

> <bookmark mark='won'/> O wins. The bus prints MarkPlaced, then GameWon. The final status is O won. <bookmark mark='same'/> Both strategies are predictable. Thus this match is the same on every run.

#### Visuals

- Left: board at the board position, indices on.
- Right: a move list at `(3.3, 1.5, 0)`, aligned left, font size 30. One line for each move, added at its bookmark:
  - "1. X → 0" (color `#4C9BE8`)
  - "2. O → 4" (color `#F2A541`)
  - "3. X → 1" (color `#4C9BE8`)
  - "4. O → 2" (color `#F2A541`)
  - "5. X → 3" (color `#4C9BE8`)
  - "6. O → 6" (color `#F2A541`)
- For X moves, use the scan highlight to visit cells in order before the mark appears.
- From `m4`: a dashed line in `#F2A541` (stroke width 6, opacity 0.6) from the center of cell 2 to the center of cell 6 (the threat).
- From `m6`: a solid line in `#F2A541` (stroke width 10) from cell 2 to cell 6 (the win). This replaces the dashed line.
- From `won`: two event cards (color `#98C379`) on the right at `(3.3, -1.8, 0)`: `MarkPlaced` and `GameWon`, side by side. Under them the text `GameStatus.O_WON` (font size 28, `#F2A541`) at `(3.3, -3.0, 0)`.

#### Animation steps

1. Start of block 1: `FadeIn` the empty board with indices.
2. `m1`: scan highlight on cell 0 (0.4 seconds). `Create` a blue X in cell 0. Remove the highlight. Add move line 1.
3. `m2`: `Create` an orange O in cell 4. Add move line 2.
4. `m3`: scan highlight on cell 0, then cell 1 (0.4 seconds each). `Create` a blue X in cell 1. Remove the highlight. Add move line 3.
5. `m4`: `Create` an orange O in cell 2. Add move line 4. `Create` the dashed threat line from cell 2 to cell 6. `Indicate` cell 6.
6. `m5`: scan highlight on cells 0, 1, 2, 3 (0.4 seconds each). `Create` a blue X in cell 3. Remove the highlight. Add move line 5.
7. `m6`: `Create` an orange O in cell 6. Add move line 6. `ReplacementTransform` the dashed line into the solid win line. Then `Indicate` the blue X marks in cells 0 and 3 (the X line that O blocks).
8. `won`: `FadeIn` the `MarkPlaced` card, then the `GameWon` card, then the status text.
9. `same`: `Indicate` the whole move list. End of block 4: `FadeOut` all objects.

#### Accuracy notes

- The move order is exactly X 0, O 4, X 1, O 2, X 3, O 6. Do not change it.
- The final board is `X X O / X O . / O . .` (cells 5, 7, 8 are free).
- O wins on the diagonal 2, 4, 6. The status is `GameStatus.O_WON`.
- For the last move, the bus prints `MarkPlaced` first and `GameWon` second.
- X plays only three marks. The game ends after 6 moves.
- The scan in step 6 for move 5 can stop at cell 3 in this scene for speed. The code checks all 9 indices (shown in E3S6 and E3S10).

---

### Scene E3S10: The missed block

- **Scene ID:** `E3S10`
- **Class name:** `E3S10MissedBlock`
- **Target duration:** 68 seconds (narration: 141 words, about 60 seconds of speech; the rest is animation time)

#### Narration

Block 1:

> Go back to move five. This is the move where X loses the game. <bookmark mark='rewind'/> Before move five, O has marks in cells two and four. <bookmark mark='threat'/> Cell six is the last free cell on that diagonal. If O gets cell six, O wins.

Block 2:

> <bookmark mark='block'/> X can stop this. A mark of X in cell six blocks the line. <bookmark mark='scan'/> But the strategy does not look for a block. It scans in index order. The free list is three, five, six, seven, eight. <bookmark mark='choose3'/> Index three is first, so X plays cell three.

Block 3:

> <bookmark mark='outcomes'/> How bad is that choice? Assume perfect play from both players after this move. <bookmark mark='draw'/> Cell six gives a draw. <bookmark mark='loss'/> Each of the other four cells loses.

Block 4:

> <bookmark mark='nochecks'/> Look at the code again. No line looks for a win. No line looks for a block. <bookmark mark='onlyq'/> The strategy only asks one question: is this cell occupied?

#### Visuals

- Left: board at the board position, indices on. X (`#4C9BE8`) in cells 0 and 1. O (`#F2A541`) in cells 2 and 4.
- Left bottom: free list text at `(-3.5, -2.6, 0)`.
- Right: code panel with Snippet B, from `nochecks` only. Before `nochecks`, the right side shows the outcome legend.
- Outcome legend (right, from `outcomes`, center `(3.3, 0.5, 0)`, font size 30): two lines, "draw" in `#9A9AB0` and "X loses" in `#E06C75`.
- Outcome labels in cells (from `draw` and `loss`, font size 26, centered in each cell):
  - Cell 6: "draw" in `#9A9AB0`.
  - Cells 3, 5, 7, 8: "loses" in `#E06C75`.
- Threat line: a dashed line in `#F2A541` from cell 2 to cell 6.

#### Animation steps

1. Start of block 1: `FadeIn` the board with X in 0 and 1, O in 2 and 4.
2. `rewind`: `Indicate` the O marks in cells 2 and 4.
3. `threat`: `Create` the dashed threat line from cell 2 to cell 6. Put a pulsing outline on cell 6: a `Square(side_length=1.2)` with stroke `#F2A541`, stroke width 8. Use `Indicate` two times.
4. `block`: `Create` a blue X in cell 6 at opacity 0.35 (a "ghost" move). Keep it for 2 seconds. Then `FadeOut` the ghost X.
5. `scan`: move the scan highlight across all cells 0 to 8 (0.35 seconds each). Add each free index to the list text. The final list text is `free = [3, 5, 6, 7, 8]`.
6. `choose3`: draw a `SurroundingRectangle` (stroke `#4C9BE8`) around the `3` in the list. `Create` a blue X in cell 3. Remove the scan highlight.
7. `outcomes`: `FadeOut` the blue X in cell 3 (return to the position before move 5). `FadeIn` the outcome legend on the right.
8. `draw`: `Write` "draw" in cell 6.
9. `loss`: `Write` "loses" in cells 3, 5, 7, and 8, with `LaggedStart`.
10. `nochecks`: `FadeOut` the outcome legend. `FadeIn` Snippet B on the right. `Indicate` the full list comprehension lines.
11. `onlyq`: highlight the line `if not board.is_occupied(Position.from_index(index))`. End of block 4: `FadeOut` all objects.

#### Accuracy notes

- The position is real: it is the board before move 5 of the demo match (X in 0 and 1, O in 2 and 4, X to move).
- Free cells: 3, 5, 6, 7, 8. `FirstAvailableStrategy` returns 3.
- With perfect play after the move: cell 6 → draw; cells 3, 5, 7, 8 → X loses. This was checked with `MinimaxStrategy._score`. Do not show the scores 0 and −10 in this video; show only "draw" and "loses".
- X has no winning move in this position. Do not say "X missed a win" here.
- Before move 3, every free cell gave a draw. Thus move 5 is the losing move. Do not say that the first move or move 3 lost the game.
- The strategy code has no check for a win and no check for a block.

---

### Scene E3S11: Predictable means easy to exploit

- **Scene ID:** `E3S11`
- **Class name:** `E3S11Predictable`
- **Target duration:** 55 seconds (narration: 119 words, about 51 seconds of speech; the rest is animation time)

#### Narration

Block 1:

> There is one more weakness. <bookmark mark='predict'/> The strategy is fully predictable. Give it a board, and you know its move before it plays.

Block 2:

> <bookmark mark='plan'/> An opponent that knows this can plan. It makes a threat on a cell that is not the first free cell. <bookmark mark='fills'/> The naive strategy fills the first free cell, and the threat stays open. <bookmark mark='nosearch'/> The opponent does not need to search every future. It only needs to know the order.

Block 3:

> <bookmark mark='numbers'/> The demo shows this. In video five, a learner trains against this strategy from the O seat. <bookmark mark='wins'/> In six thousand training games, the learner wins five thousand, nine hundred and sixty. <bookmark mark='lesson'/> A player with no defense and no surprise is simple to write, and simple to beat.

#### Visuals

- Left: board at the board position, indices on. Start with the position before move 5: X in 0 and 1, O in 2 and 4.
- Left, from `predict`: a grey text "next move: 3" (font size 30, `#9A9AB0`) above the board at `(-3.5, 2.3, 0)`.
- From `plan`: dashed threat line in `#F2A541` from cell 2 to cell 6. Grey label "threat on 6" (font size 24) near cell 6, at `(-5.9, -2.0, 0)`.
- From `fills`: blue X in cell 3.
- Right, from `numbers`: a result panel centered at `(3.3, 0, 0)`:
  - Title text "learner (O) vs FirstAvailableStrategy (X)" (font size 26, `#E6E6E6`).
  - Three bars, each with a label and a number (font size 28):
    - "won 5960" bar in `#98C379`, length proportional to 5960/6000 of 5 units.
    - "drew 11" bar in `#9A9AB0`, length proportional to 11/6000 of 5 units (show at least 0.05 units).
    - "lost 29" bar in `#E06C75`, length proportional to 29/6000 of 5 units (show at least 0.05 units).
  - Caption under the bars: "6,000 training games (video 5)" (font size 22, `#9A9AB0`).

#### Animation steps

1. Start of block 1: `FadeIn` the board and the four marks.
2. `predict`: `Write` "next move: 3". Put the scan highlight on cell 3.
3. `plan`: `Create` the dashed threat line and the label "threat on 6".
4. `fills`: `Create` a blue X in cell 3. Remove the scan highlight. `Indicate` cell 6 (still free).
5. `nosearch`: `FadeOut` the "next move: 3" text.
6. `numbers`: `FadeIn` the result panel title and the three bar labels.
7. `wins`: `GrowFromEdge` each bar from its left edge, with `LaggedStart`. `Indicate` the "won 5960" label.
8. `lesson`: `Indicate` the board. End of block 3: `FadeOut` all objects.

#### Accuracy notes

- The numbers are from the demo output line `tabular O vs naive: won 5960, drew 11, lost 29`. The learner plays O. `FirstAvailableStrategy` plays X. There are 6,000 training episodes.
- These are training games, with exploration on. Do not call them "test games" or "a win rate after training".
- Do not explain how the learner works. Video 5 explains it.
- "An opponent that knows the order" is a picture of the idea. Do not say that the learner reads the source code.

---

### Scene E3S12: Closing and hook

- **Scene ID:** `E3S12`
- **Class name:** `E3S12Hook`
- **Target duration:** 28 seconds (narration: 54 words, about 23 seconds of speech; the rest is animation time)

#### Narration

Block 1:

> Here is what we saw. <bookmark mark='r1'/> A strategy is one method: choose position. <bookmark mark='r2'/> Strategy is a Protocol, so any object with that method fits. <bookmark mark='r3'/> FirstAvailableStrategy takes the first free cell in index order. It is stateless and predictable, and it loses.

Block 2:

> <bookmark mark='hook'/> So what does a player that never makes a mistake look like? <bookmark mark='next'/> Next: minimax.

#### Visuals

- Left: three summary lines at `x = -6.5`, aligned left, at `y = 1.5`, `y = 0.5`, `y = -0.5`, font size 30, color `#E6E6E6`:
  - "1. Strategy = one method: `choose_position`"
  - "2. `Protocol`: the method decides the fit"
  - "3. `FirstAvailableStrategy`: first free cell, loses"
- Right: the final board of the demo match (cell side 0.9) at `(4.0, 0.5, 0)`: X (`#4C9BE8`) in 0, 1, 3; O (`#F2A541`) in 2, 4, 6; solid O win line from cell 2 to cell 6.
- From `hook`: the text "What does a player that never makes a mistake look like?" (font size 36, `#E6E6E6`) at `(0, -2.0, 0)`.
- From `next`: the text "Next: minimax" (font size 48, `#E6E6E6`) at `(0, -3.0, 0)`.

#### Animation steps

1. Start of block 1: `FadeIn` the final board on the right.
2. `r1`: `Write` summary line 1.
3. `r2`: `Write` summary line 2.
4. `r3`: `Write` summary line 3.
5. `hook`: `FadeOut` the three summary lines. `Write` the question text.
6. `next`: `Write` "Next: minimax". Wait 2 seconds. `FadeOut` all objects.

#### Accuracy notes

- The final board is the real final board: X in 0, 1, 3; O in 2, 4, 6.
- Do not explain minimax in this scene. Say only "Next: minimax".

---

## 7. Duration summary

| Scene | Class | Target (s) | Narration words |
|-------|-------|-----------|-----------------|
| E3S1 | `E3S1Recap` | 18 | 36 |
| E3S2 | `E3S2EmptySeat` | 55 | 119 |
| E3S3 | `E3S3Protocol` | 62 | 137 |
| E3S4 | `E3S4PlayerAgnostic` | 47 | 101 |
| E3S5 | `E3S5FirstAvailableCode` | 55 | 117 |
| E3S6 | `E3S6Scan` | 60 | 127 |
| E3S7 | `E3S7Properties` | 52 | 117 |
| E3S8 | `E3S8MatchSetup` | 42 | 90 |
| E3S9 | `E3S9Replay` | 75 | 156 |
| E3S10 | `E3S10MissedBlock` | 68 | 141 |
| E3S11 | `E3S11Predictable` | 55 | 119 |
| E3S12 | `E3S12Hook` | 28 | 54 |
| **Total** | | **617 (10:17)** | **1314** |

The narration uses about 130 to 150 words per minute. The animations can add pauses. If the rendered episode is longer than 12 minutes, shorten the `wait` calls, not the narration.

## 8. Accuracy notes for the article

These notes record where the article and the code differ, or where the article is not exact. The code wins.

1. The article calls the protocol "a structural interface" and says an object "**is** a strategy". The protocol is not `@runtime_checkable`, so Python does not check it at run time. Only a static type checker can check the fit. The project has no type checker configured.
2. The article says "one `MinimaxStrategy` object can sit in the X seat in one match and the O seat in the next". This is possible, but `main.py` makes a new `MinimaxStrategy()` for each seat. The video uses `FirstAvailableStrategy` in training (X and O seats) as the example.
3. The article describes `FirstAvailableStrategy` as "walk the nine cells … collect the empty ones, and return the first". This is correct: the code does not stop at the first free cell. The video must show the full scan.
4. The article (later section) says "two lines of code" for first-available. The class body is a list comprehension and a return; the class has 9 lines. The video says "one list and one return statement" and "nine lines".
5. The article does not name the losing move. The code check shows that move 5 (X in cell 3) is the losing move; cell 6 was the only move that kept a draw.

## 9. Checks

Answer each question with yes or no. Each answer must be "yes".

1. Is the recap in `E3S1` 20 seconds or less?
2. Does the video say that a strategy is one method, `choose_position`, that takes a `Game` and returns a `Position`?
3. Does the video say that `Strategy` is a `typing.Protocol`, and that an object fits without inheritance?
4. Does the video avoid a claim that Python checks the protocol at run time?
5. Does the video say that a strategy takes no player and plays for `game.current_player`?
6. Is Snippet B on screen exactly the 9 lines of `FirstAvailableStrategy` from `strategies.py`?
7. Does the scan animation in `E3S6` visit all 9 indices and give `free = [1, 2, 3, 5, 6, 7, 8]` and the move 1?
8. Is the replayed move order exactly X 0, O 4, X 1, O 2, X 3, O 6?
9. Is the final status `GameStatus.O_WON`, with the win on the diagonal 2, 4, 6?
10. Does `E3S10` show the real position before move 5 (X in 0 and 1, O in 2 and 4) and the free list `[3, 5, 6, 7, 8]`?
11. Does `E3S10` show cell 6 as "draw" and cells 3, 5, 7, 8 as "loses"?
12. Does the video say that the code has no check for a win and no check for a block?
13. Are the learner numbers exactly 6,000 games, won 5960, drew 11, lost 29, with the learner in the O seat?
14. Does the video describe minimax only as "a player that searches every future", with no explanation of the algorithm?
15. Do X marks use `#4C9BE8`, O marks use `#F2A541`, `PlaceMark` use `#61AFEF`, and event cards use `#98C379`?
16. Is red (`#E06C75`) used only for losses, and never as a decoration or a highlight?
17. Does the last scene end with the question about a player that never makes a mistake, and "Next: minimax"?
18. Is the total rendered length between 8 and 12 minutes?
