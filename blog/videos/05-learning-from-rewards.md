# Episode 5: Learning from Rewards

## 1. Header

- **Series:** Who Decides the Next Move?
- **Episode number:** 5
- **Title:** Learning from Rewards
- **Target length:** 12 minutes 15 seconds of narration (15 scenes). Animation pauses can add up to 30 seconds.
- **Source files:**
  - `src/tictactoe/learning.py` (`Experience`, `ReinforcementLearner`, `_features`, `PolicyLearner`)
  - `src/tictactoe/trainer.py` (`TrainingSummary`, `_reward`, `Trainer`)
  - `main.py` (training section)
- **Source article:** `blog/articles/03-policy-learner.md` (all sections)

## 2. Goal

After the video, the viewer can explain how a program learns tic-tac-toe from rewards. The viewer can tell how the `PolicyLearner` reads a board as 10 player-relative features, how a table of 9 × 10 weights gives one logit for each free cell, and how softmax changes the logits into move probabilities. The viewer can tell how the `Trainer` gives the same final reward to all moves of one game, and how the policy-gradient update (the REINFORCE rule) with a per-board value baseline makes a good move more probable. The viewer can also tell the two limits of this learner: it learns only what its opponent teaches, and a weighted sum cannot combine features.

## 3. Recap from the last video

Maximum 20 seconds. This is scene `E5S1`. In video 4, the `MinimaxStrategy` searched the full game tree. It never loses. But a person wrote all of its logic, and in pure Python it is slow. This video lets the program find its own moves.

## 4. Terms

Use each term with exactly this name. Do not use synonyms.

| Term | Definition |
|------|------------|
| reinforcement learning | A method where a program learns by trial and error from rewards. |
| state | One board position: one arrangement of X marks, O marks, and empty cells. |
| policy | The rule that gives each free cell a probability for the next move. |
| reward | The result of a game from the learner's side: +1 for a win, 0 for a draw, −1 for a loss. |
| episode | One full training game, from the empty board to a win or a draw. |
| `ReinforcementLearner` | A `Protocol` with two methods: `choose_position` (the same as `Strategy`) and `learn`. |
| `Experience` | A frozen record of one learner move: `board`, `player`, `action`, `reward`. |
| feature | One number that describes the board to the learner. The learner uses 10 features. |
| player-relative | The features describe the board from the side of the player to move: my mark is +1, the opponent mark is −1. |
| bias | The tenth feature. It is always 1. |
| weight table | The `PolicyLearner` weights: 9 rows (one row for each move) × 10 columns (one column for each feature). |
| linear softmax policy | The `PolicyLearner` policy: a weighted sum for each free cell, then softmax over the free cells. |
| logit | The weighted sum for one free cell: the raw score before softmax. |
| softmax | The function that changes logits into probabilities that are all positive and have a sum of 1. |
| explore | The mode `explore=True`: the learner samples a move from the probabilities. Training uses this mode. |
| greedy | The mode `explore=False`: the learner plays the cell with the highest probability. |
| value | `V(board)`: the learner's estimate of the reward from one board. One number for each board in the value table. |
| value table | `self._values`: a dictionary from `Board` to value. |
| advantage | `reward − V(board)`: how much better or worse the result was than the value. |
| policy gradient | A learning rule that changes the weights so that moves with a positive advantage become more probable. |
| REINFORCE rule | The policy-gradient rule that uses the full game reward for each move. |
| per-board value baseline | The value `V(board)` that the update subtracts from the reward. |
| `Trainer` | The application service that plays training games and calls `learn`. |
| `TrainingSummary` | A frozen record with `wins`, `draws`, `losses`, from the learner's side. |
| overfitting | A learner is good against its training opponent only, and not against other opponents. |
| feature interaction | An effect that exists only when two or more features have given values together. |

## 5. Source facts

### 5.1 Code snippets

Copy each snippet exactly. Keep the leading spaces as they are shown.

**Snippet A: `ReinforcementLearner`** (`src/tictactoe/learning.py`)

```python
class ReinforcementLearner(Protocol):
    def choose_position(self, game: Game) -> Position: ...

    def learn(self, experience: Experience) -> None: ...
```

**Snippet B: `Experience`** (`src/tictactoe/learning.py`)

```python
@dataclass(frozen=True, slots=True)
class Experience:
    board: Board
    player: Player
    action: Position
    reward: float
```

**Snippet C: `_features`** (`src/tictactoe/learning.py`)

```python
def _features(board: Board, player: Player) -> tuple[float, ...]:
    opponent = player.opponent
    values = []
    for index in range(_ACTIONS):
        mark = board.player_at(Position.from_index(index))
        if mark == player:
            values.append(1.0)
        elif mark == opponent:
            values.append(-1.0)
        else:
            values.append(0.0)
    values.append(1.0)
    return tuple(values)
```

**Snippet D: constructor** (`src/tictactoe/learning.py`)

```python
class PolicyLearner:
    def __init__(self, learning_rate: float = 0.1, value_rate: float = 0.9, rng: random.Random | None = None) -> None:
        self._learning_rate = learning_rate
        self._value_rate = value_rate
        self._values: dict[Board, float] = {}
        self._rng = rng if rng is not None else random.Random()
        self._weights = [[0.0 for _ in range(_FEATURES)] for _ in range(_ACTIONS)]
```

The first line of `__init__` is long. Scale the code panel down so the full line fits in the right half. Do not wrap or change the line.

**Snippet E: `_probabilities`** (`src/tictactoe/learning.py`)

```python
    def _probabilities(self, board: Board, player: Player) -> tuple[tuple[int, ...], tuple[float, ...]]:
        free = tuple(index for index in range(_ACTIONS) if not board.is_occupied(Position.from_index(index)))
        features = _features(board, player)
        logits = [
            sum(weight * feature for weight, feature in zip(self._weights[action], features))
            for action in free
        ]
        peak = max(logits)
        exps = [math.exp(logit - peak) for logit in logits]
        total = sum(exps)
        return free, tuple(expired / total for expired in exps)
```

**Snippet F: `choose_position`** (`src/tictactoe/learning.py`)

```python
    def choose_position(self, game: Game, explore: bool = True) -> Position:
        free, probabilities = self._probabilities(game.board, game.current_player)
        if not explore:
            best = max(range(len(free)), key=lambda position: probabilities[position])
            return Position.from_index(free[best])
        roll = self._rng.random()
        cumulative = 0.0
        for action, probability in zip(free, probabilities):
            cumulative += probability
            if roll < cumulative:
                return Position.from_index(action)
        return Position.from_index(free[-1])
```

**Snippet G1: `Trainer.train`, part 1** (`src/tictactoe/trainer.py`)

```python
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
```

**Snippet G2: `Trainer.train`, part 2** (`src/tictactoe/trainer.py`)

```python
            for board, action in moves:
                learner.learn(Experience(board, seat, action, _reward(seat, game.status)))
            if _reward(seat, game.status) > 0.0:
                wins += 1
            elif _reward(seat, game.status) == 0.0:
                draws += 1
            else:
                losses += 1
        return TrainingSummary(wins, draws, losses)
```

**Snippet H: `_reward`** (`src/tictactoe/trainer.py`)

```python
def _reward(player: Player, status: GameStatus) -> float:
    if status is GameStatus.DRAW:
        return 0.0
    winner = X if status is GameStatus.X_WON else O
    return 1.0 if player == winner else -1.0
```

**Snippet I1: `learn`, the value baseline** (`src/tictactoe/learning.py`)

```python
    def learn(self, experience: Experience) -> None:
        value = self._values.get(experience.board, 0.0)
        advantage = experience.reward - value
        self._values[experience.board] = self._value_rate * value + (1.0 - self._value_rate) * experience.reward
```

**Snippet I2: `learn`, the weight update** (`src/tictactoe/learning.py`)

```python
        free, probabilities = self._probabilities(experience.board, experience.player)
        features = _features(experience.board, experience.player)
        for position, action in enumerate(free):
            indicator = 1.0 if action == experience.action.index else 0.0
            scale = self._learning_rate * advantage * (indicator - probabilities[position])
            if scale == 0.0:
                continue
            weight = self._weights[action]
            for feature_index in range(_FEATURES):
                weight[feature_index] += scale * features[feature_index]
```

**Snippet J: training in `main.py`**

```python
    x_learner = PolicyLearner(learning_rate=0.1, rng=random.Random(0))
    x_summary = Trainer().train(x_learner, X, FirstAvailableStrategy(), EPISODES)
    o_learner = PolicyLearner(learning_rate=0.1, rng=random.Random(1))
    o_summary = Trainer().train(o_learner, O, FirstAvailableStrategy(), EPISODES)
    print(f"tabular X vs naive: won {x_summary.wins}, drew {x_summary.draws}, lost {x_summary.losses}")
    print(f"tabular O vs naive: won {o_summary.wins}, drew {o_summary.draws}, lost {o_summary.losses}")
```

**Snippet K: the demo matches after training** (`main.py`)

```python
    run_match(engine, FirstAvailableStrategy(), o_learner, explore=False)
    run_match(engine, x_learner, o_learner, explore=False)
```

### 5.2 Constants and structure facts

