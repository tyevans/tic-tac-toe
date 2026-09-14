# Episode 4: The Perfect Player

## 1. Header

- **Title:** The Perfect Player
- **Number:** 4 of 6
- **Target length:** 9 minutes 55 seconds (12 scenes, 595 seconds)
- **Source files:**
  - `src/tictactoe/strategies.py` (`MinimaxStrategy`, `Strategy`)
  - `src/tictactoe/value_objects.py` (`Board.with_mark`, `Board.winning_line`, `Board.is_full`)
  - `main.py` (the match `run_match(engine, MinimaxStrategy(), MinimaxStrategy())`, `EPISODES = 6000`)
  - `AGENTS.md` (the statement that `MinimaxStrategy` is too slow to use as a training opponent)
- **Source article sections:** `blog/articles/02-writing-our-own-strategies.md`, from "The optimal player: minimax, in plain English" to the end ("Show it draws itself, and pay for it", "What if it learned instead?").

## 2. Goal

After the video, the viewer can explain how `MinimaxStrategy` selects a move. The viewer can draw a small game tree, give each end board a score of +10, −10, or 0, and move the scores up to the root with max on "my" turn and min on the opponent's turn. The viewer can read `choose_position` and `_score`, and can tell which cell the strategy selects when two moves have the same score. The viewer can also explain why a full search costs 549,945 `_score` calls for the first move, and why this makes minimax too slow to use as a training opponent.

## 3. Recap from the last video

Maximum 20 seconds. This is scene `E4S1`. The facts:

- A strategy is any object with one method: `choose_position(game) -> Position`. This is the `Strategy` protocol (the "seam").
- `FirstAvailableStrategy` takes the first free cell in index order, 0 to 8.
- It lost to `MinimaxStrategy`, because it never looks ahead.

## 4. Terms

- **Minimax:** A search that tries every possible rest of the game, then selects the move with the best score when the opponent also plays its best moves.
- **Game tree:** A diagram of boards. Each line goes from a board to a board with one more mark.
- **Root:** The board at the top of the game tree. It is the board now, before the move.
- **Child board:** A board that you get when the player to move puts one mark in one free cell.
- **End board:** A board where a player has a winning line, or where all nine cells are full. An end board has no child boards.
- **Score:** An integer for a board, from the point of view of `me`: 10 for a win, −10 for a loss, 0 for a draw.
- **`me`:** The player who asks for a move. `me` does not change during the search.
- **`player_to_move`:** The player who puts the next mark on a board in the search. It changes at each level of the tree.
- **Max:** On a board where `me` is to move, the score of the board is the highest score of its child boards.
- **Min:** On a board where the opponent is to move, the score of the board is the lowest score of its child boards.
- **Recursion:** A function that calls itself on a smaller problem. `_score` calls `_score` on each child board.
- **Tie-break:** The rule that selects one move when two or more moves have the same highest score.
- **Depth discount:** A change to the score that makes a fast win better than a slow win. This code does not have a depth discount.

## 5. Source facts

### 5.1 Code snippets

Copy these snippets exactly. Do not change the code. The code panel may scale the text to fit, but it must not wrap or cut a line.

**Snippet S-PROTOCOL** (`strategies.py`)

```python
class Strategy(Protocol):
    def choose_position(self, game: Game) -> Position: ...
```

**Snippet S-BASE** (`strategies.py`, the class line and the first 7 lines of `_score`)

```python
class MinimaxStrategy:
    def _score(self, board: Board, player_to_move: Player, me: Player) -> int:
        if board.winning_line(me) is not None:
            return 10
        if board.winning_line(me.opponent) is not None:
            return -10
        if board.is_full():
            return 0
```

**Snippet S-SCORE** (`strategies.py`, all of `_score`, with the class line)

```python
class MinimaxStrategy:
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
```

Line numbers in S-SCORE for highlights (1 = `class MinimaxStrategy:`): base cases are lines 3 to 8. The list of child scores is lines 9 to 13. The max/min line is line 14.

Note: S-SCORE has 14 lines. It fits the 15-line limit.

**Snippet S-CHOOSE** (`strategies.py`, all of `choose_position`, 11 lines)

```python
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
```

Line numbers in S-CHOOSE for highlights: `me = game.current_player` is line 4. The candidate list is lines 5 to 9. The `max` line is line 10.

**Snippet S-WITHMARK** (`value_objects.py`, `Board.with_mark` and `Board.is_full`)

```python
    def is_full(self) -> bool:
        return all(cell.player is not None for cell in self.cells)

    def with_mark(self, position: Position, player: Player) -> "Board":
        if self.is_occupied(position):
            raise PositionOccupiedError(position.row, position.column)
        cells = list(self.cells)
        cells[position.index] = Cell(player)
        return Board(tuple(cells))
```

### 5.2 Board notation in this file

This file writes a board as three rows, top to bottom, with `.` for a free cell. Example: `XXO / .OX / .O.` means cells 0=X, 1=X, 2=O, 3=free, 4=O, 5=X, 6=free, 7=O, 8=free. Index 0 is top left. Index 8 is bottom right.

### 5.3 The small tree (scenes E4S5 and E4S6)

The root board is `XXO / .OX / .O.`. X is to move. `me` is X. Free cells: 3, 6, 8. All values below come from `MinimaxStrategy._score` in the real code.

| Node | Parent | Mark played | Board | Who moves next | Kind | Score |
|------|--------|-------------|-------|----------------|------|-------|
| R | none | none | `XXO / .OX / .O.` | X | max | 0 |
| A | R | X at 3 | `XXO / XOX / .O.` | O | min | −10 |
| A1 | A | O at 6 | `XXO / XOX / OO.` | none | end: O wins (line 2, 4, 6) | −10 |
| A2 | A | O at 8 | `XXO / XOX / .OO` | X | max | 10 |
| A2a | A2 | X at 6 | `XXO / XOX / XOO` | none | end: X wins (line 0, 3, 6) | 10 |
| B | R | X at 6 | `XXO / .OX / XO.` | O | min | 0 |
| B1 | B | O at 3 | `XXO / OOX / XO.` | X | max | 0 |
| B1a | B1 | X at 8 | `XXO / OOX / XOX` | none | end: full, draw | 0 |
| B2 | B | O at 8 | `XXO / .OX / XOO` | X | max | 10 |
| B2a | B2 | X at 3 | `XXO / XOX / XOO` | none | end: X wins (line 0, 3, 6) | 10 |
| C | R | X at 8 | `XXO / .OX / .OX` | O | min | −10 |
| C1 | C | O at 3 | `XXO / OOX / .OX` | X | max | 0 |
| C1a | C1 | X at 6 | `XXO / OOX / XOX` | none | end: full, draw | 0 |
| C2 | C | O at 6 | `XXO / .OX / OOX` | none | end: O wins (line 2, 4, 6) | −10 |