- `_ACTIONS = SIZE * SIZE` = 9. `_FEATURES = _ACTIONS + 1` = 10.
- The weight table has 9 × 10 = 90 weights. All weights start at `0.0`.
- Row `a` of the weight table belongs to move (cell) `a`. Column `i` belongs to feature `i`. Columns 0 to 8 are the cells. Column 9 is the bias.
- Defaults: `learning_rate = 0.1`, `value_rate = 0.9`. `main.py` sets `learning_rate=0.1` and seeds `random.Random(0)` for the X learner and `random.Random(1)` for the O learner.
- `EPISODES = 6000` in `main.py`. Each learner trains 6000 episodes against `FirstAvailableStrategy`.
- `FirstAvailableStrategy` always plays the free cell with the lowest index.
- The `Trainer` drives the `Game` aggregate directly. It uses no engine and no event bus.
- Softmax is over the free cells only. Occupied cells get no probability.
- The code subtracts the largest logit (`peak`) before `math.exp`. This does not change the probabilities. It prevents very large numbers.
- The value table key is the full `Board`. A new board has value `0.0`.
- Value update: `V ← 0.9 · V + 0.1 · reward`.
- Weight update for each free cell `a`: `weights[a] += learning_rate · advantage · (indicator − probability[a]) · features`. `indicator` is 1 for the played cell and 0 for other free cells. Rows of occupied cells do not change.
- After training (the `main.py` seeds): the X learner value table has 87 boards. The O learner value table has 38 boards.
- A raw logit gap of 2 gives probabilities 0.88 and 0.12 (e² / (1 + e²) = 0.8808).

### 5.3 Real numbers used on screen

All numbers come from the snippets in section 5.6. Round as shown.