Facts from the table:

- The tree has 14 boards: 1 root and 13 boards below it. `choose_position` calls `_score` 13 times for this root.
- `choose_position` builds `candidates = [(-10, 3), (0, 6), (-10, 8)]`. It returns `Position(row=2, column=0)`, which is index 6.
- Index 6 blocks the O line 2, 4, 6.
- Min at A: min(−10, 10) = −10. Min at B: min(0, 10) = 0. Min at C: min(0, −10) = −10. Max at R: max(−10, 0, −10) = 0.
- The max boards A2, B1, B2, C1 have only one child board each, so max gives the score of that child.

### 5.4 Tie-break

- The `max` line is `max(candidates, key=lambda candidate: candidate[0])`. The key is only the score. The index is not part of the comparison.
- Python `max` returns the first item with the highest key. `candidates` is in index order 0 to 8. Thus, **a tie goes to the lowest index**.
- Test in Python: `max([(0, 0), (0, 1), (0, 4), (-10, 5)], key=lambda c: c[0])` returns `(0, 0)`. Without the key, `max` of the same list returns `(0, 4)`. The code uses the key, so the result is `(0, 0)`.
- Real evidence 1: from the empty board, all nine candidates have score 0. `MinimaxStrategy` selects index 0 (top left). The demo output shows X at index 0 first.
- Real evidence 2: on move 3 of the minimax-against-minimax game, all seven candidates have score 0: `[(0, 1), (0, 2), (0, 3), (0, 5), (0, 6), (0, 7), (0, 8)]`. X selects index 1.
- Real evidence 3: on move 8, candidates are `[(0, 7), (0, 8)]`. O selects index 7.

### 5.5 No depth discount (scene E4S8)

- `_score` returns 10 for every win. The number of moves before the win does not change the score.
- Example board: `XXO / OX. / O..`. X is to move. Free cells: 5, 7, 8.
- X at 7 wins now (line 1, 4, 7). X at 8 wins now (line 0, 4, 8).
- X at 5 does not win now. After X at 5, X has two open lines (1, 4, 7 and 0, 4, 8). O can block only one. X wins on its next move.
- `candidates = [(10, 5), (10, 7), (10, 8)]`. All three scores are 10. The tie goes to the lowest index. `choose_position` returns index 5, `Position(row=1, column=2)`.
- Result: the strategy does not take the win that is available now. It still wins, two plies later. Its play is correct (it never loses a won game), but it does not prefer a fast win.

### 5.6 Cost numbers (scene E4S9)

Measured with the real `MinimaxStrategy` code, Python 3.13.5, on one test machine.

- For the first move from the empty board, `choose_position` calls `_score` **549,945** times.
- Of these calls, **255,168** are end boards. This is the number of all possible tic-tac-toe games.
  - From X's point of view: 131,184 end boards score 10 (X wins), 77,904 score −10 (O wins), 46,080 score 0 (draw).
- Time for one first move from the empty board: **120.8 seconds** (about 2 minutes).
- Boards at each depth of the full game tree (depth 0 is the empty board):

| Depth (marks on the board) | Boards |
|---|---|
| 0 | 1 |
| 1 | 9 |
| 2 | 72 |
| 3 | 504 |
| 4 | 3,024 |
| 5 | 15,120 |
| 6 | 54,720 |
| 7 | 148,176 |
| 8 | 200,448 |
| 9 | 127,872 |
| **Total** | **549,946** |

  549,946 − 1 root = 549,945 `_score` calls.

- Cost of each move in the real minimax-against-minimax game (same test machine):

| Move | Player | Free cells | `_score` calls | Time |
|---|---|---|---|---|
| 1 | X | 9 | 549,945 | 120.8 s |
| 2 | O | 8 | 59,704 | 14.1 s |
| 3 | X | 7 | 7,331 | 1.66 s |
| 4 | O | 6 | 934 | 0.21 s |
| 5 | X | 5 | 197 | 0.049 s |
| 6 | O | 4 | 46 | 0.011 s |
| 7 | X | 3 | 13 | 0.0035 s |
| 8 | O | 2 | 4 | 0.0012 s |
| 9 | X | 1 | 1 | 0.0003 s |

- For each `_score` call, the code makes a new `Board` (with `with_mark`, a new tuple of nine cells) and new `Position` objects, and checks up to 16 lines (8 for `me`, 8 for the opponent).

### 5.7 The real minimax-against-minimax game (scene E4S10)

From `/tmp/ttt_main_output.txt`, the match header is `MinimaxStrategy (X) vs MinimaxStrategy (O)`. The moves, in order (cell index):

| Move | Player | Cell | Board after the move |
|---|---|---|---|
| 1 | X | 0 | `X.. / ... / ...` |
| 2 | O | 4 | `X.. / .O. / ...` |
| 3 | X | 1 | `XX. / .O. / ...` |
| 4 | O | 2 | `XXO / .O. / ...` |
| 5 | X | 6 | `XXO / .O. / X..` |
| 6 | O | 3 | `XXO / OO. / X..` |
| 7 | X | 5 | `XXO / OOX / X..` |
| 8 | O | 7 | `XXO / OOX / XO.` |
| 9 | X | 8 | `XXO / OOX / XOX` |

The events at the end are `MarkPlaced`, then `GameDrawn`. The final status is `GameStatus.DRAW`.

Notes on the moves (from the real candidate lists):

- Move 2: O candidates `[(-10, 1), (-10, 2), (-10, 3), (0, 4), (-10, 5), (-10, 6), (-10, 7), (-10, 8)]`. Only the center (4) does not lose against best play.
- Move 4: O blocks X's line 0, 1, 2 at cell 2.
- Move 5: X blocks O's line 2, 4, 6 at cell 6.
- Move 6: O blocks X's line 0, 3, 6 at cell 3.
- Move 7: X blocks O's line 3, 4, 5 at cell 5.

### 5.8 Training cost estimate (scene E4S11)

This is an estimate from the measured numbers, not a measured training run.

- `main.py` trains each learner for `EPISODES = 6000` games.
- If `MinimaxStrategy` plays O against a learner in the X seat, O's first move in each game makes 55,504 to 63,904 `_score` calls (it depends on X's first cell). At the measured rate, that is more than 10 seconds for each game. 6,000 games take more than 16 hours.
- If `MinimaxStrategy` plays X, its first move takes about 2 minutes in each game. 6,000 games take more than 8 days.
- `AGENTS.md` says: "`MinimaxStrategy` is too slow in pure Python to use as a training opponent (seconds per move)". The deep learners train against `ThreatBuilderStrategy` instead.

## 6. Scenes

Word counts are for the narration text without bookmark tags. The speech rate is about 140 words per minute.

---

### Scene E4S1: Recap

- **Manim class:** `E4S1Recap`
- **Target duration:** 20 seconds (44 words)

#### Narration

> <bookmark mark='seam'/>A strategy has one method: `choose_position`. It gets the game and gives back a position.
>
> <bookmark mark='naive'/>The naive strategy takes the first free cell. <bookmark mark='loss'/>It lost, because it never looks ahead.
>
> <bookmark mark='question'/>Today we meet a strategy that looks at every possible rest of the game.

(Spoken form of `choose_position`: "choose position".)

#### Visuals

- Title at top center: `Episode 4: The Perfect Player`, main text color, font size 40.
- Code panel, right half: snippet S-PROTOCOL.
- Board, left half, center at (−3.5, −0.3): the final board of the naive game `XXO / XO. / O..` (X marks blue, O marks orange).
- Red line (error color) through cells 2, 4, 6 on the board, and a label below the board: `FirstAvailableStrategy (X) lost`, red, font size 28.
- Last text, center: `MinimaxStrategy`, main text color, font size 48.

#### Animation steps

1. `seam`: FadeIn the title. Then Create the code panel with S-PROTOCOL on the right.
2. `naive`: Create the empty board on the left. Place the marks in the real game order: X0, O4, X1, O2, X3, O6. Use a fast run time (0.3 seconds for each mark).
3. `loss`: Create the red line through cells 2, 4, 6. FadeIn the red label below the board.
4. `question`: FadeOut the board, line, label, and code panel. Write `MinimaxStrategy` at center.

#### Accuracy notes

- The naive game is `FirstAvailableStrategy (X) vs MinimaxStrategy (O)`. The moves are X0, O4, X1, O2, X3, O6. O wins with line 2, 4, 6.
- Do not say that the naive strategy is random. It is deterministic.

---

### Scene E4S2: The Game Tree

- **Manim class:** `E4S2GameTree`
- **Target duration:** 50 seconds (119 words)

#### Narration

> <bookmark mark='imagine'/>Think about a chess player before a move. The player thinks: "If I play here, they play there. Then I play here."
>
> <bookmark mark='root'/>Minimax does this for every possible move. It starts from the board now. We call this board the root.
>
> <bookmark mark='children'/>For each free cell, it makes a child board with one more mark. Three free cells give three child boards.
>
> <bookmark mark='withmark'/>`with_mark` makes each child board. It does not change the old board. It returns a new board.
>
> <bookmark mark='alternate'/>Below each child board, the other player moves. The turns change at each level: X, then O, then X.
>
> <bookmark mark='end'/>A path stops at an end board. On an end board, a player has a line, or all nine cells are full.

(Spoken form of `with_mark`: "with mark".)

#### Visuals

- Root board: small board (cell side 0.4), top center at (0, 2.6), board `XXO / .OX / .O.` from section 5.3.
- Three child boards A, B, C (cell side 0.4) at (−4.5, 0.2), (0, 0.2), (4.5, 0.2). Lines from the root to each child, secondary text color `#9A9AB0`, stroke width 2.
- On each line, a small label with the new mark: `X at 3`, `X at 6`, `X at 8`, blue (X color), font size 22.
- The new mark in each child board: blue, with a short Indicate animation.
- Level labels at the left edge, x = −6.3: `X to move` (blue) at y = 2.6, `O to move` (orange) at y = 0.2.
- Code panel for `withmark`: snippet S-WITHMARK, bottom right, scaled to width 6.0, center at (3.5, −2.3). The panel must not overlap a board. If it overlaps child board C, scale the panel down until it does not.
- End-board example for `end`: two small boards (cell side 0.3) at bottom left, (−5.0, −2.6) and (−2.8, −2.6): `XXO / XOX / OO.` with an orange line through 2, 4, 6, and `XXO / OOX / XOX` with no line. Labels below them: `O has a line` (orange) and `all cells full` (secondary text), font size 20.

#### Animation steps

1. `imagine`: FadeIn a text at center, `If I play here, they play there...`, main text color, font size 32. Hold. FadeOut the text.
2. `root`: Create the root board at (0, 2.6) with its marks. Write the label `root` above it, main text color, font size 24.
3. `children`: Flash each free cell of the root (cells 3, 6, 8), one after the other. For each, Create the line and the child board, and write the mark label on the line. Show `X to move` at y = 2.6.
4. `withmark`: FadeIn the S-WITHMARK code panel at (3.5, −2.3). Surround the line `return Board(tuple(cells))` with a `SurroundingRectangle` in main text color. Keep the root board on screen, unchanged, to show that it did not change.
5. `alternate`: FadeOut the code panel. Write `O to move` (orange) at y = 0.2 at the left edge, next to the child boards.
6. `end`: FadeIn the two end-board examples at the bottom left, with their labels. Create the orange line on the first example.

#### Accuracy notes

- `with_mark` returns a new `Board`. It does not change the old board. It raises `PositionOccupiedError` if the cell is occupied.
- The turns alternate in the search because `_score` passes `player_to_move.opponent` to the next call.
- An end board is a board with a winning line for either player, or a full board. The code checks in this order: `me` wins, opponent wins, full.

---

### Scene E4S3: Scores at the End

- **Manim class:** `E4S3EndScores`
- **Target duration:** 50 seconds (113 words)

#### Narration

> <bookmark mark='me'/>Minimax gives each end board a score. The score is always from the point of view of one player. The code calls this player `me`.
>
> <bookmark mark='win'/>If `me` has a winning line, the score is 10.
>
> <bookmark mark='loss'/>If the opponent has a winning line, the score is minus 10.
>
> <bookmark mark='draw'/>If the board is full with no line, the score is 0. That is a draw.
>
> <bookmark mark='model'/>Look at the questions in this code. `winning_line` and `is_full` are methods of the `Board`. Minimax does not write the rules of tic-tac-toe again. It asks the model.
>
> <bookmark mark='fixed'/>`me` never changes during the search. A score of 10 always means a win for the player who asked for the move.

(Spoken forms: `me` is "me", `winning_line` is "winning line", `is_full` is "is full".)

#### Visuals