**Board B1** (from the real demo game `FirstAvailableStrategy` (X) vs `PolicyLearner` (O), before O's second move). X on cells 0 and 1. O on cell 2. O to move. The learner is the trained O learner.

```
 X | X | O
---+---+---
   |   |
---+---+---
   |   |
```

- Features for O: `[−1, −1, +1, 0, 0, 0, 0, 0, 0, 1]`.
- Weight rows of the trained O learner (columns 0 to 9):
  - Row 7: `[−1.022, −0.616, +1.004, −0.931, +0.068, −0.251, −0.045, 0.000, +0.771, +1.022]`
  - Row 8: `[−0.334, −0.522, +0.934, −0.413, −1.185, +0.763, +0.159, +0.264, 0.000, +0.334]`
  - Row 6: `[−0.685, +0.574, −0.245, −0.297, +0.492, −0.617, 0.000, +0.187, −0.093, +0.685]`
- Logit of cell 7, term by term (only the non-zero features give a term):
  `(−1.022)(−1) + (−0.616)(−1) + (1.004)(+1) + (1.022)(1) = 1.022 + 0.616 + 1.004 + 1.022 = 3.663` (the four terms add to 3.664; the exact sum is 3.6633, so show `3.66`).
- Logits and probabilities for all free cells:

| Cell | Logit | Probability (2 decimals) | Cumulative (4 decimals) |
|------|-------|--------------------------|-------------------------|
| 3 | −4.93 | 0.00 | 0.0001 |
| 4 | −4.91 | 0.00 | 0.0003 |
| 5 | −2.65 | 0.00 | 0.0017 |
| 6 | +0.55 | 0.04 | 0.0370 |
| 7 | +3.66 | 0.79 | 0.8298 |
| 8 | +2.12 | 0.17 | 1.0000 |

- Greedy choice: cell 7. This agrees with the real demo game (O played cell 7).
- Sampling examples: a roll of 0.50 picks cell 7 (0.0370 ≤ 0.50 < 0.8298). A roll of 0.90 picks cell 8.

**Board B2** (same demo game, before O's third move). X on 0, 1, 3. O on 2, 7. O to move. X threatens to win on cell 6 (line 0-3-6).

```
 X | X | O
---+---+---
 X |   |
---+---+---
   | O |
```

- Trained O learner: cell 4 → 0.00, cell 5 → 0.00, cell 6 → 0.15 (0.1458), cell 8 → 0.85 (0.8528).
- Greedy choice: cell 8. It does not block cell 6. The real demo game agrees.
- The value of B2 in the O learner value table is 1.00. The naive X player never takes cell 6 here, because cell 4 is free and has a lower index.
- Next in the real game: X plays 4 (lowest free cell). O plays 6 and wins on line 6-7-8.

**Board B3** (from the real demo game `PolicyLearner` (X) vs `PolicyLearner` (O), before X's third move). X on 2, 4. O on 6, 8. X to move. O threatens to win on cell 7 (line 6-7-8).

```
   |   | X
---+---+---
   | X |
---+---+---
 O |   | O
```

- Trained X learner: cell 0 → 0.23, cell 1 → 0.06, cell 3 → 0.19, cell 5 → 0.29, cell 7 → 0.24 (0.2350).
- Greedy choice: cell 5. It does not block cell 7. O then plays 7 and wins.
- B3 is not in the X learner value table. The X learner never saw this board in training.

**One update with real numbers** (a new `PolicyLearner`, all weights 0.0). Board U: X on cell 0, O to move. Experience: `board` = U, `player` = O, `action` = cell 4, `reward` = +1.0.

```
 X |   |
---+---+---
   |   |
---+---+---
   |   |
```

- Features for O: `[−1, 0, 0, 0, 0, 0, 0, 0, 0, 1]`.
- Before: all 8 free cells (1 to 8) have logit 0 and probability 0.125 (show `0.13` in the heat map, and `0.125` in the formula).
- `V(U)` before = 0.0. `advantage` = 1.0 − 0.0 = 1.0.
- `V(U)` after = 0.9 · 0.0 + 0.1 · 1.0 = 0.1.
- Played cell 4: `scale` = 0.1 · 1.0 · (1 − 0.125) = 0.0875. Row 4 becomes `[−0.0875, 0, 0, 0, 0, 0, 0, 0, 0, +0.0875]`.
- Each other free cell (for example cell 1): `scale` = 0.1 · 1.0 · (0 − 0.125) = −0.0125. Row 1 becomes `[+0.0125, 0, 0, 0, 0, 0, 0, 0, 0, −0.0125]`.
- Row 0 (occupied cell) does not change.
- After: logit of cell 4 = 0.175. Logit of each other free cell = −0.025.
- After: probability of cell 4 = 0.1486 (show `0.15`). Probability of each other free cell = 0.1216 (show `0.12`).
- A second win from the same board and the same move: `V(U)` = 0.19, `advantage` = 0.9, probability of cell 4 = 0.1721 (show `0.17`), others 0.1183 (show `0.12`).

**Value and advantage after repeated wins from one board** (reward +1 each time):

| Win number | V before | advantage |
|------------|----------|-----------|
| 1 | 0.00 | 1.00 |
| 2 | 0.10 | 0.90 |
| 3 | 0.19 | 0.81 |
| 4 | 0.27 | 0.73 |
| 5 | 0.34 | 0.66 |

After 5 wins, `V` = 0.41. A loss (reward −1) from that board gives `advantage` = −1 − 0.41 = −1.41.

### 5.4 Demo results (real output of `uv run main.py`)

```text
Training tabular X and O PolicyLearners over 6000 episodes each
tabular X vs naive: won 5968, drew 7, lost 25
tabular O vs naive: won 5960, drew 11, lost 29
```

Real game 1, `FirstAvailableStrategy` (X) vs `PolicyLearner` (O), greedy. Moves in order: X 0, O 2, X 1, O 7, X 3, O 8, X 4, O 6. Result: `GameStatus.O_WON` (line 6-7-8). Final board:

```
 X | X | O
---+---+---
 X | X |
---+---+---
 O | O | O
```

Real game 2, `PolicyLearner` (X) vs `PolicyLearner` (O), greedy. Moves in order: X 2, O 6, X 4, O 8, X 5, O 7. Result: `GameStatus.O_WON` (line 6-7-8). Final board:

```
   |   | X
---+---+---
   | X | X
---+---+---
 O | O | O
```

**Blocking test** (section 5.6, snippet S4). The test uses all legal boards where the opponent has exactly one open two-in-a-row and the learner has no win on this move. It counts how often the greedy move blocks.

| Learner | Boards | Greedy blocks | Block rate | Rate of a random move |
|---------|--------|---------------|------------|-----------------------|
| Trained O learner | 580 | 170 | 29% | 30% |
| Trained X learner | 396 | 145 | 37% | 33% |

Of these boards, the O learner saw 13 in training and the X learner saw 7.

**Baseline test** (section 5.6, snippet S5). `value_rate=1.0` keeps every value at 0.0, so `advantage` = `reward`. This is the same learner without a baseline.

Seat X, `learning_rate=0.1`, `random.Random(0)`, 6000 episodes in 12 blocks of 500. Results are won/drew/lost.

| Opponent | `value_rate` | Total (6000) | First 500 | Last 500 |
|----------|--------------|--------------|-----------|----------|
| `FirstAvailableStrategy` | 0.9 (baseline) | 5968 / 7 / 25 | 477 / 5 / 18 | 500 / 0 / 0 |
| `FirstAvailableStrategy` | 1.0 (no baseline) | 5959 / 0 / 41 | 475 / 0 / 25 | 500 / 0 / 0 |
| `ThreatBuilderStrategy(random.Random(7))` | 0.9 (baseline) | 1989 / 3612 / 399 | 50 / 171 / 279 | 175 / 322 / 3 |
| `ThreatBuilderStrategy(random.Random(7))` | 1.0 (no baseline) | 3311 / 1502 / 1187 | 95 / 147 / 258 | 348 / 94 / 58 |

Losses in each block of 500 against `ThreatBuilderStrategy`:

- With the baseline: 279, 50, 20, 10, 6, 8, 9, 3, 4, 3, 4, 3.
- Without the baseline: 258, 132, 115, 97, 88, 81, 76, 67, 76, 69, 70, 58.

Findings:

- Against the naive opponent, the baseline makes almost no difference. Both learners win almost all games.
- Against an opponent that builds threats, the learner without the baseline wins more but loses about 20 times more often in the last block (58 vs 3). Its losses fall slowly and go up and down. The learner with the baseline plays safely: few losses, many draws.
- This test does not show a strong oscillation or a clear "unlearning". `AGENTS.md` claims both. The episode states only the measured difference.
- The O seat was not tested with `ThreatBuilderStrategy`.

### 5.5 Differences between the article, `AGENTS.md`, and the code

The code wins in each case. The narration follows the right column.

| Source says | Code and tests show | Episode uses |
|-------------|---------------------|--------------|
| Article title and text: "a table of move-scores"; `main.py` output and article: "tabular" | Move scores are computed as weighted sums of 10 features. Only the value table stores one number for each board. | "linear softmax policy", "a table of weights" |
| Article and `AGENTS.md`: "actor-critic" | `learn` moves `V` toward the final reward. It never uses the value of the next board. | "REINFORCE with a learned baseline", then "a simple form of actor-critic" |
| Article and `AGENTS.md`: without a baseline the policy "oscillates" and "can even unlearn" | Snippet S5: no visible difference against the naive opponent. Against `ThreatBuilderStrategy`, many more losses without the baseline (58 vs 3 in the last 500), but no clear oscillation. | Only the measured loss numbers |
| Article: the bias is "a small starting position so every cell has a baseline to tilt" | The bias is a constant feature `1.0`. Its weight gives each move a score that does not depend on the board. | "the bias", always 1 |
| `AGENTS.md`: trained against the naive opponent, the learner "never learns to block" | Snippet S4: greedy block rate 29% (O) and 37% (X), random rate 30% and 33%. | "almost no better than random at blocking" |
| Article, last section: the next model is needed because the linear policy cannot combine cells | True in principle (scene `E5S14`). But against `ThreatBuilderStrategy`, the linear learner in seat X got 1989 / 3612 / 399 over 6000 episodes. The `main.py` neural learner in seat X got 1902 / 3220 / 878 with the same seeds (`random.Random(0)` for the learner, `random.Random(7)` for the opponent). | The hook states the model limit only. It does not claim that the network gets better results. |

### 5.6 Reproduce the numbers

Run each snippet from the project root with `uv run python <file>`. S1 trains the two learners with the `main.py` settings (about 18 seconds each) and saves them. S2 to S4 load the saved learners.

**S1: train and save, check the summaries**

```python
import random, pickle
from tictactoe import *
x = PolicyLearner(learning_rate=0.1, rng=random.Random(0))
print("X", Trainer().train(x, X, FirstAvailableStrategy(), 6000))
o = PolicyLearner(learning_rate=0.1, rng=random.Random(1))
print("O", Trainer().train(o, O, FirstAvailableStrategy(), 6000))
pickle.dump((x, o), open("/tmp/e5/learners.pkl", "wb"))
print("values table sizes", len(x._values), len(o._values))
```

Output: `X TrainingSummary(wins=5968, draws=7, losses=25)`, `O TrainingSummary(wins=5960, draws=11, losses=29)`, `values table sizes 87 38`.

**S2: features, logits, probabilities for B1, B2, B3**

```python
import pickle
from tictactoe import *
from tictactoe.learning import _features
from tictactoe.value_objects import Board, Position
def board_from(xs, os):
    b = Board.empty()
    for i in xs: b = b.with_mark(Position.from_index(i), X)
    for i in os: b = b.with_mark(Position.from_index(i), O)
    return b
x, o = pickle.load(open("/tmp/e5/learners.pkl", "rb"))
def show(learner, b, player):
    f = _features(b, player)
    free, p = learner._probabilities(b, player)
    print("features", f, "V", learner._values.get(b))
    c = 0
    for a, q in zip(free, p):
        c += q
        logit = sum(w * v for w, v in zip(learner._weights[a], f))
        print(f"cell {a}: logit {logit:+.3f} prob {q:.4f} cum {c:.4f} row {[round(w, 3) for w in learner._weights[a]]}")
show(o, board_from([0, 1], [2]), O)
show(o, board_from([0, 1, 3], [2, 7]), O)
show(x, board_from([2, 4], [6, 8]), X)
```

**S3: one update on a new learner, and the value sequence**

```python
import random
from tictactoe import *
from tictactoe.learning import _features
from tictactoe.value_objects import Board, Position
L = PolicyLearner(learning_rate=0.1, rng=random.Random(0))
b = Board.empty().with_mark(Position.from_index(0), X)
print("before", L._probabilities(b, O))
L.learn(Experience(b, O, Position.from_index(4), 1.0))
print("V", L._values[b], "row4", L._weights[4], "row1", L._weights[1], "row0", L._weights[0])
print("after", L._probabilities(b, O))
L.learn(Experience(b, O, Position.from_index(4), 1.0))
print("after second win", L._values[b], L._probabilities(b, O))
M = PolicyLearner()
for i in range(5):
    v = M._values.get(b, 0.0)
    print("win", i + 1, "V before", round(v, 4), "advantage", round(1.0 - v, 4))
    M.learn(Experience(b, O, Position.from_index(4), 1.0))
print("V after 5 wins", round(M._values[b], 4), "loss advantage", round(-1.0 - M._values[b], 4))
```

**S4: blocking test**

```python
import pickle, itertools
from tictactoe import *
from tictactoe.value_objects import Board, Position
LINES = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
x, o = pickle.load(open("/tmp/e5/learners.pkl", "rb"))
def threats(cells, me):
    return {c for l in LINES for c in l if cells[c] is None and sum(cells[i] == me for i in l) == 2}
def won(cells, p):
    return any(all(cells[i] == p for i in l) for l in LINES)
def run(learner, mover):
    other = O if mover == X else X
    total = block = seen = 0
    chance = 0.0
    for assign in itertools.product([None, X, O], repeat=9):
        nx = sum(a == X for a in assign); no = sum(a == O for a in assign)
        if mover == O and nx != no + 1: continue
        if mover == X and nx != no: continue
        if won(assign, X) or won(assign, O) or None not in assign: continue
        if threats(assign, mover): continue
        t = threats(assign, other)
        if len(t) != 1: continue
        b = Board.empty()
        for i, a in enumerate(assign):
            if a is not None: b = b.with_mark(Position.from_index(i), a)
        free, p = learner._probabilities(b, mover)
        best = free[max(range(len(free)), key=lambda k: p[k])]
        total += 1; block += best in t; chance += 1 / len(free); seen += b in learner._values
    print(mover.symbol, total, block, block / total, chance / total, seen)
run(o, O); run(x, X)
```

**S5: baseline test**

```python
import random
from tictactoe import *
for opponent_name in ("naive", "threat"):
    for vr in (0.9, 1.0):
        L = PolicyLearner(learning_rate=0.1, value_rate=vr, rng=random.Random(0))
        opp = FirstAvailableStrategy() if opponent_name == "naive" else ThreatBuilderStrategy(random.Random(7))
        t = Trainer()
        rows = []
        for block in range(12):
            s = t.train(L, X, opp, 500)
            rows.append((s.wins, s.draws, s.losses))
        print(opponent_name, vr, [sum(r[i] for r in rows) for i in range(3)], rows)
```

The run takes about 3 minutes. The `ThreatBuilderStrategy` part takes about 2 minutes. Calling `train` 12 times with 500 episodes gives the same result as one call with 6000 episodes for the naive opponent (the totals agree with `main.py`), because the learner keeps its state between calls.

## 6. Scenes

### Layout rules for all scenes

- Frame: 14.2 units wide, 8 units high. The center is (0, 0).
- "Left half" means the object center is at x = −3.5. "Right half" means x = +3.5.
- Board: use `make_board()`. Cell side 1.2, so the board is 3.6 units wide. Default board center: (−3.5, 0.3).
- Scene title: `Text`, font size 40, `TEXT_COLOR`, at the top edge (`to_edge(UP, buff=0.4)`).
- Feature vector: a row of 10 small squares (side 0.55) with a number in each square. Colors of the number and the square stroke: +1 `POSITIVE_COLOR`, −1 `NEGATIVE_COLOR`, 0 `NEUTRAL_COLOR`. Put small grey labels `0` to `8` and `b` (bias) under the squares.
- Weight numbers: positive `POSITIVE_COLOR`, negative `NEGATIVE_COLOR`, zero `NEUTRAL_COLOR`.
- Heat map: use `heat_map()`. Fill each free cell with `POSITIVE_COLOR` at opacity equal to the probability. Write the probability with two decimals.
- Use `Text` with Unicode symbols (`·`, `−`, `←`, `×`, `Σ`). Do not use `MathTex`.
- Do not show the terms "feedforward", "neural network", or "a table of move scores" before scene `E5S15`.

---

### E5S1: Recap

- **Manim class:** `E5S1Recap`
- **Target duration:** 20 seconds (about 45 words)

**Narration**

> <bookmark mark='minimax'/>In the last video, minimax searched every possible game. It never loses.
>
> <bookmark mark='cost'/>But a person wrote every line of its logic. And in pure Python, one search can take seconds.
>
> <bookmark mark='question'/>Today, the program finds its own moves. Who decides the next move? The program learns to decide.

**Visuals**

- Left half: a small game tree (a root node, three child nodes, nine grandchild nodes, lines in `MUTED_COLOR`). Label under it: `MinimaxStrategy`, `TEXT_COLOR`.
- Right half: a clock icon (a circle with two hands, `MUTED_COLOR`) and the text `seconds for each move`, `MUTED_COLOR`. Under it, a pencil icon or the text `hand-written logic`, `MUTED_COLOR`.
- Center, at the end: the series question `Who decides the next move?`, `TEXT_COLOR`, font size 48.

**Animation steps**

1. `minimax`: Create the game tree from the root down (`Create`, 2 seconds). Write the label `MinimaxStrategy`.
2. `cost`: Fade in the clock and the text `seconds for each move`. Then fade in `hand-written logic`.
3. `question`: Fade out all objects. Write `Who decides the next move?` in the center.

**Accuracy notes**

- `MinimaxStrategy` is too slow to use as a training opponent in pure Python (seconds for each move, from `AGENTS.md`). Do not give a more exact time.

---

### E5S2: Reinforcement learning in one picture

- **Manim class:** `E5S2RLPicture`
- **Target duration:** 40 seconds (about 90 words)

**Narration**

> <bookmark mark='title'/>The method has the name reinforcement learning. It is learning by trial and error.
>
> <bookmark mark='state'/>Three words do all the work. A state is one board position.
>
> <bookmark mark='policy'/>A policy is the rule that gives each free cell a probability. The learner picks its move from these probabilities.
>
> <bookmark mark='reward'/>A reward tells how the game ended for the learner. A win gives plus one. A draw gives zero. A loss gives minus one.
>
> <bookmark mark='loop'/>The learner plays, gets a reward, and changes its policy. Moves that win become more probable. Moves that lose become less probable.

**Visuals**

- Title at top: `Reinforcement learning`.
- A loop of three boxes, placed on a circle of radius 2.2 around (0, −0.4):
  - Top box: `state` with a small board (cell side 0.4) with X on 0 and O on 4. Stroke `TEXT_COLOR`.
  - Lower right box: `policy` with a small heat map (cell side 0.4, any four free cells with visible green opacity). Stroke `TEXT_COLOR`.
  - Lower left box: `reward` with three numbers in a column: `+1` (`POSITIVE_COLOR`), `0` (`NEUTRAL_COLOR`), `−1` (`NEGATIVE_COLOR`).
- Curved arrows between the boxes, clockwise: state → policy → reward → state. Arrow color `MUTED_COLOR`.
- Text in the loop center at the `loop` bookmark: `trial and error`, `MUTED_COLOR`.

**Animation steps**

1. `title`: Write the title.
2. `state`: Fade in the state box.
3. `policy`: Fade in the policy box and the arrow from state to policy.
4. `reward`: Fade in the reward box and the arrow from policy to reward. Write `+1`, then `0`, then `−1`.
5. `loop`: Draw the arrow from reward to state. Write `trial and error` in the center. Rotate a small dot along the three arrows one time (3 seconds).

**Accuracy notes**

- The reward values are exactly +1, 0, −1 (`_reward` in `trainer.py`).
- A policy gives probabilities to free cells only.

---

### E5S3: A learner is a strategy that learns

- **Manim class:** `E5S3LearnerProtocol`
- **Target duration:** 40 seconds (about 95 words)

**Narration**

> <bookmark mark='strategy'/>In video 3, a strategy had one method: choose position. It looks at the game and returns a position.
>
> <bookmark mark='protocol'/>A reinforcement learner is a protocol with two methods. The first method is the same choose position. So a learner can sit in any seat that a strategy can use.
>
> <bookmark mark='learn'/>The second method is learn. After a game, the learner gets one experience for each of its moves.
>
> <bookmark mark='experience'/>An experience is a frozen record with four fields. Read it as a sentence. On this board, this player played this action, and the game gave this reward.

**Visuals**

- Left half: a card `Strategy` with one line `choose_position(game) → Position`, stroke `TEXT_COLOR`, at (−3.5, 1.5). At the `protocol` bookmark, a larger card `ReinforcementLearner` at (−3.5, −0.5) with two lines: `choose_position(game) → Position` and `learn(experience)`. Draw the `learn` line in `POSITIVE_COLOR` to show it is new.
- Right half: code panel with Snippet A. At the `experience` bookmark, replace it with Snippet B.
- At the `experience` bookmark, under the code panel at (3.5, −2.6): the sentence `board · player · action · reward`, `MUTED_COLOR`.

**Animation steps**

1. `strategy`: Fade in the `Strategy` card.
2. `protocol`: Fade in the code panel with Snippet A. Fade in the `ReinforcementLearner` card. Draw a line from the `choose_position` line of the `Strategy` card to the same line of the `ReinforcementLearner` card, `MUTED_COLOR`.
3. `learn`: Indicate the `learn` line in the card and the `learn` line in the code panel (`Indicate`, color `POSITIVE_COLOR`).
4. `experience`: Transform the code panel to Snippet B. Write the sentence under it. Highlight the four field lines one at a time (0.5 seconds each) with a surrounding rectangle in `MUTED_COLOR`.

**Accuracy notes**

- `ReinforcementLearner` is a structural `typing.Protocol`. No class inherits from it.
- `Experience` is `@dataclass(frozen=True, slots=True)`. It does not validate its fields.
- `PolicyLearner.choose_position` has an extra parameter `explore: bool = True`. The protocol does not show it. Scene `E5S7` explains it.

---

### E5S4: Reading the board as features

- **Manim class:** `E5S4Features`
- **Target duration:** 50 seconds (about 110 words)

**Narration**

> <bookmark mark='board'/>The learner cannot see the board. It reads the board as a list of numbers. We call each number a feature.
>
> <bookmark mark='mover'/>Here O is to move. The learner reads each cell from the side of the player to move.
>
> <bookmark mark='walk'/>My own mark gives plus one. The opponent's mark gives minus one. An empty cell gives zero.
>
> <bookmark mark='bias'/>At the end, the code adds one more feature. It is always one. We call it the bias.
>
> <bookmark mark='relative'/>So there are ten features. If X were to move, all the signs would change. The learner never asks, am I X or O? It only asks, mine or theirs? Thus one learner can play either seat.

**Visuals**

- Left half: Board B1 at (−3.5, 1.0): X on cells 0 and 1 (`X_COLOR`), O on cell 2 (`O_COLOR`). Show the cell indices 0 to 8 in small grey text.
- Text above the board at (−3.5, 3.0): `O to move`, `O_COLOR`.
- Bottom, full width at y = −2.4: the feature vector, 10 squares, center (0, −2.4). Values in order: `−1, −1, +1, 0, 0, 0, 0, 0, 0, 1`.
- Right half: code panel with Snippet C, at (3.5, 1.0), scaled to fit above the feature vector.
- At the `relative` bookmark: a second feature vector under the first at y = −3.3, with the label `if X were to move` on its left in `X_COLOR`, font size 20. Values: `+1, +1, −1, 0, 0, 0, 0, 0, 0, 1`.

**Animation steps**

1. `board`: Create the board, the marks, and the cell indices. Fade in the code panel.
2. `mover`: Write `O to move`.
3. `walk`: For each cell 0 to 8, in order: indicate the cell on the board (0.3 seconds), then move a copy of the cell's value from the cell to its square in the feature vector (0.3 seconds). Highlight the matching `if` / `elif` / `else` line in the code panel while the value moves.
4. `bias`: Create the tenth square with `1`. Highlight the line `values.append(1.0)` after the loop.
5. `relative`: Fade in the second vector and its label. Indicate squares 0, 1, 2 in both vectors.

**Accuracy notes**

- Features are in cell index order 0 to 8, then the bias.
- The values are floats (`1.0`, `-1.0`, `0.0`). The screen can show `+1`, `−1`, `0`.
- Board B1 is a real board from the demo game `FirstAvailableStrategy` (X) vs `PolicyLearner` (O).

---

### E5S5: The weight table and the logits

- **Manim class:** `E5S5WeightsLogits`
- **Target duration:** 55 seconds (about 130 words)

**Narration**

> <bookmark mark='table'/>The policy keeps a table of weights. There is one row for each move, so nine rows. There is one column for each feature, so ten columns. That is ninety numbers.
>
> <bookmark mark='zero'/>A new learner starts with all weights at zero. It has no preference.
>
> <bookmark mark='row'/>These weights come from the trained O learner. To score cell 7, take row 7.
>
> <bookmark mark='multiply'/>Multiply each weight by the matching feature. Then add all the products. Empty cells give zero, so only four terms stay.
>
> <bookmark mark='logit'/>The sum is 3.66. We call this raw score a logit.
>
> <bookmark mark='all'/>The learner does this for each free cell. Cell 8 gets 2.12. Cell 6 gets 0.55. Cells 3, 4, and 5 get low negative logits.
>
> <bookmark mark='linear'/>Each logit is one weighted sum. We call this a linear model.

**Visuals**

- Left half: the weight table as a 9 × 10 grid of small rectangles (width 0.55, height 0.4), center (−3.3, 0). Row labels `0` to `8` on the left (`MUTED_COLOR`), column labels `0` to `8` and `b` on the top (`MUTED_COLOR`). Label under the grid: `9 moves × 10 features = 90 weights`, `TEXT_COLOR`.
- At the `zero` bookmark, each rectangle shows `0` in `NEUTRAL_COLOR`, font size 14.
- At the `row` bookmark, fill only rows 6, 7, and 8 with the trained numbers from section 5.3 (three decimals, font size 14, colored by sign). Other rows keep grey `0` placeholders but change to the text `…` in `MUTED_COLOR`. Put a caption over the grid: `trained O learner`, `MUTED_COLOR`.
- Right half, top at (3.5, 2.6): small Board B1 (cell side 0.6) with its feature vector under it (square side 0.4).
- Right half, center at (3.5, 0.2): the sum for cell 7, as `Text` in four lines:
  - `(−1.022)·(−1) = +1.022`
  - `(−0.616)·(−1) = +0.616`
  - `(+1.004)·(+1) = +1.004`
  - `(+1.022)·(1) = +1.022` with `b` label on the right
- Under the sum: a line, then `logit[7] = 3.66`, `POSITIVE_COLOR`.
- At the `all` bookmark: under the small board, a list of logits: `cell 3: −4.93`, `cell 4: −4.91`, `cell 5: −2.65`, `cell 6: +0.55`, `cell 7: +3.66`, `cell 8: +2.12`. Positive in `POSITIVE_COLOR`, negative in `NEGATIVE_COLOR`. Also write each logit in its free cell of the small board, font size 16.
- At the `linear` bookmark: the formula `logit[a] = Σ weight[a][i] · feature[i]` at the bottom center (0, −3.3), `TEXT_COLOR`.

**Animation steps**

1. `table`: Create the grid, row labels, column labels, and the label under the grid.
2. `zero`: Write `0` in all 90 rectangles (`LaggedStart`, 1.5 seconds total).
3. `row`: Transform rows 6, 7, 8 into the trained numbers. Transform the other rows into `…`. Write the caption. Fade in the small board and its feature vector on the right. Surround row 7 with a rectangle in `TEXT_COLOR`.
4. `multiply`: For columns 0, 1, 2, and `b` of row 7: move a copy of the weight and a copy of the feature to the sum area, then write that sum line (0.8 seconds each). Dim columns 3 to 8 of row 7 to 30% opacity.
5. `logit`: Draw the line and write `logit[7] = 3.66`. Write `3.66` in cell 7 of the small board.
6. `all`: Fade out the four sum lines. Write the logit list. Write each logit in its cell of the small board.
7. `linear`: Write the formula at the bottom.

**Accuracy notes**

- Row 7 column 7 is exactly 0.000. The weight of a move for its own cell never changes: when the cell is free its feature is 0, and when it is occupied the row does not update.
- The exact logit of cell 7 is 3.6633. The four rounded terms add to 3.664. Show `3.66` only.
- Occupied cells (0, 1, 2) get no logit. Do not write a logit in them.
- Do not call the weight table "a table of move scores for each board". It is a table of weights.

---

### E5S6: Softmax gives probabilities

- **Manim class:** `E5S6Softmax`
- **Target duration:** 45 seconds (about 95 words)

**Narration**

> <bookmark mark='problem'/>Logits are not probabilities. They can be negative, and they do not add up to one.
>
> <bookmark mark='softmax'/>Softmax fixes this. Raise e to the power of each logit. Then divide each result by the total.
>
> <bookmark mark='free'/>The code does this for the free cells only. An occupied cell never gets a probability.
>
> <bookmark mark='heat'/>Now the logits become a heat map. Cell 7 gets 0.79. Cell 8 gets 0.17. Cell 6 gets 0.04. The other cells get almost zero.
>
> <bookmark mark='gap'/>A bigger logit always gives a bigger probability. A logit gap of two gives a split of about 88 to 12.

**Visuals**

- Left half: Board B1 at (−3.5, 0.3), with the logits written in the free cells (from `E5S5`, font size 20).
- Right half: code panel with Snippet E at (3.5, 1.2).
- Under the code panel at (3.5, −2.2): the formula `probability[a] = e^logit[a] / Σ e^logit[k]  (k: free cells)`, `TEXT_COLOR`, font size 26.
- At the `heat` bookmark: the heat map on Board B1. Values: cell 3 `0.00`, cell 4 `0.00`, cell 5 `0.00`, cell 6 `0.04`, cell 7 `0.79`, cell 8 `0.17`. Under the board: `sum = 1.00`, `MUTED_COLOR`.
- At the `gap` bookmark: bottom center (0, −3.3), two bars side by side: a bar of height 0.88 × 2 units labeled `0.88` and a bar of height 0.12 × 2 units labeled `0.12`, both `POSITIVE_COLOR`. Label under them: `logit gap = 2`, `MUTED_COLOR`.

**Animation steps**

1. `problem`: Show the board with logits. Indicate the negative logits (`−4.93`, `−4.91`, `−2.65`) in `NEGATIVE_COLOR`.
2. `softmax`: Fade in the code panel. Highlight the lines from `peak = max(logits)` to `return`. Write the formula.
3. `free`: Highlight the `free = ...` line. Flash cells 0, 1, 2 with a red cross (`ERROR_COLOR`, 0.5 seconds), then remove the crosses.
4. `heat`: Transform each logit in its cell into the probability, and fill each cell with the heat map color. Write `sum = 1.00`.
5. `gap`: Fade out the formula. Grow the two bars from the bottom. Write their labels.

**Accuracy notes**

- The code subtracts `peak` (the largest logit) before `math.exp`. This gives the same probabilities. The narration does not need to say this. If the panel highlights that line, do not say that it changes the result.
- Probabilities come from the trained O learner on Board B1 (section 5.3). Cell 7 is 0.7928, cell 8 is 0.1702, cell 6 is 0.0353.
- e² / (1 + e²) = 0.8808.

---

### E5S7: Explore or play greedy

- **Manim class:** `E5S7ExploreGreedy`
- **Target duration:** 45 seconds (about 105 words)

**Narration**

> <bookmark mark='two'/>The learner can use these probabilities in two ways.
>
> <bookmark mark='explore'/>With explore set to true, it samples. It rolls a random number between zero and one. Then it walks the free cells and adds their probabilities.
>
> <bookmark mark='roll'/>For a roll of 0.9, the running total passes 0.9 at cell 8. So the learner plays cell 8, the second choice.
>
> <bookmark mark='why'/>Sometimes it tries a move that is not its favorite. That is how it finds out that it was wrong. Training uses this mode.
>
> <bookmark mark='greedy'/>With explore set to false, it is greedy. It always plays the highest probability, cell 7. The demo games use this mode.

**Visuals**

- Left half: Board B1 with the heat map from `E5S6`, at (−3.5, 1.0).
- Left half, under the board at (−3.5, −2.3): a horizontal number line from 0 to 1, width 5 units. Colored segments in cell order: cells 3, 4, 5 (too thin to see; draw a 0.02-unit sliver with the label `3 4 5` above, font size 14), cell 6 (width 0.0353 of the line), cell 7 (width 0.7928), cell 8 (width 0.1702). Segment fill `POSITIVE_COLOR` with opacity equal to the probability, and white borders between segments. Label each wide segment with its cell number.
- Right half: code panel with Snippet F at (3.5, 0.5).

**Animation steps**

1. `two`: Show the board, the heat map, and the code panel.
2. `explore`: Highlight the lines from `roll = self._rng.random()` to `return Position.from_index(action)`. Create the number line and its segments from left to right.
3. `roll`: Put a triangle marker at 0.90 on the number line, `TEXT_COLOR`. Write `roll = 0.90` over it. Indicate the cell 8 segment, then indicate cell 8 on the board. Place a small O (`O_COLOR`, 50% opacity) in cell 8.
4. `why`: Fade out the small O.
5. `greedy`: Highlight the lines `if not explore:` to `return Position.from_index(free[best])`. Indicate cell 7 on the board. Place an O in cell 7 (`O_COLOR`, full opacity).

**Accuracy notes**

- The default is `explore: bool = True`. `Trainer` calls `learner.choose_position(game)`, so training explores.
- `main.py` calls `run_match(..., explore=False)` for the demo games, so the demo games are greedy.
- The cumulative values are 0.0001, 0.0003, 0.0017, 0.0370, 0.8298, 1.0000. A roll of 0.90 picks cell 8.

---

### E5S8: The training loop

- **Manim class:** `E5S8TrainingLoop`
- **Target duration:** 60 seconds (about 140 words)

**Narration**

> <bookmark mark='trainer'/>The trainer plays the training games. One full game is one episode.
>
> <bookmark mark='play'/>In each episode, the learner plays one seat. A fixed strategy plays the other seat. Here the opponent is the naive first available strategy.
>
> <bookmark mark='record'/>When it is the learner's turn, the learner picks a move. The trainer records the board and the move.
>
> <bookmark mark='end'/>The game continues to the end. No one teaches the learner during the game.
>
> <bookmark mark='reward'/>Then the trainer calculates one reward. Plus one for a win, zero for a draw, minus one for a loss.
>
> <bookmark mark='same'/>Now look carefully. Every recorded move gets the same reward. A good move and a bad move in a won game both get plus one. This method waits for the final result. Its name is Monte Carlo.
>
> <bookmark mark='count'/>At the end, the trainer counts wins, draws, and losses in a training summary.

**Visuals**

- Title at top: `Trainer.train`.
- Left half: a board at (−3.5, 1.2), cell side 0.9 (smaller than default).
- Left half, under the board at (−3.5, −1.6): a column named `moves` (header `TEXT_COLOR`). Each entry is a small board image (cell side 0.25) with an arrow to a cell number.
- Right half: code panel. Snippet G1 from `trainer` to `end`. Snippet G2 and Snippet H from `reward` to the end (G2 on top at (3.5, 1.3), H under it at (3.5, −2.0)).
- Use real game 1 moves from section 5.4 (X is `FirstAvailableStrategy`, O is the learner): X 0, O 2, X 1, O 7, X 3, O 8, X 4, O 6.
- At the `reward` bookmark: text `reward = +1` in `POSITIVE_COLOR` under the board.
- At the `same` bookmark: a green tag `+1` (`POSITIVE_COLOR`) next to each of the four entries in the `moves` column.
- At the `count` bookmark: a card `TrainingSummary` at (−3.5, −3.3) with `wins`, `draws`, `losses`.

**Animation steps**

1. `trainer`: Write the title. Fade in the code panel with Snippet G1. Highlight `for episode in range(episodes):`.
2. `play`: Create the empty board. Write `learner: O` in `O_COLOR` and `opponent: FirstAvailableStrategy` in `X_COLOR` above the board, font size 22.
3. `record`: Play the moves X 0, O 2, X 1, O 7 at 0.6 seconds each. After each O move, add an entry to the `moves` column (the board before the move, and the cell). Highlight `moves.append((game.board, action))` at each O move.
4. `end`: Play X 3, O 8, X 4, O 6 at 0.6 seconds each. Add entries for O 8 and O 6. Draw a line through cells 6, 7, 8 in `O_COLOR`. Write `O_WON`.
5. `reward`: Transform the code panel to Snippet G2 and Snippet H. Highlight `return 1.0 if player == winner else -1.0`. Write `reward = +1`.
6. `same`: Move a copy of `+1` to each of the four `moves` entries (`LaggedStart`). Highlight the line `learner.learn(Experience(board, seat, action, _reward(seat, game.status)))`.
7. `count`: Fade in the `TrainingSummary` card. Highlight the last line of Snippet G2.

**Accuracy notes**

- The learner gets `learn` calls only after the game ends, one call for each learner move, in the order of the moves.
- All learner moves of one game get the same reward.
- The `Trainer` uses the `Game` aggregate directly (`game.place_mark(action).game`). No engine, no event bus.
- The real game 1 in `main.py` was played greedy after training. Here the scene uses its moves only as an example of one episode. Do not say that this exact game happened in training.

---

### E5S9: The update, with real numbers

- **Manim class:** `E5S9Update`
- **Target duration:** 80 seconds (about 185 words)

**Narration**

> <bookmark mark='setup'/>Now the most important part: what learn does with one experience. We use a new learner, so all weights are zero.
>
> <bookmark mark='board'/>X played cell 0. O is to move. All eight free cells have the same probability, 0.125. The learner played cell 4, and later it won. The reward is plus one.
>
> <bookmark mark='advantage'/>First, the advantage. It is the reward minus the value of this board. This board is new, so its value is zero. The advantage is one.
>
> <bookmark mark='indicator'/>Next, the learner walks each free cell. The indicator is one for the played cell. It is zero for the other cells.
>
> <bookmark mark='scale'/>For cell 4, the scale is 0.1 times 1 times, 1 minus 0.125. That gives 0.0875. For each other cell, the scale is 0.1 times 1 times, 0 minus 0.125. That gives minus 0.0125.
>
> <bookmark mark='rows'/>Each row changes by its scale times the features. Row 4 moves toward this board. The other rows move away.
>
> <bookmark mark='after'/>Now the probability of cell 4 is 0.15. Each other cell drops to 0.12. After a loss, the signs flip. This rule has the name policy gradient. This form is the REINFORCE rule.

**Visuals**

- Left half: Board U at (−3.5, 1.4): X on cell 0 (`X_COLOR`). Heat map on cells 1 to 8, each `0.13` at opacity 0.125. Text above the board: `O to move`, `O_COLOR`.
- Left half, under the board at (−3.5, −1.3): the feature vector `−1, 0, 0, 0, 0, 0, 0, 0, 0, 1`.
- Right half, top: code panel with Snippet I2 at (3.5, 1.6), scaled to height 3.2.
- Right half, bottom: a calculation area at (3.5, −1.6), `Text`, font size 24:
  - Line 1 (`advantage` bookmark): `advantage = reward − V = 1.0 − 0.0 = 1.0`
  - Line 2 (`scale` bookmark): `cell 4: 0.1 · 1.0 · (1 − 0.125) = +0.0875` in `POSITIVE_COLOR`
  - Line 3 (`scale` bookmark): `other cells: 0.1 · 1.0 · (0 − 0.125) = −0.0125` in `NEGATIVE_COLOR`
- At the `rows` bookmark, left bottom at (−3.5, −2.8): two rows of 10 small squares:
  - `row 4:  −0.0875  0 … 0  +0.0875`
  - `row 1:  +0.0125  0 … 0  −0.0125`, with the label `(same for rows 2, 3, 5, 6, 7, 8)`, `MUTED_COLOR`, font size 18.
  - `row 0: no change (cell 0 is not free)`, `MUTED_COLOR`, font size 18.
- At the `after` bookmark: the heat map changes to cell 4 `0.15` (opacity 0.1486) and each other free cell `0.12` (opacity 0.1216). A small green up arrow next to cell 4. A small red down arrow next to the text `others`.

**Animation steps**

1. `setup`: Write `new learner: all 90 weights = 0` at the top center, `MUTED_COLOR`. Fade in the code panel with Snippet I2.
2. `board`: Create Board U, the X mark, and the heat map with `0.13` in each free cell. Fade in the feature vector. Place a dashed O outline in cell 4 (`O_COLOR`). Write `reward = +1` in `POSITIVE_COLOR` next to the board.
3. `advantage`: Write calculation line 1.
4. `indicator`: Highlight `indicator = 1.0 if action == experience.action.index else 0.0`. Write `1` in small text over cell 4 and `0` over each other free cell (`MUTED_COLOR`, font size 16), then fade them out.
5. `scale`: Highlight the `scale = ...` line. Write calculation line 2, then line 3.
6. `rows`: Highlight `weight[feature_index] += scale * features[feature_index]`. Create the row displays. Indicate the first and last square of row 4 in `POSITIVE_COLOR`.
7. `after`: Transform the heat map numbers and opacities to the new values. Grow the up arrow and the down arrow.

**Accuracy notes**

- The update changes the rows of all free cells, not only the played cell.
- The update changes each weight by `scale · feature`. Features that are 0 give no change. So only column 0 (the X on cell 0) and column 9 (the bias) change here.
- The update uses the probabilities from the current weights at learn time, not at play time.
- After the update, the logit of cell 4 is 0.175 and each other logit is −0.025. The probability of cell 4 is 0.1486. Each other probability is 0.1216.
- In the code, this update is called after the value table update (Snippet I1). Scene `E5S10` shows that part.
- Say "policy gradient" and "REINFORCE rule". Do not call the model "feedforward".

---

### E5S10: Why the value baseline matters

- **Manim class:** `E5S10Baseline`
- **Target duration:** 80 seconds (about 200 words)

**Narration**

> <bookmark mark='problem'/>Go back to the reward. Every move in a won game gets plus one. But not every move in a won game was good. A raw reward is a noisy teacher.
>
> <bookmark mark='value'/>So the learner keeps a second memory, the value table. It stores one value for each board that it saw. The value estimates the reward from that board.
>
> <bookmark mark='advantage'/>The update uses the advantage: the reward minus the value. The learner reacts to the surprise, not to the raw score.
>
> <bookmark mark='sequence'/>After each result, the value moves toward the reward. The new value is 0.9 times the old value, plus 0.1 times the reward. So repeated wins from one board teach less each time. The advantage falls from 1 to 0.9, 0.81, and 0.73. A surprise loss teaches a lot.
>
> <bookmark mark='name'/>The exact name is REINFORCE with a learned baseline. The code calls it actor-critic, a simple form of it. The value moves toward the final reward only. It never uses the value of the next board. So there is no bootstrapping.
>
> <bookmark mark='test'/>Does the baseline help? Against an opponent that builds threats, the learner with the baseline lost 3 of its last 500 games. Without the baseline, it lost 58.

**Visuals**

- Title at top: `The value baseline`.
- Left half, top at (−3.5, 1.9): a small board with any learner move, and the text `+1` in `POSITIVE_COLOR` on each of four move tags. One tag has a small grey question mark next to it (`MUTED_COLOR`), to show a move that was not good.
- Left half, center at (−3.5, 0.3): a two-column table named `value table` (header `TEXT_COLOR`): three rows, each a small board image (cell side 0.25) and a number: `0.10`, `1.00`, `−0.30`. Colors by sign. Put `…` as a fourth row.
- Right half, top: code panel with Snippet I1 at (3.5, 2.2).
- Right half, center at (3.5, 0.3): `advantage = reward − V(board)`, `TEXT_COLOR`, font size 30. Under it: `V ← 0.9 · V + 0.1 · reward`, `TEXT_COLOR`, font size 30.
- At the `sequence` bookmark, left bottom at (−3.5, −2.3): the table from section 5.3 "Value and advantage after repeated wins", rows 1 to 4 only, columns `win`, `V before`, `advantage`. Advantage numbers in `POSITIVE_COLOR`. Under the table: `after 5 wins, a loss: advantage = −1 − 0.41 = −1.41` in `NEGATIVE_COLOR`, font size 22.
- At the `name` bookmark, right bottom at (3.5, −1.7): a box with stroke `RULE_COLOR` and three lines:
  - `REINFORCE with a learned baseline` (font size 28, `TEXT_COLOR`)
  - `code name: actor-critic (simple form)` (font size 22, `MUTED_COLOR`)
  - `no bootstrapping: V moves toward the final reward` (font size 22, `MUTED_COLOR`)
- At the `test` bookmark: fade out the left bottom table and the right bottom box. At (0, −2.5), two horizontal bars, width in proportion to losses out of 500 (full width 6 units = 60 losses):
  - `with baseline: lost 3 of last 500`, bar width 0.3, `NEGATIVE_COLOR`.
  - `without baseline: lost 58 of last 500`, bar width 5.8, `NEGATIVE_COLOR`.
  - Label over the bars: `opponent: ThreatBuilderStrategy, seat X`, `MUTED_COLOR`, font size 20.

**Animation steps**

1. `problem`: Write the title. Fade in the small board and the four `+1` tags. Fade in the question mark.
2. `value`: Fade in the code panel with Snippet I1. Create the value table. Highlight the line `value = self._values.get(experience.board, 0.0)`.
3. `advantage`: Highlight `advantage = experience.reward - value`. Write `advantage = reward − V(board)`.
4. `sequence`: Highlight the `self._values[experience.board] = ...` line. Write `V ← 0.9 · V + 0.1 · reward`. Write the table rows one at a time (0.6 seconds each). Write the loss line.
5. `name`: Create the box and write its three lines.
6. `test`: Fade out the table and the box. Grow the two bars. Write their labels.

**Accuracy notes**

- The order in the code: first read `V`, then compute `advantage` with the old `V`, then update `V`, then update the weights.
- The value table is a dictionary keyed by the full `Board`. A new board has value 0.0.
- The value table rows in the visuals (`0.10`, `1.00`, `−0.30`) are examples of the format only. The narration does not read them.
- REINFORCE with a learned baseline must be said before "actor-critic".
- The claim "no bootstrapping" is exact: `learn` uses only `experience.reward` and the stored value of the same board.
- The test numbers come from snippet S5 (sections 5.4 and 5.6). `value_rate=1.0` keeps every value at 0.0, so the advantage equals the raw reward. This is the learner without a baseline.
- Do not say that the policy "oscillates" or "unlearns" as a measured fact. The test did not show this. `AGENTS.md` and the article state it.
- Do not say that the naive opponent shows the difference. Against the naive opponent, both versions win almost all games.
- Do not name `ThreatBuilderStrategy` in the narration. Video 6 introduces it. The label on screen is sufficient.

---

### E5S11: Training results

- **Manim class:** `E5S11Results`
- **Target duration:** 35 seconds (about 70 words)

**Narration**

> <bookmark mark='main'/>The demo trains two learners, one for each seat. Each learner plays six thousand episodes against the naive strategy.
>
> <bookmark mark='x'/>The X learner won 5968 games. It drew 7 and lost 25.
>
> <bookmark mark='o'/>The O learner won 5960 games. It drew 11 and lost 29.
>
> <bookmark mark='meaning'/>Both learners started with all weights at zero. No one wrote a rule about tic-tac-toe. After a short time, they almost never lose to this opponent.

**Visuals**

- Top half: code panel with Snippet J, centered at (0, 2.0), full width, scaled to fit.
- Bottom left at (−3.5, −1.8): a stacked horizontal bar for X, width 5 units: won 5968 (`POSITIVE_COLOR`), drew 7 (`NEUTRAL_COLOR`), lost 25 (`NEGATIVE_COLOR`). Label above: `X learner (seat X)`, `X_COLOR`. Numbers under the bar: `won 5968 · drew 7 · lost 25`.
- Bottom right at (3.5, −1.8): the same bar for O: won 5960, drew 11, lost 29. Label above: `O learner (seat O)`, `O_COLOR`. Numbers: `won 5960 · drew 11 · lost 29`.
- The draw and loss parts are very thin. Give each of them a minimum width of 0.05 units so they are visible. Add a note `(draw and loss widths enlarged)` at the bottom, `MUTED_COLOR`, font size 16.

**Animation steps**

1. `main`: Fade in the code panel.
2. `x`: Grow the X bar from left to right. Write its numbers.
3. `o`: Grow the O bar. Write its numbers.
4. `meaning`: Write `all weights started at 0.0` at (0, −3.2), `MUTED_COLOR`.

**Accuracy notes**

- The numbers are the real output of `uv run main.py`: `tabular X vs naive: won 5968, drew 7, lost 25` and `tabular O vs naive: won 5960, drew 11, lost 29`.
- The counts include the early episodes, when the learner still played almost at random.
- The program output uses the word "tabular". The narration does not use that word.

---

### E5S12: The demo games after training

- **Manim class:** `E5S12DemoGames`
- **Target duration:** 50 seconds (about 120 words)

**Narration**

> <bookmark mark='game1'/>Now the demo plays greedy games. First, the naive strategy plays X. The trained learner plays O.
>
> <bookmark mark='threat'/>Look at this board. X has cells 0 and 3. X can win on cell 6. O must block.
>
> <bookmark mark='miss'/>But the learner gives cell 6 only 0.15. It plays cell 8. The naive player takes cell 4, the first free cell. Then O wins on cell 6.
>
> <bookmark mark='why'/>The learner did not block, and it did not need to. The naive player never takes cell 6 here.
>
> <bookmark mark='game2'/>Second, the trained X learner plays the trained O learner. O has cells 6 and 8. O can win on cell 7.
>
> <bookmark mark='miss2'/>X gives cell 7 only 0.24 and plays cell 5. O wins on cell 7.

**Visuals**

- Left half: Board for game 1 at (−3.5, 0.3). Title above: `FirstAvailableStrategy (X) vs PolicyLearner (O)`, font size 22.
- Right half at `threat`: Board B2 heat map, center (3.5, 0.3). Values: cell 4 `0.00`, cell 5 `0.00`, cell 6 `0.15`, cell 8 `0.85`. A red outline (`ERROR_COLOR`) around cell 6 with the label `X wins here`.
- At `game2`: replace both boards. Left: Board for game 2, title `PolicyLearner (X) vs PolicyLearner (O)`. Right: Board B3 heat map. Values: cell 0 `0.23`, cell 1 `0.06`, cell 3 `0.19`, cell 5 `0.29`, cell 7 `0.24`. A red outline around cell 7 with the label `O wins here`.

**Animation steps**

1. `game1`: Create the left board and title. Play X 0, O 2, X 1, O 7, X 3 at 0.5 seconds each.
2. `threat`: Draw a faint line through cells 0 and 3 toward cell 6 (`X_COLOR`, 50% opacity). Create Board B2 heat map on the right. Draw the red outline around cell 6 on both boards.
3. `miss`: Indicate `0.85` on cell 8. Play O 8, then X 4, then O 6 on the left board. Draw the winning line 6-7-8 in `O_COLOR`. Write `O_WON`.
4. `why`: Write `the naive X plays the lowest free cell` under the left board, `MUTED_COLOR`, font size 22.
5. `game2`: Fade out all objects. Create the new title and the left board. Play X 2, O 6, X 4, O 8 at 0.5 seconds each. Create Board B3 heat map on the right. Draw the red outline around cell 7 on both boards.
6. `miss2`: Indicate `0.29` on cell 5. Play X 5, then O 7 on the left board. Draw the winning line 6-7-8 in `O_COLOR`. Write `O_WON`.

**Accuracy notes**

- Game 1 moves: X 0, O 2, X 1, O 7, X 3, O 8, X 4, O 6. Result `O_WON`.
- Game 2 moves: X 2, O 6, X 4, O 8, X 5, O 7. Result `O_WON`.
- In game 2, X never threatened a win on O's turns, so O never needed to block. Do not claim that O made a mistake.
- Board B3 never occurred in the X learner's training (it is not in its value table). The weights still give probabilities for it.

---

### E5S13: Limit one: the teacher

- **Manim class:** `E5S13Overfitting`
- **Target duration:** 45 seconds (about 100 words)

**Narration**

> <bookmark mark='teacher'/>Here is the first limit. The naive opponent never builds a threat. So the learner never needs to block a two in a row.
>
> <bookmark mark='test'/>We tested this. We took every legal board where the opponent has one open two in a row.
>
> <bookmark mark='result'/>The trained O learner blocked in 29 percent of these boards. A random move blocks in 30 percent. The X learner blocked in 37 percent, and random gives 33.
>
> <bookmark mark='lesson'/>So the learner is almost no better than random at blocking. It learned to beat one opponent only. We call this overfitting. A learner can only learn what its opponent teaches.

**Visuals**

- Left half at (−3.5, 0.5): a board where the naive X always fills cells in order 0, 1, 2, 3, … Show X marks appearing in cells 0, 1, 3 with small index numbers. Label: `FirstAvailableStrategy: lowest free cell`, `MUTED_COLOR`.
- Right half at (3.5, 0.3): a grouped bar chart, y axis 0% to 50%.
  - Group `O learner (580 boards)`: bar `learner 29%` (`O_COLOR`), bar `random 30%` (`NEUTRAL_COLOR`).
  - Group `X learner (396 boards)`: bar `learner 37%` (`X_COLOR`), bar `random 33%` (`NEUTRAL_COLOR`).
  - Title over the chart: `greedy move blocks the threat`, `TEXT_COLOR`, font size 26.
- Bottom center at (0, −3.2): `overfitting`, `ERROR_COLOR`, font size 36.

**Animation steps**

1. `teacher`: Create the left board. Place X marks in cells 0, 1, 3 at 0.5 seconds each, with a small arrow that shows the order.
2. `test`: Create the chart axes and the title.
3. `result`: Grow the O learner bar, then the random bar. Then grow the X learner bar and its random bar.
4. `lesson`: Write `overfitting`.

**Accuracy notes**

- The test is S4 in section 5.6. It uses the trained learners from `main.py` settings, greedy moves, and all legal boards with exactly one opponent threat and no win for the learner on this move.
- `AGENTS.md` states that a learner trained against the naive opponent never learns to block a two-in-a-row. The test agrees: the block rate is at the random level.
- Random rate means the mean of 1 / (number of free cells) over the same boards.
- Do not say "never blocks". The learner sometimes blocks by chance.
- Do not say that a linear softmax policy can never learn to block. Against an opponent that builds threats, a new `PolicyLearner` in seat X loses only 3 of its last 500 games (section 5.4, baseline test). The limit in this scene is the opponent, not the model.

---

### E5S14: Limit two: a weighted sum cannot combine features

- **Manim class:** `E5S14Linear`
- **Target duration:** 65 seconds (about 150 words)

**Narration**

> <bookmark mark='second'/>The second limit is in the model. Each logit is one weighted sum. Each cell adds its own part, with no link to the other cells.
>
> <bookmark mark='example'/>Look at cell 2, with cells 0 and 1 in the same row. Suppose cells 0 and 1 are both mine. Then cell 2 wins. Cell 2 must score high.
>
> <bookmark mark='block'/>Suppose cells 0 and 1 are both theirs. Then cell 2 blocks. Cell 2 must also score high.
>
> <bookmark mark='mixed'/>But if the cells are mixed or empty, cell 2 is not special.
>
> <bookmark mark='sum'/>A weighted sum cannot do this. The features are plus one, plus one in the first case, and minus one, minus one in the second case. If the sum goes up for one case, it goes down for the other.
>
> <bookmark mark='interaction'/>Cell 2 matters only when cells 0 and 1 match. That is a feature interaction. A linear model cannot represent it.

**Visuals**

- Top center: three small boards in a row, each cell side 0.6, at x = −4.5, 0, +4.5, y = 1.6. The learner is O in all three.
  - Board 1: O on 0 and 1. Cell 2 outlined in `POSITIVE_COLOR`. Label `mine, mine → win: high`.
  - Board 2: X on 0 and 1. Cell 2 outlined in `POSITIVE_COLOR`. Label `theirs, theirs → block: high`.
  - Board 3: O on 0, X on 1. Cell 2 outlined in `NEUTRAL_COLOR`. Label `mixed → not special`.
- Bottom half at (0, −1.8): the formula `part of logit[2] = w0 · f0 + w1 · f1`, `TEXT_COLOR`, font size 30.
- Under the formula: a table with three rows:
  - `f0 = +1, f1 = +1   →  +w0 + w1`
  - `f0 = −1, f1 = −1   →  −(w0 + w1)`
  - `f0 = +1, f1 = −1   →  w0 − w1`
- At the `sum` bookmark: a two-sided arrow between the first two table rows with the text `opposite signs`, `ERROR_COLOR`.
- At the `interaction` bookmark: text `feature interaction: needs f0 and f1 together`, `RULE_COLOR`, at (0, −3.4).

**Animation steps**

1. `second`: Write the formula at the bottom.
2. `example`: Create Board 1 and its label.
3. `block`: Create Board 2 and its label.
4. `mixed`: Create Board 3 and its label.
5. `sum`: Write the three table rows one at a time. Grow the two-sided arrow and write `opposite signs`.
6. `interaction`: Write the feature interaction text.

**Accuracy notes**

- For fixed other features, the logit part from cells 0 and 1 is `w0 · f0 + w1 · f1`. For (+1, +1) it is `w0 + w1`. For (−1, −1) it is `−(w0 + w1)`. Both cannot be larger than the (0, 0) value of 0. The same is true for the difference of two logits, because that difference is also a weighted sum.
- The model can learn "my mark here is good" or "their mark there is bad". It cannot learn "this cell is good only when those two cells are both mine or both theirs".
- The value table (`self._values`) is a true lookup table with one number for each exact board. There are at most 3⁹ = 19,683 boards. This scene is about the policy weights, not the value table.

---

### E5S15: Closing and hook

- **Manim class:** `E5S15Hook`
- **Target duration:** 25 seconds (about 55 words)

**Narration**

> <bookmark mark='summary'/>Today the program learned from rewards. A table of weights scored each free cell. Policy gradient with a baseline made winning moves more probable.
>
> <bookmark mark='need'/>But a weighted sum cannot combine features. We need a model that can combine features.
>
> <bookmark mark='next'/>Next: a neural network. Who decides the next move? A network that learns patterns.

**Visuals**

- Left half at (−3.5, 0.5): a small 9 × 10 grid (the weight table), `MUTED_COLOR`, label `linear softmax policy`.
- Right half at (3.5, 0.5): a small network diagram: 9 input dots, 16 hidden dots, 9 output dots, lines in `MUTED_COLOR` at 30% opacity. Label `neural network`.
- An arrow from left to right at (0, 0.5), `TEXT_COLOR`.
- Bottom center at (0, −2.8): `Next: A Neural Network Policy`, `TEXT_COLOR`, font size 40.

**Animation steps**

1. `summary`: Fade in the small weight table and its label. Indicate the table.
2. `need`: Grow the arrow from left to right.
3. `next`: Create the network diagram (inputs, then hidden, then outputs, then lines). Write `Next: A Neural Network Policy`.

**Accuracy notes**

- The video 6 network is 9 inputs → 16 hidden units with `tanh` → 9 outputs → softmax. The diagram must show 9, 16, and 9 dots.
- Video 6 keeps the same policy-gradient rule, the same value baseline, and the same `Trainer`.

## 7. Checks

Answer each question with yes or no. Each "no" is a problem to record in `QUESTIONS.md`.

1. Does the recap (`E5S1`) take 20 seconds or less?
2. Does the narration call the `PolicyLearner` a "linear softmax policy" or "a table of weights", and never "feedforward" or "a table of move scores for each board"?
3. Does the weight table on screen have 9 rows and 10 columns, with the tenth column labeled as the bias?
4. Does Board B1 show X on cells 0 and 1, O on cell 2, and the feature vector `−1, −1, +1, 0, 0, 0, 0, 0, 0, 1`?
5. Does `E5S5` show `logit[7] = 3.66` and the logits `−4.93, −4.91, −2.65, +0.55, +3.66, +2.12` for cells 3 to 8?
6. Does the heat map in `E5S6` show `0.00, 0.00, 0.00, 0.04, 0.79, 0.17` for cells 3 to 8, and no probability on cells 0, 1, 2?
7. Does `E5S7` say that training uses `explore=True` (sampling) and the demo games use `explore=False` (greedy)?
8. Does `E5S8` show that every learner move of one game gets the same reward, and name the method Monte Carlo?
9. Does `E5S9` show `scale = +0.0875` for cell 4, `−0.0125` for the other free cells, and the new probabilities `0.15` and `0.12`?
10. Does `E5S10` name the method "REINFORCE with a learned baseline" before it says "actor-critic"?
11. Does `E5S10` show the value update `V ← 0.9 · V + 0.1 · reward` and state that there is no bootstrapping?
12. Are the training results `won 5968, drew 7, lost 25` (X) and `won 5960, drew 11, lost 29` (O)?
13. Do the two demo games in `E5S12` use the real moves from section 5.4, and does each end in `O_WON`?
14. Does `E5S13` show the block rates 29% vs 30% (O) and 37% vs 33% (X), and avoid the words "never blocks"?
15. Does `E5S14` explain that a weighted sum cannot score cell 2 high for both (+1, +1) and (−1, −1)?
16. Does the last scene name the next video's model as a neural network with 9, 16, and 9 units?
17. Is every code snippet on screen the same as section 5.1?
18. Do all colors agree with the README color table (X blue, O orange, positive green, negative red, neutral grey)?