- Code panel, right half: snippet S-BASE.
- Left half: three small boards (cell side 0.45) in a column at x = −4.0, y = 2.0, 0.0, −2.0:
  - `XXO / XOX / XOO` with a blue line through 0, 3, 6. Score label to the right: `+10`, green (reward color), font size 36.
  - `XXO / XOX / OO.` with an orange line through 2, 4, 6. Score label: `−10`, red (negative color).
  - `XXO / OOX / XOX`, no line. Score label: `0`, grey (neutral color).
- A label at top left, (−4.0, 3.4): `me = X`, blue, font size 30.

#### Animation steps

1. `me`: Create the S-BASE code panel on the right. Write `me = X` at top left.
2. `win`: Create the first board and its blue line. Highlight code lines 3 and 4 (`if board.winning_line(me) is not None:` and `return 10`) with a rectangle in main text color. Write `+10` in green.
3. `loss`: Create the second board and its orange line. Move the highlight to code lines 5 and 6. Write `−10` in red.
4. `draw`: Create the third board. Move the highlight to code lines 7 and 8. Write `0` in grey.
5. `model`: Move the highlight to surround `winning_line` on line 3 and `is_full` on line 7 (two rectangles). Indicate the words.
6. `fixed`: Indicate the `me = X` label two times.

#### Accuracy notes

- The values are exactly `10`, `-10`, and `0`. Say "10", not "1". On screen, write `+10`, `−10`, `0`.
- The order of the checks is: `me` wins, then opponent wins, then full.
- All three example boards are real boards from the small tree in section 5.3.

---

### Scene E4S4: Max and Min

- **Manim class:** `E4S4MaxMin`
- **Target duration:** 45 seconds (98 words)

#### Narration

> <bookmark mark='notend'/>If the board is not an end board, the game continues. `_score` makes a child board for each free cell.
>
> <bookmark mark='recurse'/>Then it calls `_score` again on each child board. A function that calls itself is recursion.
>
> <bookmark mark='max'/>Now the most important line. If it is my turn, I take the highest score. That is max.
>
> <bookmark mark='min'/>If it is the opponent's turn, we think the opponent plays its best move. Its best move is my lowest score. That is min.
>
> <bookmark mark='flip'/>`me` stays the same. `player_to_move` changes at each call. Thus max and min change at each level of the tree.

(Spoken forms: `_score` is "score", `player_to_move` is "player to move".)

#### Visuals

- Code panel, right half: snippet S-SCORE (14 lines). Scale to fit width 7.0.
- Left half: a small diagram, center at (−3.8, 0):
  - One parent node: a rounded rectangle 1.4 × 0.7 at (−3.8, 1.8) with the text `?`.
  - Three child nodes: rounded rectangles 1.0 × 0.6 at (−5.4, −0.2), (−3.8, −0.2), (−2.2, −0.2), with the texts `+10` (green), `0` (grey), `−10` (red).
  - Lines from parent to children, secondary text color.
- Result labels below the diagram, at (−3.8, −1.6): `X to move: max → +10` in blue, and at (−3.8, −2.4): `O to move: min → −10` in orange. Font size 28.

#### Animation steps

1. `notend`: Create the code panel with S-SCORE. Dim lines 3 to 8 to 40% opacity. Highlight lines 9 to 13 with a rectangle in main text color.
2. `recurse`: Indicate the text `self._score(` on line 10. Create a curved arrow, main text color, from line 10 back to line 2 (`def _score`).
3. `max`: FadeOut the curved arrow. Move the highlight to line 14. Create the parent node and the three child nodes on the left. Write `X to move: max → +10` in blue. Transform the parent text `?` into `+10` in green.
4. `min`: Transform the parent text back to `?`. Write `O to move: min → −10` in orange. Transform the parent text `?` into `−10` in red.
5. `flip`: Indicate `me` in the parameter list of line 2. Then Indicate `player_to_move.opponent` on line 10.

#### Accuracy notes

- The line is `return max(scores) if player_to_move == me else min(scores)`.
- The example child scores `+10, 0, −10` are for teaching only. Say nothing that makes them sound like a real board.
- In this project, "my turn" means `player_to_move == me`.

---

### Scene E4S5: A Real Small Tree

- **Manim class:** `E4S5SmallTree`
- **Target duration:** 50 seconds (115 words)

#### Narration

> <bookmark mark='root'/>Let us search a real board. X is to move. Three cells are free: 3, 6, and 8.
>
> <bookmark mark='level1'/>X can play in each free cell. That gives three child boards.
>
> <bookmark mark='level2'/>On each child board, O has two free cells. That gives six boards.
>
> <bookmark mark='owins'/>Two of them are end boards now. O completes the diagonal, so they score minus 10.
>
> <bookmark mark='level3'/>On the other four boards, X puts a mark in the last free cell.
>
> <bookmark mark='xwins'/>Two of these end boards are wins for X. They score 10.
>
> <bookmark mark='draws'/>The other two are full with no line. They score 0.
>
> <bookmark mark='count'/>The tree has fourteen boards. The search calls `_score` thirteen times, one time for each board below the root.

#### Visuals

Use the data in section 5.3. The frame is 14.2 units wide and 8 units high. Use small boards with cell side 0.2 (board side 0.6) and stroke width 2. Marks are 70% of the cell, in X and O colors.

Positions of board centers:

| Node | Position |
|---|---|
| R | (0, 3.0) |
| A | (−4.5, 1.3) |
| B | (0, 1.3) |
| C | (4.5, 1.3) |
| A1 | (−5.6, −0.5) |
| A2 | (−3.4, −0.5) |
| B1 | (−1.1, −0.5) |
| B2 | (1.1, −0.5) |
| C1 | (3.4, −0.5) |
| C2 | (5.6, −0.5) |
| A2a | (−3.4, −2.4) |
| B1a | (−1.1, −2.4) |
| B2a | (1.1, −2.4) |
| C1a | (3.4, −2.4) |

- Edges: lines from the bottom center of the parent to the top center of the child, secondary text color, stroke width 2.
- Edge labels: the cell index of the new mark (for example `3`), font size 18, at the midpoint of the edge, offset 0.2 to the left. Color: blue for X marks (R to A, B, C; and level 2 to level 3), orange for O marks (level 1 to level 2).
- End boards: a line through the winning cells in the winner's color, stroke width 3. Draw boards (B1a, C1a) have no line.
- Score labels on end boards: below each end board, offset 0.55 down, font size 24. `+10` green, `−10` red, `0` grey.
- Legend at the bottom left, (−5.5, −3.6): `me = X`, blue, font size 22.

#### Animation steps

1. `root`: Create board R. Flash cells 3, 6, 8 of R with a white outline (main text color).
2. `level1`: Create the edges R→A, R→B, R→C with their blue labels `3`, `6`, `8`. Then Create boards A, B, C.
3. `level2`: Create the six edges with orange labels (A→A1 `6`, A→A2 `8`, B→B1 `3`, B→B2 `8`, C→C1 `3`, C→C2 `6`). Then Create the six boards.
4. `owins`: On A1 and C2, Create the orange line through cells 2, 4, 6. Write `−10` in red below A1 and C2.
5. `level3`: Create the four edges with blue labels (A2→A2a `6`, B1→B1a `8`, B2→B2a `3`, C1→C1a `6`). Then Create the four boards.
6. `xwins`: On A2a and B2a, Create the blue line through cells 0, 3, 6. Write `+10` in green below A2a and B2a.
7. `draws`: Write `0` in grey below B1a and C1a. Indicate both boards.
8. `count`: Write `14 boards, 13 _score calls` at the bottom right, (4.8, −3.6), main text color, font size 26. Keep all tree objects on screen at the end; scene E4S6 starts with the same tree.

#### Accuracy notes

- The root is `XXO / .OX / .O.` with X to move. Every board, edge, and score must match section 5.3.
- O's line in A1 and C2 is cells 2, 4, 6. X's line in A2a and B2a is cells 0, 3, 6.
- B1a and C1a are the same board, `XXO / OOX / XOX`. A2a and B2a are the same board, `XXO / XOX / XOO`. This is correct: two different paths reach each of these boards. Draw each path as a separate board.
- The tree has 14 boards. `_score` is called 13 times. The root is not given to `_score`; `choose_position` handles the root.

---

### Scene E4S6: Scores Move Up

- **Manim class:** `E4S6BackUp`
- **Target duration:** 65 seconds (145 words)

#### Narration

> <bookmark mark='start'/>Now we move the scores up, from the end boards to the root.
>
> <bookmark mark='single'/>First, the X boards on the third level. Each one has only one child board. So max gives the score of that child: 10, 0, 10, and 0.
>
> <bookmark mark='minA'/>Now O's boards. On the left board, O can win now, or give X a win. The min is minus 10. O takes the win.
>
> <bookmark mark='minB'/>On the middle board, O can make a draw, or give X a win. The min is 0.
>
> <bookmark mark='minC'/>On the right board, O can make a draw, or win. The min is minus 10.
>
> <bookmark mark='maxR'/>Last, the root. It is X's turn, so we use max. The choices are minus 10, 0, and minus 10. The max is 0.
>
> <bookmark mark='move'/>So X plays in cell 6. <bookmark mark='block'/>Look at the board. Cell 6 blocks the O diagonal. The other two moves lose.

#### Visuals

- Start with the full tree from E4S5, at the same positions, with all end-board score labels.
- Remove the text `14 boards, 13 _score calls` at the start.
- For each non-end board, a kind label to the left of the board, offset 0.6 left, font size 20: `max` in blue on R, A2, B1, B2, C1; `min` in orange on A, B, C.
- Score labels for non-end boards: to the right of the board, offset 0.6 right, font size 24, colored by value (`+10` green, `−10` red, `0` grey).
- Moving score: a copy of the child score label moves along the edge to the parent (MoveAlongPath or `.animate.move_to`), then it becomes the parent score label.
- Chosen edge: R→B edge changes to main text color, stroke width 5.
- Losing edges: R→A and R→C change to red, stroke width 2, 50% opacity.
- Result text at bottom right, (4.5, −3.6): `candidates = [(-10, 3), (0, 6), (-10, 8)]`, as a `Code`-style monospace `Text`, font size 22, main text color.

#### Animation steps

1. `start`: FadeOut `14 boards, 13 _score calls`. Write all kind labels (`max`, `min`) at the same time.
2. `single`: For A2, B1, B2, C1, in this order: copy the score label of the child board and move it up along the edge to the right of the parent. Final labels: A2 `+10`, B1 `0`, B2 `+10`, C1 `0`.
3. `minA`: Surround A1 (`−10`) and A2 (`+10`) with a rectangle in main text color. Move a copy of `−10` from A1 up to A. Indicate A1's edge.
4. `minB`: Surround B1 (`0`) and B2 (`+10`). Move a copy of `0` from B1 up to B.
5. `minC`: Surround C1 (`0`) and C2 (`−10`). Move a copy of `−10` from C2 up to C.
6. `maxR`: Surround A, B, C. Move a copy of `0` from B up to R. Write the result text at bottom right.
7. `move`: Change the edge R→B to main text color, stroke width 5. Change edges R→A and R→C to red at 50% opacity. Indicate the edge label `6`.
8. `block`: FadeOut all objects except board R and the result text. Scale board R up to cell side 0.5 and move it to (−5.0, 1.5). Place a blue X in cell 6 of R with a Flash. Draw a dashed orange line through cells 2, 4, 6, then change it to red and FadeOut, to show a blocked line.

#### Accuracy notes

- Min at A: min(−10, 10) = −10. Min at B: min(0, 10) = 0. Min at C: min(0, −10) = −10. Max at R: max(−10, 0, −10) = 0.
- The real `choose_position` output for this root is index 6, `Position(row=2, column=0)`.
- `candidates` from the real code is `[(-10, 3), (0, 6), (-10, 8)]`.
- Do not say that the root has score 0 because "the game is a draw now". Say that with best play from both players, the result is a draw.

---

### Scene E4S7: choose_position

- **Manim class:** `E4S7ChoosePosition`
- **Target duration:** 50 seconds (116 words)

#### Narration

> <bookmark mark='code'/>Here is `choose_position`. It does the root level of the tree.
>
> <bookmark mark='me'/>First, `me` is the current player. The strategy plays for the player whose turn it is. Thus one object can play X or O.
>
> <bookmark mark='cands'/>For each free cell, it puts my mark in the cell. Then it asks `_score` for the score of that child board. The opponent moves next.
>
> <bookmark mark='pairs'/>Each candidate is a pair: the score and the cell index.
>
> <bookmark mark='max'/>Then `max` finds the candidate with the highest score. The strategy returns the position of that cell.
>
> <bookmark mark='result'/>For our small tree, the candidates are minus 10 at cell 3, 0 at cell 6, and minus 10 at cell 8. The result is cell 6.

(Spoken form of `choose_position`: "choose position".)

#### Visuals

- Code panel, right half: snippet S-CHOOSE.
- Left half: board R `XXO / .OX / .O.` (cell side 0.6) at (−4.2, 1.2).
- Candidate list below the board, at (−4.2, −1.6): three rows of monospace text, font size 30:
  - `(-10, 3)` in red
  - `(0, 6)` in grey
  - `(-10, 8)` in red
- Result label below the list, at (−4.2, −3.2): `Position(row=2, column=0)`, main text color, font size 26.

#### Animation steps

1. `code`: Create the S-CHOOSE code panel. Create board R on the left.
2. `me`: Highlight line 4 (`me = game.current_player`) with a rectangle in main text color. Write `me = X` in blue above the board, at (−4.2, 3.0).
3. `cands`: Move the highlight to lines 5 to 9. Indicate `me.opponent` on line 6. Flash cells 3, 6, 8 of the board.
4. `pairs`: Write the three candidate rows one after the other.
5. `max`: Move the highlight to line 10. Surround the row `(0, 6)` with a rectangle in main text color.
6. `result`: Write the result label. Place a blue X in cell 6 of the board.

#### Accuracy notes

- Each candidate is `(score, index)`. The score comes first.
- `choose_position` passes `me.opponent` as `player_to_move`, because after my mark the opponent moves.
- `MinimaxStrategy` is stateless. One object can play both seats. `main.py` uses two `MinimaxStrategy()` objects in the draw match, but one object also works.

---

### Scene E4S8: Ties and Slow Wins

- **Manim class:** `E4S8TiesAndSlowWins`
- **Target duration:** 70 seconds (156 words)

#### Narration

> <bookmark mark='tie'/>What happens when two candidates have the same score? Look at the key in the `max` call. The key is only the score.
>
> <bookmark mark='first'/>When scores are equal, Python's `max` returns the first candidate in the list. The list is in cell order. So a tie goes to the lowest cell index.
>
> <bookmark mark='empty'/>From the empty board, all nine first moves score 0. So minimax always starts in cell 0, the top left corner.
>
> <bookmark mark='board'/>Now look at this board. X is to move. <bookmark mark='now'/>X can win now in cell 7, or in cell 8.
>
> <bookmark mark='slow'/>But cell 5 also scores 10. After cell 5, X has two open lines. O can block only one, so X wins on its next move.
>
> <bookmark mark='pick'/>All three moves score 10. The tie goes to cell 5. Minimax does not take the win now. It wins two moves later.
>
> <bookmark mark='nodiscount'/>Every win scores 10, fast or slow. This code does not prefer a fast win.

#### Visuals

- Part 1 (bookmarks `tie` to `empty`):
  - Code panel, right half: only line 10 of S-CHOOSE, as a one-line `Code` panel: `        _, best_index = max(candidates, key=lambda candidate: candidate[0])`. Strip the leading spaces for this one-line panel only. Center at (3.3, 2.5).
  - Brace under `candidate[0]` with the label `score only`, main text color, font size 26.
  - Left half: empty board (cell side 0.6) at (−4.2, 0.5) with a grey `0` (neutral color, font size 28) in each of the nine cells.
- Part 2 (bookmarks `board` to `nodiscount`):
  - Board `XXO / OX. / O..` (cell side 0.8) at (−3.5, 0.0).
  - Candidate list at (3.5, 0.0), three rows of monospace text, font size 32, all green: `(10, 5)`, `(10, 7)`, `(10, 8)`.
  - Blue dashed lines on the board for X's lines 1, 4, 7 and 0, 4, 8.
  - Label at bottom center, (0, −3.2): `win now: 10    win later: 10`, green, font size 30.

#### Animation steps

1. `tie`: Create the one-line code panel. Create the brace and the label `score only`.
2. `first`: Write, below the code panel at (3.3, 0.8), the text `ties → lowest index`, main text color, font size 30.
3. `empty`: Create the empty board with nine grey `0` labels. Surround cell 0 with a rectangle in main text color. Place a blue X in cell 0 and FadeOut the nine `0` labels.
4. `board`: FadeOut all Part 1 objects. Create the Part 2 board with its marks.
5. `now`: Create the blue dashed line through cells 1, 4, 7 and through cells 0, 4, 8. Flash cells 7 and 8.
6. `slow`: Place a semi-transparent (50% opacity) blue X in cell 5. Then place a semi-transparent orange O in cell 7 (the block), and show the dashed line 0, 4, 8 still open by Indicate. FadeOut the two semi-transparent marks.
7. `pick`: Write the three candidate rows. Surround the row `(10, 5)` with a rectangle in main text color. Place a solid blue X in cell 5.
8. `nodiscount`: Write the label `win now: 10    win later: 10` at bottom center.

#### Accuracy notes

- A tie goes to the **lowest** index, not the highest. The `key` compares only `candidate[0]` (the score). Python `max` returns the first maximal item. The index in the tuple is never compared.
- From the empty board, all nine candidates score 0, and the real strategy selects index 0.
- The Part 2 board is `XXO / OX. / O..`. The real `candidates` list is `[(10, 5), (10, 7), (10, 8)]` and the real result is index 5.
- After X at 5, O can block cell 7 or cell 8. X then wins at the other cell. O cannot win on that move.
- Do not say that the slow win is a mistake that can lose. The strategy still wins. It only does not win in the fewest moves.

---

### Scene E4S9: The Tree Explodes

- **Manim class:** `E4S9Cost`
- **Target duration:** 70 seconds (141 words; the long spoken numbers need extra time)

#### Narration

> <bookmark mark='small'/>Our small tree had fourteen boards. Now start from the empty board.
>
> <bookmark mark='d1'/>X has nine first moves. <bookmark mark='d2'/>For each one, O has eight replies. That is seventy-two boards.
>
> <bookmark mark='grow'/>Each level multiplies again. At depth eight, there are two hundred thousand boards.
>
> <bookmark mark='total'/>For the first move, `_score` runs five hundred forty-nine thousand, nine hundred forty-five times.
>
> <bookmark mark='games'/>Two hundred fifty-five thousand, one hundred sixty-eight of those boards are end boards. That is every possible game of tic-tac-toe.
>
> <bookmark mark='new'/>For each call, the code makes a new board and checks the winning lines. Nothing is reused.
>
> <bookmark mark='time'/>On our test machine, this one first move took about two minutes.
>
> <bookmark mark='table'/>The cost drops fast after that. The second move took fourteen seconds. The third move took less than two seconds. The last moves take a few milliseconds.
>
> <bookmark mark='frontload'/>Most of the cost is in the first two moves.

#### Visuals

- Part 1 (bookmarks `small` to `games`): a bar chart, left two thirds of the screen.
  - Ten horizontal bars, one for each depth 0 to 9, from top (depth 0) at y = 3.0 to bottom (depth 9) at y = −1.5, spacing 0.5.
  - Label at the left of each bar, x = −6.5: `depth 0` to `depth 9`, secondary text color, font size 20.
  - Each bar starts at x = −5.0. Bar length = 8.0 × (boards at that depth) / 200,448. Bar height 0.35. Color: main text color.
  - The count at the right end of each bar, font size 20, main text color: `1`, `9`, `72`, `504`, `3,024`, `15,120`, `54,720`, `148,176`, `200,448`, `127,872`.
  - Note: bars for depth 0 to 3 are very short. Draw them with a minimum length of 0.03 so that they are visible.
  - Big number at bottom, (0, −2.6): `549,945 _score calls`, main text color, font size 44.
  - Below it, (0, −3.4): `255,168 end boards`, secondary text color, font size 30.
- Part 1 opening image (`small`): the 14-board small tree from E4S5 as a tiny group (scale 0.3) at top right (5.5, 2.8), then FadeOut.
- Part 2 (bookmarks `new` to `frontload`):
  - Snippet S-WITHMARK is not shown. Instead, show a row of new-board icons: 12 small boards (cell side 0.12) that appear quickly in a row at y = 2.5, to show "a new board for each call".
  - Clock label at center, (0, 1.0): `first move: 120.8 s`, main text color, font size 48.
  - Table at (0, −1.5), font size 24, columns `move`, `_score calls`, `time`, with rows from section 5.6: moves 1, 2, 3, 4, and 9 only (write `...` between move 4 and move 9).

#### Animation steps

1. `small`: FadeIn the tiny small tree at top right. Then FadeOut it. Create the depth labels.
2. `d1`: GrowFromEdge (left) the bars for depth 0 and depth 1. Write their counts.
3. `d2`: Grow the bar for depth 2. Write `72`.
4. `grow`: Grow the bars for depth 3 to depth 9, one after the other, run time 0.4 seconds each. Write their counts. Indicate the depth 8 bar.
5. `total`: Write `549,945 _score calls` with a counter animation from 0 to 549,945 (use a `DecimalNumber` with `num_decimal_places=0` and `group_with_commas=True`, then add the text ` _score calls`).
6. `games`: Write `255,168 end boards`.
7. `new`: FadeOut all Part 1 objects. Show the 12 board icons one after the other, run time 0.1 seconds each.
8. `time`: FadeOut the board icons. Write `first move: 120.8 s`.
9. `table`: Move the clock label up to (0, 3.0) and scale it to font size 32. Create the table row by row.
10. `frontload`: Surround the rows for move 1 and move 2 with a rectangle in main text color.

#### Accuracy notes

- 549,945 `_score` calls for the first move from the empty board (measured with the real code).
- 255,168 end boards (all possible games). Split from X's point of view: 131,184 wins, 77,904 losses, 46,080 draws. The narration does not need the split.
- 120.8 seconds for one first move, measured on one test machine with Python 3.13.5. Say "on our test machine" and "about two minutes". Do not claim this time for all computers.
- Move 2 took 14.1 seconds (59,704 calls). Move 3 took 1.66 seconds (7,331 calls).
- The number of boards at depth 8 is 200,448. Say "two hundred thousand" in the narration; write `200,448` on screen.
- Do not say "nodes"; say "boards".

---

### Scene E4S10: Minimax Against Minimax

- **Manim class:** `E4S10SelfDraw`
- **Target duration:** 50 seconds (99 words; the nine mark animations need extra time)

#### Narration

> <bookmark mark='match'/>What happens when minimax plays against minimax? The demo runs this match.
>
> <bookmark mark='open'/>X starts in the top left corner. This is the tie-break at work. O takes the center. Every other reply loses against best play.
>
> <bookmark mark='blocks'/>Now watch the blocks. O blocks the top row. X blocks the diagonal. O blocks the left column. X blocks the middle row.
>
> <bookmark mark='end'/>The last two marks fill the board. No player has a line.
>
> <bookmark mark='events'/>The bus prints `MarkPlaced`, then `GameDrawn`. The status is a draw.
>
> <bookmark mark='meaning'/>Two perfect players cannot beat each other. With best play, tic-tac-toe is a draw. Minimax never loses.

(Spoken forms: `MarkPlaced` is "mark placed", `GameDrawn` is "game drawn".)

#### Visuals

- Header at top center, (0, 3.4): `MinimaxStrategy (X) vs MinimaxStrategy (O)`, main text color, font size 32.
- Board (cell side 1.2, the standard board) at left center, (−3.0, −0.3).
- Move list at right, (4.0, 0.0), monospace text, font size 26. One row for each move: `1  X  0`, `2  O  4`, and so on to `9  X  8`. X rows blue, O rows orange.
- Block arrows: for each block, a dashed line in the blocked player's color through the blocked line, which then turns red and fades out.
- Event cards at bottom right, (4.0, −2.8): two event cards side by side, `MarkPlaced` and `GameDrawn`, using `make_event_card()` (green, event color).
- Final label under the board, (−3.0, −2.6): `GameStatus.DRAW`, grey (neutral color), font size 32.

#### Animation steps

1. `match`: Write the header. Create the empty board.
2. `open`: Place X in cell 0 and add row `1  X  0`. Place O in cell 4 and add row `2  O  4`. Indicate cell 4.
3. `blocks`: Place the marks for moves 3 to 7 with their rows. After each block move, show its block line:
   - Move 3: X in cell 1 (no block line).
   - Move 4: O in cell 2. Dashed blue line through 0, 1, 2, then red, then FadeOut.
   - Move 5: X in cell 6. Dashed orange line through 2, 4, 6, then red, then FadeOut.
   - Move 6: O in cell 3. Dashed blue line through 0, 3, 6, then red, then FadeOut.
   - Move 7: X in cell 5. Dashed orange line through 3, 4, 5, then red, then FadeOut.
4. `end`: Place O in cell 7 and X in cell 8, with their rows.
5. `events`: FadeIn the `MarkPlaced` card, then the `GameDrawn` card.
6. `meaning`: Write `GameStatus.DRAW` under the board in grey.

#### Accuracy notes

- The real move order is X0, O4, X1, O2, X6, O3, X5, O7, X8. The final board is `XXO / OOX / XOX`.
- The last two events are `MarkPlaced` and `GameDrawn`. The final status is `GameStatus.DRAW`.
- O at 4 is the only move-2 candidate with score 0. All other O candidates score −10.
- Move 3 (X at 1) is a tie-break: all seven candidates score 0.
- "Minimax never loses" is a claim about correct play in tic-tac-toe. The demo shows one game. Do not say that the demo proves it.

---

### Scene E4S11: Too Slow to Train With

- **Manim class:** `E4S11TooSlow`
- **Target duration:** 45 seconds (98 words)

#### Narration

> <bookmark mark='idea'/>A perfect player sounds like the best teacher. Later, a program learns by playing thousands of games against an opponent.
>
> <bookmark mark='games'/>The demo trains each learner for six thousand games.
>
> <bookmark mark='estimate'/>Suppose minimax plays O. Its first move in each game takes more than ten seconds. Six thousand games take more than sixteen hours.
>
> <bookmark mark='worse'/>Suppose minimax plays X. Its first move takes about two minutes. Six thousand games take more than eight days.
>
> <bookmark mark='rule'/>So the project does not use minimax as a training opponent. In pure Python, it is too slow.
>
> <bookmark mark='instead'/>The learners in later videos train against faster opponents.

#### Visuals

- Top center, (0, 3.2): `EPISODES = 6000`, monospace, main text color, font size 36.
- Two estimate rows, left aligned at x = −5.5:
  - y = 1.2: `minimax as O: > 10 s per game  →  > 16 hours`, orange, font size 30.
  - y = 0.0: `minimax as X: ≈ 2 min per game  →  > 8 days`, blue, font size 30.
- Label under the rows, (0, −1.0): `estimate from measured times`, secondary text color, font size 22.
- A rule box at bottom center, (0, −2.6): rounded rectangle, purple stroke (rule color), with the text `MinimaxStrategy: too slow to use as a training opponent`, main text color, font size 28.

#### Animation steps

1. `idea`: FadeIn a small standard-style board icon (cell side 0.3) at (−4.0, 2.2) and a second one at (−2.8, 2.2), with a two-headed arrow between them, main text color. FadeOut them at the end of the block.
2. `games`: Write `EPISODES = 6000`.
3. `estimate`: Write the orange row. Write the estimate label.
4. `worse`: Write the blue row.
5. `rule`: Create the purple rule box and its text.
6. `instead`: Indicate the rule box.

#### Accuracy notes

- These are estimates, not measured training runs. The screen must show the label `estimate from measured times`.
- O's first move costs 55,504 to 63,904 `_score` calls, which depends on X's first cell. Move 2 in the real game took 14.1 seconds with 59,704 calls.
- X's first move costs 549,945 calls and took 120.8 seconds.
- `AGENTS.md` states that `MinimaxStrategy` is too slow in pure Python to use as a training opponent.
- Do not name `ThreatBuilderStrategy` or describe it in this scene. Video 6 introduces it.
- Do not name the learners' algorithms here.

---

## 7. Closing and hook

### Scene E4S12: Closing and Hook

- **Manim class:** `E4S12Hook`
- **Target duration:** 30 seconds (59 words, plus a 2-second hold)

#### Narration

> <bookmark mark='two'/>We now have two strategies. The naive strategy is fast, but it loses. Minimax is perfect, but it is slow.
>
> <bookmark mark='human'/>Both have one thing in common. A human wrote every rule. And minimax searches everything.
>
> <bookmark mark='question'/>Can a program learn good moves from experience instead? It can play many games, keep the results, and change its choices.
>
> <bookmark mark='next'/>Next: reinforcement learning.

#### Visuals

- Two columns.
  - Left column, center x = −3.5: title `FirstAvailableStrategy`, main text color, font size 30, at y = 2.5. Below it: `fast` in green at y = 1.6 and `loses` in red at y = 1.0, font size 28.
  - Right column, center x = 3.5: title `MinimaxStrategy`, main text color, font size 30, at y = 2.5. Below it: `never loses` in green at y = 1.6 and `slow` in red at y = 1.0.
- Center, (0, −0.4): `written by a human`, purple (rule color), font size 34.
- Center, (0, −1.6): `Can a program learn good moves from experience?`, main text color, font size 34.
- Bottom center, (0, −3.0): `Next: Learning from Rewards`, main text color, font size 40.

#### Animation steps

1. `two`: Write both column titles. Then Write `fast`, `loses`, `never loses`, `slow`.
2. `human`: Write `written by a human` in purple. Create a purple bracket (Brace) above it that spans both columns.
3. `question`: FadeOut the brace. Write the question text.
4. `next`: Write `Next: Learning from Rewards`. Hold for 2 seconds. FadeOut all objects.

#### Accuracy notes

- The next video is video 5, "Learning from Rewards". Its learner is a linear softmax policy. Do not name the learner or its method in this scene.
- Do not say that the next learner uses a table of move scores for each board.

## 8. Checks

Answer each question with yes or no. Each "no" is a problem to record in `QUESTIONS.md`.

1. Does the recap (E4S1) take 20 seconds or less?
2. Is every code panel an exact copy of a snippet in section 5.1 (no changed names, no changed spacing inside a line)?
3. Are the end scores shown as `+10`, `−10`, and `0` (not `+1` or `−1`), with green, red, and grey?
4. Does the small tree in E4S5 and E4S6 use the root `XXO / .OX / .O.` and match every board and score in section 5.3?
5. Does the root of the small tree get score 0, with candidates `(-10, 3)`, `(0, 6)`, `(-10, 8)`, and the move at cell 6?
6. Are `max` labels blue (X, `me`) and `min` labels orange (O, opponent) in E4S6?
7. Does the video say that a tie goes to the **lowest** cell index (never the highest)?
8. Does E4S8 show the board `XXO / OX. / O..` with candidates `(10, 5)`, `(10, 7)`, `(10, 8)`, and the move at cell 5?
9. Does the video say that the code does not prefer a fast win, and does it avoid saying that the slow win can lose?
10. Does E4S9 show 549,945 `_score` calls and 255,168 end boards for the first move?
11. Does E4S9 say that the two-minute time is from one test machine?
12. Does E4S10 show the moves X0, O4, X1, O2, X6, O3, X5, O7, X8, and end with `MarkPlaced`, `GameDrawn`, and `GameStatus.DRAW`?
13. Does E4S11 label the training times as an estimate?
14. Does the narration use "board" and "end board" (not "node", "leaf", "state", or "position" for a board)?
15. Does the hook name "reinforcement learning" and avoid naming the video 5 learner's method?
16. Is the total length between 8 and 12 minutes, and is each scene between 20 and 90 seconds?
17. Are all text objects inside the frame, with no overlap in the tree scenes?
18. Does every sentence of narration follow the STE rules (active voice, short sentences)?
