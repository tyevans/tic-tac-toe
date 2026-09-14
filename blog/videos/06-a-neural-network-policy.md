# Episode 6: A Neural Network Policy

## 1. Header

- **Title:** A Neural Network Policy
- **Number:** 6 of 6 (series finale)
- **Target length:** 12 minutes 25 seconds (745 seconds, 16 scenes)
- **Source files:**
  - `src/tictactoe/neural.py` (`_Feedforward`, `_features`, `_free_indices`, `_mask_occupied`, `_softmax`, `NeuralPolicyLearner`)
  - `src/tictactoe/strategies.py` (`ThreatBuilderStrategy`, `FirstAvailableStrategy`, `MinimaxStrategy`)
  - `src/tictactoe/learning.py` (`PolicyLearner`, for comparison)
  - `src/tictactoe/trainer.py` (`Trainer`)
  - `main.py` (deep training section, lines 77 to 87)
- **Source article:** `blog/articles/04-deep-learner.md`, all sections.
- **Real demo output:** the output of `uv run main.py`, saved at `/tmp/ttt_main_output.txt`. Section 5.8 copies the parts that this episode uses.

### Scene list and durations

| Scene | Class | Title | Target duration | Narration words (target) |
|-------|-------|-------|-----------------|--------------------------|
| E6S1 | `E6S1Recap` | Recap | 20 s | about 37 |
| E6S2 | `E6S2WhyANetwork` | Why a network | 45 s | about 101 |
| E6S3 | `E6S3NetworkShape` | The shape of the network | 50 s | about 105 |
| E6S4 | `E6S4ReadTheBoard` | The network reads the board | 40 s | about 96 |
| E6S5 | `E6S5ForwardPass` | The forward pass | 55 s | about 120 |
| E6S6 | `E6S6MaskAndSoftmax` | Mask and softmax | 40 s | about 85 |
| E6S7 | `E6S7PlayAMove` | Play a move | 35 s | about 72 |
| E6S8 | `E6S8AdvantageAndGradient` | Advantage and the logit gradient | 55 s | about 125 |
| E6S9 | `E6S9OutputLayer` | Change the output layer | 35 s | about 75 |
| E6S10 | `E6S10Backpropagation` | Backpropagation | 80 s | about 184 |
| E6S11 | `E6S11WhichTeacher` | Which training opponent? | 45 s | about 97 |
| E6S12 | `E6S12ThreatBuilder` | The threat builder | 50 s | about 108 |
| E6S13 | `E6S13TrainingResults` | Training results | 60 s | about 133 |
| E6S14 | `E6S14DemoGames` | The demo games | 65 s | about 145 |
| E6S15 | `E6S15FourBrains` | Four brains, one game | 40 s | about 90 |
| E6S16 | `E6S16Closing` | Closing: who decides? | 30 s | about 65 |

Total: 745 seconds, about 12 minutes 25 seconds. The narration has many numbers. Numbers take longer to say than words, so the word counts are a little lower than 140 words per minute.

## 2. Goal

After the video, the viewer can explain how a small feedforward neural network chooses a tic-tac-toe move. The viewer can follow one board through the network: the input vector, the hidden units with `tanh`, the logits, the mask, and the softmax. The viewer can explain that the network learns with the same policy-gradient rule as video 5 (REINFORCE with a per-board value baseline). The viewer can explain that backpropagation is the chain-rule method that carries that gradient back to the first layer. The viewer can say why the network trains against `ThreatBuilderStrategy`, and the viewer can read the training results without overclaiming. In this project, the network did not get better results than the linear policy, and the video says so.

## 3. Recap from the last video

Scene E6S1 (20 seconds). In video 5, the `PolicyLearner` was a linear softmax policy. Each logit was a weighted sum of 10 features. It learned by policy gradient with a per-board value baseline. But a weighted sum cannot combine features.

## 4. Terms

- **Feedforward neural network:** a model that passes numbers from one layer to the next layer, in one direction only.
- **Layer:** one step of the network. It multiplies its inputs by weights, adds the results and a bias, and can then apply a function.
- **Input:** one of the 9 numbers that describe the board, one number for each cell.
- **Hidden unit:** one of the 16 numbers between the input and the output. Each hidden unit is `tanh` of a weighted sum of the inputs plus a bias.
- **Weight:** a number that multiplies one value on its way from one layer to the next layer.
- **Bias:** a number that a layer adds to its weighted sum. `b1` has 16 biases. `b2` has 9 biases.
- **`W1`:** the weight matrix from the inputs to the hidden units. It has 16 rows of 9 weights. The code calls it `self._w1`.
- **`W2`:** the weight matrix from the hidden units to the outputs. It has 9 rows of 16 weights. The code calls it `self._w2`.
- **`tanh`:** a curved function that changes any number into a number between −1 and +1.
- **Logit:** the raw score of one cell before softmax. The network has 9 logits.
- **Mask:** the step that sets the logit of an occupied cell to −1e9 (minus one billion).
- **Softmax:** the function that changes logits into probabilities that add up to 1.
- **Forward pass:** the calculation from the input to the probabilities.
- **Advantage:** the reward minus the value of the board in the value table.
- **Logit gradient (`grad_logits`):** the vector `advantage · (one_hot(chosen) − π)`. It tells each logit to go up or down, and by how much.
- **Backpropagation:** the chain-rule method that carries the logit gradient back through `W2` and `tanh` to `W1`. It is not a separate learning rule.
- **Slope of `tanh`:** `1 − h²`, where `h` is the hidden value. It is large near 0 and small near ±1.
- **`ThreatBuilderStrategy`:** a fast strategy that plays win, then block, then fork, then build, with random tie-breaks.
- **Threat:** a line with two marks of one player and one empty cell.
- **Fork:** a move that makes two threats at the same time.

Names from earlier videos that this video uses again (do not use other names): `PolicyLearner` is a **linear softmax policy**; the learning rule is **policy gradient** (the **REINFORCE** rule) with a **per-board value baseline**. The code and `AGENTS.md` say "actor-critic". Say "REINFORCE with a baseline" first. You can say "a simple form of actor-critic" after that.

## 5. Source facts

### 5.1 Code snippets (verbatim)

All snippets are copied from the source files. Do not change them. Keep the indentation.

**S-A. `_Feedforward.__init__`** (`src/tictactoe/neural.py`, lines 13 to 19)

```python
    def __init__(self, input_size: int, hidden_size: int, output_size: int, rng: random.Random) -> None:
        input_scale = 1.0 / math.sqrt(input_size)
        hidden_scale = 1.0 / math.sqrt(hidden_size)
        self._w1 = [[rng.uniform(-input_scale, input_scale) for _ in range(input_size)] for _ in range(hidden_size)]
        self._b1 = [0.0 for _ in range(hidden_size)]
        self._w2 = [[rng.uniform(-hidden_scale, hidden_scale) for _ in range(hidden_size)] for _ in range(output_size)]
        self._b2 = [0.0 for _ in range(output_size)]
```

**S-B. `_features`** (`src/tictactoe/neural.py`)

```python
def _features(board: Board, player: Player) -> tuple[float, ...]:
    opponent = player.opponent
    values = []
    for cell in board.cells:
        if cell.player == player:
            values.append(1.0)
        elif cell.player == opponent:
            values.append(-1.0)
        else:
            values.append(0.0)
    return tuple(values)
```

**S-C. `_Feedforward.forward`** (`src/tictactoe/neural.py`, lines 21 to 30)

```python
    def forward(self, x: tuple[float, ...]) -> tuple[list[float], list[float]]:
        hidden = [
            math.tanh(sum(weight * value for weight, value in zip(row, x)) + bias)
            for row, bias in zip(self._w1, self._b1)
        ]
        logits = [
            sum(weight * value for weight, value in zip(row, hidden)) + bias
            for row, bias in zip(self._w2, self._b2)
        ]
        return hidden, logits
```

**S-D. `_mask_occupied` and `_softmax`** (`src/tictactoe/neural.py`)

```python
def _mask_occupied(logits: list[float], board: Board) -> None:
    for index, cell in enumerate(board.cells):
        if cell.player is not None:
            logits[index] = _MASK


def _softmax(logits: list[float]) -> list[float]:
    peak = max(logits)
    exps = [math.exp(logit - peak) for logit in logits]
    total = sum(exps)
    return [value / total for value in exps]
```

`_MASK` is defined at the top of `neural.py` as `_MASK = -1e9`.

**S-E. `NeuralPolicyLearner._probabilities`** (`src/tictactoe/neural.py`)

```python
    def _probabilities(self, board: Board, player: Player) -> list[float]:
        logits = self._net.forward(_features(board, player))[1]
        _mask_occupied(logits, board)
        return _softmax(logits)
```

**S-F. `NeuralPolicyLearner.choose_position`** (`src/tictactoe/neural.py`)

```python
    def choose_position(self, game: Game, explore: bool = True) -> Position:
        probabilities = self._probabilities(game.board, game.current_player)
        free = _free_indices(game.board)
        if not explore:
            return Position.from_index(max(free, key=probabilities.__getitem__))
        roll = self._rng.random()
        cumulative = 0.0
        for index in free:
            cumulative += probabilities[index]
            if roll < cumulative:
                return Position.from_index(index)
        return Position.from_index(free[-1])
```

**S-G1. `NeuralPolicyLearner.learn`, part 1** (`src/tictactoe/neural.py`)

```python
    def learn(self, experience: Experience) -> None:
        value = self._values.get(experience.board, 0.0)
        advantage = experience.reward - value
        self._values[experience.board] = self._value_rate * value + (1.0 - self._value_rate) * experience.reward
        if advantage == 0.0:
            return
```

**S-G2. `NeuralPolicyLearner.learn`, part 2** (`src/tictactoe/neural.py`)

```python
        features = _features(experience.board, experience.player)
        hidden, logits = self._net.forward(features)
        _mask_occupied(logits, experience.board)
        probabilities = _softmax(logits)
        grad_logits = [-probability for probability in probabilities]
        grad_logits[experience.action.index] += 1.0
        for index in range(_INPUT_SIZE):
            grad_logits[index] *= advantage
        self._net.update(grad_logits, hidden, features, self._learning_rate)
```

**S-H1. `_Feedforward.update`, part 1: the output layer** (`src/tictactoe/neural.py`, lines 32 to 41)

```python
    def update(self, grad_logits: list[float], hidden: list[float], x: tuple[float, ...], learning_rate: float) -> None:
        grad_hidden = [0.0 for _ in self._b1]
        for out_index, grad_logit in enumerate(grad_logits):
            if grad_logit == 0.0:
                continue
            row = self._w2[out_index]
            for hidden_index, weight in enumerate(row):
                row[hidden_index] += learning_rate * grad_logit * hidden[hidden_index]
                grad_hidden[hidden_index] += grad_logit * weight
            self._b2[out_index] += learning_rate * grad_logit
```

**S-H2. `_Feedforward.update`, part 2: through `tanh` to the input layer** (`src/tictactoe/neural.py`, lines 42 to 50)

```python
        for hidden_index in range(len(self._b1)):
            grad_hidden[hidden_index] *= 1.0 - hidden[hidden_index] * hidden[hidden_index]
        for hidden_index, grad_z in enumerate(grad_hidden):
            if grad_z == 0.0:
                continue
            row = self._w1[hidden_index]
            for input_index, weight in enumerate(row):
                row[input_index] += learning_rate * grad_z * x[input_index]
            self._b1[hidden_index] += learning_rate * grad_z
```

**S-I1. `ThreatBuilderStrategy.choose_position`, part 1** (`src/tictactoe/strategies.py`)

```python
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
```

**S-I2. `ThreatBuilderStrategy.choose_position`, part 2** (`src/tictactoe/strategies.py`)

```python
        forks = [position for position in free if self._threat_count(board.with_mark(position, me), me) >= 2]
        if forks:
            return self.rng.choice(forks)
        builds = [position for position in free if self._threat_count(board.with_mark(position, me), me) >= 1]
        if builds:
            return self.rng.choice(builds)
        return self.rng.choice(free)
```

**S-I3. `ThreatBuilderStrategy._threat_count`** (`src/tictactoe/strategies.py`)

```python
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
```

**S-J. Deep training in `main.py`** (lines 78 to 83)

```python
    x_net = NeuralPolicyLearner(learning_rate=0.1, rng=random.Random(0))
    x_net_summary = Trainer().train(x_net, X, ThreatBuilderStrategy(random.Random(7)), EPISODES)
    o_net = NeuralPolicyLearner(learning_rate=0.1, rng=random.Random(1))
    o_net_summary = Trainer().train(o_net, O, ThreatBuilderStrategy(random.Random(8)), EPISODES)
    print(f"deep X vs threat-builder: won {x_net_summary.wins}, drew {x_net_summary.draws}, lost {x_net_summary.losses}")
    print(f"deep O vs threat-builder: won {o_net_summary.wins}, drew {o_net_summary.draws}, lost {o_net_summary.losses}")
```

**S-K. The demo games after training in `main.py`** (lines 86 to 87)

```python
    run_match(engine, FirstAvailableStrategy(), o_net, explore=False)
    run_match(engine, x_net, o_net, explore=False)
```

**S-L. The video 5 logits, for comparison** (`src/tictactoe/learning.py`, `PolicyLearner._probabilities`)

```python
        logits = [
            sum(weight * feature for weight, feature in zip(self._weights[action], features))
            for action in free
        ]
```

### 5.2 Structure facts

- `NeuralPolicyLearner.__init__` has the defaults `hidden_size=16`, `learning_rate=0.1`, `value_rate=0.9`. `main.py` uses `learning_rate=0.1`.
- `_INPUT_SIZE = SIZE * SIZE` = 9. The network is `_Feedforward(_INPUT_SIZE, hidden_size, _INPUT_SIZE, self._rng)`: 9 → 16 → 9.
- `W1` (`_w1`): 16 rows × 9 weights = 144. `b1` (`_b1`): 16. `W2` (`_w2`): 9 rows × 16 weights = 144. `b2` (`_b2`): 9. Total: **313** numbers.
- Initial weights: `W1` uniform in ±1/√9 = ±0.333. `W2` uniform in ±1/√16 = ±0.25. All biases start at 0.0.
- The video 5 `PolicyLearner` has 9 × 10 = **90** weights (9 cells plus 1 bias feature) and no hidden layer.
- **Input difference.** The video 5 `_features` (in `learning.py`) appends a constant `1.0` as a tenth feature. The video 6 `_features` (in `neural.py`) returns 9 values only. The network has no bias feature in the input. The layers have the bias vectors `b1` and `b2`.
- **Masking difference.** The video 5 learner computes logits for free cells only. The video 6 network computes 9 logits and then sets occupied cells to −1e9.
- After the mask, `math.exp(-1e9 - peak)` gives exactly `0.0`. Thus an occupied cell has probability exactly 0.0, and its entry in `grad_logits` is exactly 0.0 (unless it is the chosen cell, which cannot happen because the chosen cell is free).
- In `update`, the check `if grad_logit == 0.0: continue` skips the `W2` rows and `b2` entries of masked outputs.
- **Old `W2` weights.** In `update`, the line `for hidden_index, weight in enumerate(row)` reads `weight` before the next line changes `row[hidden_index]`. Thus `grad_hidden` uses the **pre-update** `W2` weights. The script in 5.9 confirms this: the difference is 2.8e-17 (rounding only).
- The learning rule is the same as video 5. Video 5: `scale = learning_rate · advantage · (indicator − probabilities[position])`. Video 6: `grad_logits = advantage · (one_hot(chosen) − π)`, and `update` multiplies by `learning_rate` where the weights change.
- The code applies `+=` (gradient ascent on `advantage · log π`). A negative advantage makes the chosen logit go down.
- `learn` returns early when `advantage == 0.0`. The value table update happens before that check.
- `Trainer.train` calls `learner.choose_position(game)` with no `explore` argument. Thus training always uses `explore=True` (sampling). The `TrainingSummary` counts every training game, from the first game with random weights to the last game.
- `Trainer.train` calls `learn` for each move of the learner **after** the game ends, in move order, with the same final reward for each move.
- `main.py` uses `EPISODES = 6000`.

### 5.3 The example board (from the real demo output)

The example board is the board after four moves in the final demo game (`NeuralPolicyLearner (X) vs NeuralPolicyLearner (O)`, `/tmp/ttt_main_output.txt`, lines 317 to 321):

```text
 X |   | O 
---+---+---
   |   |   
---+---+---
   | X | O 
```

- X marks: cells 0 and 7. O marks: cells 2 and 8. X is to move.
- O has a threat: cells 2 and 8 are O, cell 5 is empty (line 2-5-8).
- Input vector for X (`_features(board, X)`): `(1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0)`.

### 5.4 Forward pass numbers (untrained network, `NeuralPolicyLearner(learning_rate=0.1, rng=random.Random(0))`)

This is the same seed as `x_net` in `main.py`, before any training.

- `W1` row 0, the four weights for the marked cells: cell 0: 0.2296 (input +1), cell 2: −0.0530 (input −1), cell 7: −0.1311 (input +1), cell 8: −0.0156 (input −1).
- Weighted sum for hidden unit 0: 0.2296 + 0.0530 − 0.1311 + 0.0156 = **0.167**. Bias `b1[0]` = 0.0. `tanh(0.167)` = **0.166** (0.1655).
- All 16 hidden values (3 decimals): `[0.166, 0.004, 0.111, 0.119, -0.124, 0.042, -0.016, 0.107, 0.054, 0.507, -0.021, 0.069, 0.335, -0.360, 0.649, -0.691]`.
- Hidden units shown on screen: h0 = 0.166, h9 = 0.507, h14 = 0.649, h15 = −0.691.
- 9 logits (3 decimals): `[0.057, -0.413, 0.129, -0.140, -0.068, 0.205, 0.137, 0.077, 0.054]`.
- After the mask: cells 0, 2, 7, 8 become −1e9 (show as "−1e9").
- Probabilities (2 decimals, on screen): cell 1: **0.14**, cell 3: **0.18**, cell 4: **0.19**, cell 5: **0.25**, cell 6: **0.24**, cells 0, 2, 7, 8: **0.00**. The sum is 1.0.
- Probabilities (4 decimals): cell 1: 0.1367, cell 3: 0.1797, cell 4: 0.1930, cell 5: 0.2537, cell 6: 0.2369.
- The highest probability is cell 5 (the block). The weights are random, so this is chance.

### 5.5 Play-a-move numbers (same untrained network)

- Greedy (`explore=False`): cell **5** (`Position(row=1, column=2)`).
- Sampling (`explore=True`): the first `rng.random()` after the weights are made is **0.4147**. Running total in free-cell order: cell 1: 0.1367, cell 3: 0.3164, cell 4: 0.5094. 0.4147 < 0.5094, so the network samples cell **4** (`Position(row=1, column=1)`).
- In the real final demo game, the trained X network also played cell 4 on this board (output lines 324 to 328).

### 5.6 Learning numbers (one example update, same untrained network)

Scenario (an example, not a real training step): X plays cell 4 on the example board. Then O wins at cell 5. The reward for X is −1.0. The value table is empty.

- `value` = 0.0. `advantage` = −1.0 − 0.0 = **−1.0**.
- New value for this board: 0.9 · 0.0 + 0.1 · (−1.0) = **−0.1**.
- `one_hot(4)`: `[0, 0, 0, 0, 1, 0, 0, 0, 0]`.
- `one_hot(4) − π`: cell 1: −0.137, cell 3: −0.180, cell 4: +0.807, cell 5: −0.254, cell 6: −0.237, others 0.
- `grad_logits` = advantage · (one_hot − π): cell 0: 0.0, cell 1: **+0.137**, cell 2: 0.0, cell 3: **+0.180**, cell 4: **−0.807**, cell 5: **+0.254**, cell 6: **+0.237**, cell 7: 0.0, cell 8: 0.0.
- **Output layer, output 4** (learning rate 0.1): change of `W2[4][j]` = 0.1 · (−0.807) · h_j.
  - j = 0: old −0.0027, change −0.0134, new −0.0161.
  - j = 9: old −0.2083, change −0.0409, new −0.2491.
  - j = 14: old −0.0919, change **−0.0524**, new −0.1443.
  - j = 15: old −0.1432, change +0.0557, new −0.0875 (h15 is negative, so the change is positive).
  - `b2[4]` changes by 0.1 · (−0.807) = **−0.0807**.
- **Backpropagation to hidden unit 14** (`grad_hidden[14]` = sum of `grad_logit · W2[o][14]` with old weights):
  - output 1: 0.137 × (−0.1299) = **−0.018**
  - output 3: 0.180 × 0.1277 = **+0.023**
  - output 4: −0.807 × (−0.0919) = **+0.074**
  - output 5: 0.254 × (−0.1126) = **−0.029**
  - output 6: 0.237 × 0.2049 = **+0.049**
  - outputs 0, 2, 7, 8: skipped (gradient 0.0).
  - Sum: `grad_hidden[14]` = **0.099** (0.0993).
- **Through `tanh`:** h14 = 0.649. Slope `1 − h²` = **0.578** (0.5783). `grad_z` = 0.0993 × 0.5783 = **0.057** (0.0575).
- **Input layer, row 14 of `W1`:** change = 0.1 × 0.0575 × input = **±0.0057**.
  - cell 0 (input +1): old 0.3074, new 0.3131 (+0.0057).
  - cell 2 (input −1): old −0.2507, new −0.2565 (−0.0057).
  - cell 7 (input +1): old −0.0496, new −0.0438 (+0.0057).
  - cell 8 (input −1): old −0.2657, new −0.2714 (−0.0057).
  - cell 4 (input 0): old 0.2005, new 0.2005 (no change). All empty cells: no change.
  - `b1[14]` changes by +0.0057.
- Other hidden units, for reference: h0: `grad_hidden` 0.0962, slope 0.9726, `grad_z` 0.0935. h9: 0.1194, 0.7435, 0.0888. h15: 0.1208, 0.5228, 0.0632.
- **After this one update**, probabilities on the same board: cell 1: 0.14, cell 3: 0.19, cell 4: **0.13** (was 0.19), cell 5: **0.27** (was 0.25), cell 6: 0.26 (4 decimals: 0.1428, 0.1936, 0.1339, 0.2739, 0.2557).
- The code values after `learn` agree with the hand calculation: `W2[4]` at j = 0, 9, 14, 15 is `[-0.0161, -0.2491, -0.1443, -0.0875]`. `W1[14]` at cells 0, 2, 7, 8, 4 is `[0.3131, -0.2565, -0.0438, -0.2714, 0.2005]`.

### 5.7 Training opponent facts

- Priority order in `ThreatBuilderStrategy.choose_position`: (1) win, (2) block, (3) fork (a move that makes 2 or more threats), (4) build (a move that makes 1 or more threats), (5) a random free cell. In each tier, `self.rng.choice` picks at random.
- `ThreatBuilderStrategy` holds an injected `random.Random`. `main.py` uses `random.Random(7)` for the X training run and `random.Random(8)` for the O training run.
- Measured speed on the test machine (pure Python): `ThreatBuilderStrategy` on the empty board: about **4 ms** per move (average of 1000 calls). `MinimaxStrategy` on the empty board: about **123 s** for one move. `MinimaxStrategy` after one mark: about **14 s** for one move. Speed depends on the machine.
- Video 5 tabular results against `FirstAvailableStrategy` (real output, lines 117 to 118): `tabular X vs naive: won 5968, drew 7, lost 25` and `tabular O vs naive: won 5960, drew 11, lost 29`.
- Real video 5 demo game `PolicyLearner (X) vs PolicyLearner (O)` (output lines 181 to 226): X 2, O 6, X 4, O 8, X 5, O 7. Before X's third move, O has a threat at cell 7 (line 6-7-8). X plays cell 5 and does not block. O wins at cell 7.
- Blocking after naive training (measured by the episode 5 writer, reported in episode 5): the learners trained against `FirstAvailableStrategy` block a two-in-a-row at about the random rate (O: 29% against a random rate of 30%; X: 37% against a random rate of 33%). Do not say "never learn to block".
- The value baseline: without the baseline (`value_rate=1.0`), the linear learner against `ThreatBuilderStrategy` lost 58 of the last 500 games, against 3 with the baseline (episode 5 writer). No clear oscillation was seen. This episode does not claim oscillation.
- Self-play: `AGENTS.md` and the article report that self-play did not fix the problem (the first-mover advantage dominates, and the O seat only draws or loses). `main.py` does not contain a self-play run. This episode does not reproduce that claim. The narration says "the project notes report".

### 5.8 Results and demo games (real output from `/tmp/ttt_main_output.txt`)

Training summaries (lines 229 to 230):

```text
deep X vs threat-builder: won 1902, drew 3220, lost 878
deep O vs threat-builder: won 3, drew 747, lost 5250
```

- X seat: won 31.7%, drew 53.7%, lost 14.6%.
- O seat: won 0.05%, drew 12.5%, lost 87.5%.
- A re-run of the X training (script 5.9.E) gives the same summary, `TrainingSummary(wins=1902, draws=3220, losses=878)`. The run is deterministic.

**Demo game 1: `FirstAvailableStrategy (X) vs NeuralPolicyLearner (O)`, `explore=False`** (lines 232 to 291). Moves by cell index: X 0, O 2, X 1, O 8, X 3, O 7, X 4, O 5. Result: `GameStatus.O_WON`.

Board before O's third move (after X 3):

```text
 X | X | O 
---+---+---
 X |   |   
---+---+---
   |   | O 
```

- At this board, O can win at cell 5 (line 2-5-8). X threatens to win at cell 6 (line 0-3-6).
- The O network plays cell 7. It does not take the win at 5, and it does not block 6. The move makes a fork for O (threats at 5 and 6).
- `FirstAvailableStrategy` plays cell 4 (the first free cell), not cell 6.
- O plays cell 5 and wins (line 2-5-8). Final board:

```text
 X | X | O 
---+---+---
 X | X | O 
---+---+---
   | O | O 
```

**Demo game 2: `NeuralPolicyLearner (X) vs NeuralPolicyLearner (O)`, `explore=False`** (lines 293 to 359). Moves: X 0, O 2, X 7, O 8, X 4, O 1, X 6, O 3, X 5. Result: `GameStatus.DRAW`.

- After O 8 (the example board from 5.3), O threatens cell 5. X plays 4. X does not block 5. X now threatens cell 1 (line 1-4-7).
- O can win at 5. O plays 1. O blocks X, but O misses its win.
- X plays 6. X does not block 5. X now threatens cell 3 (line 0-3-6).
- O can win at 5. O plays 3. O blocks X again, and O misses its win again.
- X plays 5, the last free cell. Draw. Final board:

```text
 X | O | O 
---+---+---
 O | X | X 
---+---+---
 X | X | O 
```

### 5.9 Scripts to reproduce the numbers

Run each script from the repository root. Scripts A, B, C, and E take a few seconds. Script D takes more than two minutes. Scripts F, G, and H train learners and take several minutes each.

**5.9.A Forward pass and play-a-move (sections 5.3, 5.4, 5.5)**

```sh
uv run python -c "
import random, math
from tictactoe import NeuralPolicyLearner, Game, Position, X
from tictactoe.neural import _features, _mask_occupied, _softmax
net = NeuralPolicyLearner(learning_rate=0.1, rng=random.Random(0))
g = Game.start('demo').game
for i in (0, 2, 7, 8):
    g = g.place_mark(Position.from_index(i)).game
print(g.board.render()); print('to move', g.current_player)
x = _features(g.board, g.current_player); print('x', x)
h, logits = net._net.forward(x)
z0 = sum(w * v for w, v in zip(net._net._w1[0], x))
print('W1 row0', [round(w, 4) for w in net._net._w1[0]], 'z0', round(z0, 4), 'tanh', round(math.tanh(z0), 4))
print('hidden', [round(v, 3) for v in h])
print('logits', [round(v, 3) for v in logits])
m = list(logits); _mask_occupied(m, g.board); p = _softmax(m)
print('probs', [round(v, 4) for v in p], 'sum', sum(p))
st = net._rng.getstate(); print('roll', net._rng.random()); net._rng.setstate(st)
print('explore pick', net.choose_position(g), 'greedy pick', net.choose_position(g, explore=False))
"
```

**5.9.B One learning update (section 5.6)**

```sh
uv run python -c "
import random, copy
from tictactoe import NeuralPolicyLearner, Game, Position, Experience, X
from tictactoe.neural import _features, _mask_occupied, _softmax
net = NeuralPolicyLearner(learning_rate=0.1, rng=random.Random(0))
g = Game.start('demo').game
for i in (0, 2, 7, 8):
    g = g.place_mark(Position.from_index(i)).game
x = _features(g.board, X); h, logits = net._net.forward(x)
m = list(logits); _mask_occupied(m, g.board); p = _softmax(m)
adv = -1.0
gl = [-q for q in p]; gl[4] += 1.0; gl = [v * adv for v in gl]
print('grad_logits', [round(v, 4) for v in gl])
W2 = copy.deepcopy(net._net._w2); W1 = copy.deepcopy(net._net._w1)
for j in (0, 9, 14, 15):
    print(f'W2[4][{j}] old={W2[4][j]:.4f} change={0.1*gl[4]*h[j]:.4f}')
gh = [sum(gl[o] * W2[o][j] for o in range(9)) for j in range(16)]
gz = [gh[j] * (1 - h[j] * h[j]) for j in range(16)]
for o in (1, 3, 4, 5, 6):
    print('output', o, 'share', round(gl[o] * W2[o][14], 4))
print('grad_hidden14', round(gh[14], 4), 'slope', round(1 - h[14] ** 2, 4), 'grad_z14', round(gz[14], 4))
for i in (0, 2, 7, 8, 4):
    print(f'W1[14][{i}] old={W1[14][i]:.4f} change={0.1*gz[14]*x[i]:.4f}')
b1 = list(net._net._b1)
net.learn(Experience(g.board, X, Position.from_index(4), -1.0))
print('old-W2 check, max diff', max(abs((a - b) / 0.1 - c) for a, b, c in zip(net._net._b1, b1, gz)))
print('W2[4] new', [round(net._net._w2[4][j], 4) for j in (0, 9, 14, 15)])
print('W1[14] new', [round(net._net._w1[14][i], 4) for i in (0, 2, 7, 8, 4)])
print('value', net._values[g.board])
m2 = list(net._net.forward(x)[1]); _mask_occupied(m2, g.board)
print('probs after', [round(v, 4) for v in _softmax(m2)])
"
```

**5.9.C Parameter count**

```sh
uv run python -c "
import random
from tictactoe import NeuralPolicyLearner
n = NeuralPolicyLearner(rng=random.Random(0))._net
print(sum(map(len, n._w1)) + len(n._b1) + sum(map(len, n._w2)) + len(n._b2))
"
```

**5.9.D Strategy speed (section 5.7)** (the minimax part takes more than two minutes)

```sh
uv run python -c "
import random, time
from tictactoe import MinimaxStrategy, ThreatBuilderStrategy, Game, Position
g = Game.start('t').game
tb = ThreatBuilderStrategy(random.Random(7)); t = time.perf_counter()
for _ in range(1000): tb.choose_position(g)
print('threat builder per move', (time.perf_counter() - t) / 1000)
g1 = g.place_mark(Position.from_index(0)).game
t = time.perf_counter(); MinimaxStrategy().choose_position(g1); print('minimax after one mark', time.perf_counter() - t)
t = time.perf_counter(); MinimaxStrategy().choose_position(g); print('minimax empty board', time.perf_counter() - t)
"
```

**5.9.E Threat analysis of the demo games (section 5.8)**

```sh
uv run python -c "
from tictactoe import Game, Position
from tictactoe.value_objects import WINNING_LINES
def wins_for(board, pl):
    out = set()
    for line in WINNING_LINES:
        v = [board.player_at(Position.from_index(i)) for i in line]
        if v.count(pl) == 2 and v.count(None) == 1:
            out.add([i for i, vv in zip(line, v) if vv is None][0])
    return sorted(out)
for name, seq in (('naive vs O-net', [0, 2, 1, 8, 3, 7, 4, 5]), ('X-net vs O-net', [0, 2, 7, 8, 4, 1, 6, 3, 5])):
    print(name); g = Game.start('x').game
    for idx in seq:
        me = g.current_player
        print(' ', me.symbol, 'plays', idx, 'own win cells', wins_for(g.board, me), 'opponent win cells', wins_for(g.board, me.opponent))
        g = g.place_mark(Position.from_index(idx)).game
    print(' ', g.status)
"
```

**5.9.F Greedy test games after training (section 5.10)**

```sh
uv run python - <<'EOF'
import random
from tictactoe import NeuralPolicyLearner, Trainer, ThreatBuilderStrategy, Game, Position, X, O, GameStatus
from tictactoe.value_objects import WINNING_LINES
def wins_for(board, pl):
    out = set()
    for line in WINNING_LINES:
        v = [board.player_at(Position.from_index(i)) for i in line]
        if v.count(pl) == 2 and v.count(None) == 1:
            out.add([i for i, vv in zip(line, v) if vv is None][0])
    return out
for seat, seed, oseed in ((X, 0, 7), (O, 1, 8)):
    net = NeuralPolicyLearner(learning_rate=0.1, rng=random.Random(seed))
    s = Trainer().train(net, seat, ThreatBuilderStrategy(random.Random(oseed)), 6000)
    opp = ThreatBuilderStrategy(random.Random(99))
    w = d = l = need_block = blocked = can_win = took = 0
    for ep in range(1000):
        g = Game.start(str(ep)).game
        while g.status is GameStatus.IN_PROGRESS:
            if g.current_player == seat:
                own = wins_for(g.board, seat); th = wins_for(g.board, seat.opponent)
                p = net.choose_position(g, explore=False).index
                if own:
                    can_win += 1; took += p in own
                elif th:
                    need_block += 1; blocked += p in th
            else:
                p = opp.choose_position(g).index
            g = g.place_mark(Position.from_index(p)).game
        if g.status is GameStatus.DRAW: d += 1
        elif (g.status is GameStatus.X_WON) == (seat == X): w += 1
        else: l += 1
    print(seat.symbol, 'train', s, 'test W/D/L', w, d, l, 'wins taken', took, '/', can_win, 'blocked', blocked, '/', need_block)
EOF
```

**5.9.G The linear policy against the threat builder (section 5.10)**

```sh
uv run python -c "
import random
from tictactoe import PolicyLearner, Trainer, ThreatBuilderStrategy, X, O
for seat, seed, oseed in ((X, 0, 7), (O, 1, 8)):
    l = PolicyLearner(learning_rate=0.1, rng=random.Random(seed))
    print(seat.symbol, Trainer().train(l, seat, ThreatBuilderStrategy(random.Random(oseed)), 6000))
"
```

**5.9.H Block probe on random boards (section 5.10)**

```sh
uv run python - <<'EOF'
import random
from tictactoe import NeuralPolicyLearner, Trainer, ThreatBuilderStrategy, Game, Position, X, O
from tictactoe.value_objects import WINNING_LINES
def threats(board, pl):
    out = set()
    for line in WINNING_LINES:
        v = [board.player_at(Position.from_index(i)) for i in line]
        if v.count(pl) == 2 and v.count(None) == 1:
            out.add([i for i, vv in zip(line, v) if vv is None][0])
    return out
def boards(seat):
    rng = random.Random(123); res = []; seen = set()
    while len(res) < 300:
        g = Game.start('b').game; ok = True
        for _ in range(rng.randrange(2, 7)):
            free = [i for i in range(9) if not g.board.is_occupied(Position.from_index(i))]
            g = g.place_mark(Position.from_index(rng.choice(free))).game
            if g.status.name != 'IN_PROGRESS': ok = False; break
        if not ok or g.current_player != seat or g.board in seen: continue
        if threats(g.board, seat) or len(threats(g.board, seat.opponent)) != 1: continue
        seen.add(g.board); res.append(g)
    return res
def block_rate(n, seat):
    bs = boards(seat)
    return sum(n.choose_position(g, explore=False).index in threats(g.board, seat.opponent) for g in bs) / len(bs)
for seat, seed, oseed in ((X, 0, 7), (O, 1, 8)):
    n = NeuralPolicyLearner(learning_rate=0.1, rng=random.Random(seed))
    before = block_rate(n, seat)
    Trainer().train(n, seat, ThreatBuilderStrategy(random.Random(oseed)), 6000)
    print(seat.symbol, 'untrained', round(before, 3), 'trained', round(block_rate(n, seat), 3))
EOF
```

### 5.10 Extra measurements (not in the article)

These numbers come from scripts 5.9.F, 5.9.G, and 5.9.H, and from the episode 5 writer. They keep the narration honest.

**Greedy test games after training.** Each trained network (same seeds as `main.py`) plays 1000 greedy games (`explore=False`) against a new `ThreatBuilderStrategy(random.Random(99))`.

| Network | Test won | Test drew | Test lost | Wins taken (when a win was available) | Blocks (when the opponent threatened and the network had no win) |
|---------|----------|-----------|-----------|----------------------------------------|---------------------------------------------------------------------|
| X network | 335 | 575 | 90 | 335 of 335 (100%) | 841 of 931 (90%) |
| O network | 0 | 184 | 816 | 0 of 14 (0%) | 515 of 1331 (39%) |

**The linear policy against the threat builder.** `PolicyLearner(learning_rate=0.1)` with the same seeds and the same opponents as the networks in `main.py`, 6000 training games each:

| Learner | Seat | Won | Drew | Lost |
|---------|------|-----|------|------|
| `PolicyLearner` (linear) | X | 1989 | 3612 | **399** |
| `NeuralPolicyLearner` (network) | X | 1902 | 3220 | **878** |
| `PolicyLearner` (linear) | O | 5 | 3750 | **2245** |
| `NeuralPolicyLearner` (network) | O | 3 | 747 | **5250** |

In this small experiment (one seed, 6000 games), the network did **not** get better results than the linear policy, in either seat. The network **can represent** combinations of cells. This test does not show that it uses that ability to play better.

**Block probe on random boards.** 300 random boards where the opponent has exactly one threat and the network has no win. The network plays greedily. Blocking rate:

| Network | Before training | After training |
|---------|-----------------|----------------|
| X network | 32.3% | 26.3% |
| O network | 9.7% | 24.7% |

These boards come from random play, so many of them do not look like the games against the threat builder. The X network blocks 90% of threats in its own kind of game (table above), but only about 26% on random boards. This is a sign that the blocking skill does not transfer to all boards. Do not say that the network "learned to block in general" or "generalizes to boards it has never seen".

## 6. Scenes

### Shared object: the network diagram

Scenes E6S3, E6S5, E6S9, and E6S10 use the network diagram. Each of these scenes repeats this specification. Write one builder, `make_network()`, in `video/episodes/e6/network.py`, and import it in each scene.

- Three columns of circles.
- Input column: 9 circles, radius 0.16, center x = −6.0, input `i` at y = 3.2 − 0.8·i (from y = 3.2 to y = −3.2).
- Hidden column: 16 circles, radius 0.11, center x = −3.5, hidden unit `j` at y = 3.0 − 0.4·j (from y = 3.0 to y = −3.0).
- Output column: 9 circles, radius 0.16, center x = −1.0, output `k` at y = 3.2 − 0.8·k.
- Circle stroke: main text color `#E6E6E6`, stroke width 2, no fill.
- Edges: a `Line` from each input to each hidden unit (144 lines) and from each hidden unit to each output (144 lines). Color: secondary text `#9A9AB0`, stroke width 1, opacity 0.15.
- Small labels: the cell index `0` to `8` to the left of each input circle and to the right of each output circle, secondary text `#9A9AB0`, font size 18.
- Column titles at y = 3.7: "inputs (9)" above the input column, "hidden (16, tanh)" above the hidden column, "logits (9)" above the output column. Secondary text `#9A9AB0`, font size 22.
- The builder returns a `VGroup` with named parts: `inputs[i]`, `hidden[j]`, `outputs[k]`, `edges_in[j][i]` (input `i` to hidden `j`), `edges_out[k][j]` (hidden `j` to output `k`).

---

### E6S1: Recap

- **Scene ID:** E6S1
- **Class:** `E6S1Recap`
- **Target duration:** 20 seconds

**Narration**

```text
In video 5, a linear softmax policy learned to play tic-tac-toe. <bookmark mark='weights'/> Each logit was a weighted sum of the cells. <bookmark mark='rule'/> It learned by policy gradient with a per-board value baseline. <bookmark mark='limit'/> But a weighted sum cannot combine features.
```

**Visuals**

- Title text at top center (y = 3.3): "Recap: video 5", main text `#E6E6E6`, font size 36.
- Left half: an empty board, center (−3.5, 0), cell side 1.2, stroke `#E6E6E6`, stroke width 4.
- Right half: code panel with snippet S-L, center (3.5, 0.8).
- Right half, below the code panel at (3.5, −1.6): the text "logit = Σ weight · feature", main text, font size 30.
- Right half at (3.5, −2.6): a rule box (rounded rectangle, stroke purple `#C678DD`) with the text "policy gradient + per-board value baseline", font size 24.
- Center bottom at (0, −3.4): the text "cannot combine features", red `#E06C75`, font size 30.

**Animation steps**

1. At the start: `FadeIn` the title and the board.
2. `weights`: `FadeIn` the code panel S-L. Then `Write` the text "logit = Σ weight · feature".
3. `rule`: `Create` the purple rule box with its text.
4. `limit`: `Write` the red text "cannot combine features". Hold to the end.

**Accuracy notes**

- Name the video 5 learner "a linear softmax policy". Do not call it a table of move scores or a neural network.
- The video 5 learner has 10 features: 9 cells plus 1 bias feature.
- Keep the recap at 20 seconds or less.
- Video 5 ends with the words "a weighted sum cannot combine features". Keep this wording.

---

### E6S2: Why a network

- **Scene ID:** E6S2
- **Class:** `E6S2WhyANetwork`
- **Target duration:** 45 seconds

**Narration**

```text
This series asks one question: who decides the next move? <bookmark mark='answer'/> In this last video, the answer is a small neural network. <bookmark mark='board'/> Look at this board. X is to move. O has marks in cells 2 and 8. <bookmark mark='threat'/> Cell 5 is important because cells 2 and 8 are both O. <bookmark mark='linear'/> A weighted sum adds the evidence from cell 2 and the evidence from cell 8. It cannot give extra value when both are true together. <bookmark mark='hidden'/> A hidden unit can learn a combination, such as two marks in one line. <bookmark mark='same'/> The learning rule from video 5 stays the same. Only the model changes.
```

**Visuals**

- Top center (y = 3.3): the text "Who decides the next move?", main text, font size 40.
- Left half: the example board, center (−3.5, −0.3), cell side 1.2. Show cell indices 0 to 8 in small grey `#9A9AB0` text. X marks (blue `#4C9BE8`) in cells 0 and 7. O marks (orange `#F2A541`) in cells 2 and 8.
- A label under the board at (−3.5, −2.6): "X to move", blue `#4C9BE8`, font size 28.
- A highlight on cell 5: a square outline, stroke purple `#C678DD`, stroke width 6.
- A line through cells 2, 5, 8 (vertical, right column): dashed line, orange `#F2A541`, opacity 0.6.
- Right half, top at (3.5, 1.5): the text "weighted sum: evidence(2) + evidence(8)", main text, font size 28.
- Right half at (3.5, 0.6): a red `#E06C75` text "no extra value for 'both'", font size 28.
- Right half at (3.5, −1.2): a small diagram: two circles labeled "cell 2" and "cell 8" at (2.5, −0.8) and (2.5, −1.8), both with lines to one circle labeled "hidden unit" at (4.5, −1.3). Circles stroke `#E6E6E6`. Lines stroke `#9A9AB0`.
- Right half at (3.5, −2.6): the text "hidden unit: 'both are O'", green `#98C379`, font size 28.
- Bottom center at (0, −3.5): the text "same learning rule, new model", main text, font size 30.

**Animation steps**

1. At the start: `Write` the question text at the top.
2. `answer`: `Transform` the question text into a smaller copy at top left (scale 0.6, position (−4.5, 3.5)). `FadeIn` the text "a small neural network" at top center (y = 3.3), main text, font size 36.
3. `board`: `Create` the board. `FadeIn` the marks one at a time (0.3 seconds each). `Write` "X to move".
4. `threat`: `Create` the purple outline on cell 5 and the dashed orange line through cells 2, 5, 8.
5. `linear`: `Write` "weighted sum: evidence(2) + evidence(8)". Then `Write` the red text "no extra value for 'both'".
6. `hidden`: `FadeOut` the two texts from step 5. `Create` the small diagram. `Write` the green text "hidden unit: 'both are O'".
7. `same`: `Write` the bottom text "same learning rule, new model". Hold to the end.

**Accuracy notes**

- A linear logit is a sum of one term for each cell (plus a bias). It cannot make the effect of cell 2 depend on cell 8.
- Say "a hidden unit can learn a combination". Do not say that the trained network has a hidden unit that detects exactly this pattern. Nobody checked the hidden units of the trained network.
- The learning rule is the same policy-gradient rule as video 5 (REINFORCE with a per-board value baseline).
- Do not say that the network plays better than the linear policy. In this project, it did not (section 5.10). Say only that a network **can represent** combinations.

---

### E6S3: The shape of the network

- **Scene ID:** E6S3
- **Class:** `E6S3NetworkShape`
- **Target duration:** 50 seconds

**Narration**

```text
The NeuralPolicyLearner is a feedforward neural network. <bookmark mark='inputs'/> It has nine inputs, one for each cell. <bookmark mark='hidden'/> It has sixteen hidden units. <bookmark mark='outputs'/> It has nine outputs, one logit for each cell. <bookmark mark='w1'/> The matrix W1 connects the inputs to the hidden units. It has sixteen rows of nine weights. Each hidden unit also has a bias in b1. <bookmark mark='w2'/> The matrix W2 connects the hidden units to the outputs. It has nine rows of sixteen weights, and the outputs have biases in b2. <bookmark mark='code'/> The weights start as small random numbers. The biases start at zero. <bookmark mark='count'/> That is 313 numbers in total. The linear policy in video 5 had 90.
```

**Visuals**

- The network diagram (shared object), on the left half. Specification: input column 9 circles radius 0.16 at x = −6.0, y = 3.2 − 0.8·i; hidden column 16 circles radius 0.11 at x = −3.5, y = 3.0 − 0.4·j; output column 9 circles radius 0.16 at x = −1.0, y = 3.2 − 0.8·k; circle stroke `#E6E6E6` width 2; 288 edges `#9A9AB0`, width 1, opacity 0.15; index labels font size 18 `#9A9AB0`; column titles at y = 3.7, font size 22, `#9A9AB0`.
- Label "W1: 16 × 9" at (−4.75, −3.6), main text, font size 24.
- Label "W2: 9 × 16" at (−2.25, −3.6), main text, font size 24.
- Right half: code panel with snippet S-A, center (3.6, 1.2), scaled to a width of 6.4.
- Right half, a count table at (3.6, −2.0), main text, font size 26, four lines:
  - "W1  144"
  - "b1   16"
  - "W2  144"
  - "b2    9"
- Under the table at (3.6, −3.3): "total 313 (video 5: 90)", green `#98C379`, font size 30.

**Animation steps**

1. At the start: nothing on screen except the column titles.
2. `inputs`: `Create` the 9 input circles and their index labels, from top to bottom (lag ratio 0.1).
3. `hidden`: `Create` the 16 hidden circles (lag ratio 0.05).
4. `outputs`: `Create` the 9 output circles and their index labels.
5. `w1`: `Create` the 144 input-to-hidden edges (run time 1.5 seconds). Then `Write` "W1: 16 × 9".
6. `w2`: `Create` the 144 hidden-to-output edges (run time 1.5 seconds). Then `Write` "W2: 9 × 16".
7. `code`: `FadeIn` the code panel S-A. `Indicate` the lines with `rng.uniform` (lines 4 and 6 of the snippet) and then the lines with `0.0` (lines 5 and 7).
8. `count`: `Write` the count table line by line. Then `Write` the green total. Hold to the end.

**Accuracy notes**

- 9 inputs → 16 hidden units (`tanh`) → 9 outputs (logits). Then mask, then softmax.
- `W1` is 16 rows × 9 weights. `W2` is 9 rows × 16 weights. `b1` has 16 values. `b2` has 9 values. The total is 313.
- `W1` starts uniform in ±0.333. `W2` starts uniform in ±0.25. Biases start at 0.0.
- The video 5 `PolicyLearner` has 90 weights (9 × 10).
- Say "feedforward neural network". Do not say "deep network" in the narration; one hidden layer is not deep. (`main.py` prints the label "deep". That is the project's label, not a technical claim.)

---

### E6S4: The network reads the board

- **Scene ID:** E6S4
- **Class:** `E6S4ReadTheBoard`
- **Target duration:** 40 seconds

**Narration**

```text
First, the network reads the board. <bookmark mark='encode'/> The encoding is the same as in video 5. A mark of the player to move is plus one. A mark of the opponent is minus one. An empty cell is zero. <bookmark mark='nobias'/> One detail is different. The video 5 input had a tenth feature that was always one. This input has only nine values. The biases b1 and b2 do that job now. <bookmark mark='vector'/> This board comes from the last demo game. X is to move. So the input is one, zero, minus one, zero, zero, zero, zero, one, minus one.
```

**Visuals**

- Left half: the example board at (−3.5, 0.5), cell side 1.2, with cell indices. X marks (blue `#4C9BE8`) in cells 0 and 7. O marks (orange `#F2A541`) in cells 2 and 8.
- Under the board at (−3.5, −1.8): "X to move", blue `#4C9BE8`, font size 28.
- Right half: code panel with snippet S-B, center (3.6, 1.3).
- Right half at (3.6, −1.4): a legend with three rows, font size 26: "+1 = mark of the player to move" (blue `#4C9BE8`), "−1 = mark of the opponent" (orange `#F2A541`), "0 = empty" (grey `#9A9AB0`).
- Bottom, full width at y = −3.2: the input vector as 9 small boxes (width 0.9, height 0.6, spaced 1.0 apart, centered at x = 0). Box values: `1`, `0`, `−1`, `0`, `0`, `0`, `0`, `1`, `−1`. Box stroke: blue `#4C9BE8` for `1`, orange `#F2A541` for `−1`, grey `#9A9AB0` for `0`. Small index labels `0` to `8` above the boxes, font size 18, grey.
- A crossed-out tenth box at the right end of the vector (x = 5.0): the text "1 (bias feature)" in grey with a red `#E06C75` cross line.

**Animation steps**

1. At the start: `FadeIn` the board and its marks. `Write` "X to move".
2. `encode`: `FadeIn` the code panel S-B. `Indicate` the line `values.append(1.0)`, then `values.append(-1.0)`, then `values.append(0.0)`, in sync with the three legend rows. `Write` each legend row after its `Indicate`.
3. `nobias`: `FadeIn` the grey tenth box "1 (bias feature)". Then `Create` the red cross line over it.
4. `vector`: For each cell 0 to 8, move a copy of the cell content (mark or empty) down to its vector box and `Write` the value (lag 0.3 seconds each). Hold to the end.

**Accuracy notes**

- The input is player-relative: +1 for the player to move, −1 for the opponent, 0 for empty.
- The input vector for this board, with X to move, is `(1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0)`.
- The `neural.py` `_features` has no bias feature. The `learning.py` `_features` has one. The network has bias vectors `b1` and `b2` in its layers.
- This board is real: the final demo game, after four moves (X 0, O 2, X 7, O 8).

---

### E6S5: The forward pass

- **Scene ID:** E6S5
- **Class:** `E6S5ForwardPass`
- **Target duration:** 55 seconds

**Narration**

```text
Now the forward pass. These weights are the real starting weights of the X network, before training. <bookmark mark='unit0'/> Look at hidden unit 0. It multiplies each input by its weight and adds the results. Only the four marked cells count, because the other inputs are zero. <bookmark mark='sum'/> The sum is 0.167. The bias is zero. <bookmark mark='tanh'/> Then tanh bends the sum into the range from minus one to plus one. The result is 0.166. <bookmark mark='all'/> All sixteen hidden units do the same, each with its own row of weights. <bookmark mark='logits'/> Then each output adds up the sixteen hidden values with its own row of W2. The result is nine logits. <bookmark mark='why'/> The tanh bend is important. Without it, the two layers are equal to one weighted sum.
```

**Visuals**

- The network diagram (shared object), on the left half. Specification: input column 9 circles radius 0.16 at x = −6.0, y = 3.2 − 0.8·i; hidden column 16 circles radius 0.11 at x = −3.5, y = 3.0 − 0.4·j; output column 9 circles radius 0.16 at x = −1.0, y = 3.2 − 0.8·k; circle stroke `#E6E6E6` width 2; 288 edges `#9A9AB0`, width 1, opacity 0.15; index labels font size 18 `#9A9AB0`; column titles at y = 3.7, font size 22, `#9A9AB0`.
- Input values written next to the input circles (to the right of each circle, font size 18): `1`, `0`, `−1`, `0`, `0`, `0`, `0`, `1`, `−1`. Fill input circles with value `1` in blue `#4C9BE8` (opacity 0.8), value `−1` in orange `#F2A541` (opacity 0.8), value `0` no fill.
- Right half, top: the code panel with snippet S-C, center (3.6, 2.0), scaled to a width of 6.4.
- Right half, the calculation for hidden unit 0, at (3.6, −0.6), main text, font size 24, four lines:
  - "0.2296 · (1)"
  - "+ (−0.0530) · (−1)"
  - "+ (−0.1311) · (1)"
  - "+ (−0.0156) · (−1)"
- Under it at (3.6, −2.0): "= 0.167 + b1[0] (0.0)", main text, font size 26.
- Under it at (3.6, −2.7): "tanh(0.167) = 0.166", green `#98C379`, font size 30.
- A small `tanh` graph at (3.6, −1.2), shown only at bookmark `why`: axes x from −3 to 3, y from −1 to 1, width 3.0, height 1.6, curve in main text color, the part near 0 marked with a dot at (0.167, 0.166).
- Hidden values written to the right of four hidden circles (font size 18): h0 "0.166", h9 "0.507", h14 "0.649", h15 "−0.691". Fill the hidden circle with green `#98C379` for a positive value and red `#E06C75` for a negative value, opacity equal to the absolute value.
- Logit values written to the right of the output circles (font size 18): output 0: `0.057`, 1: `−0.413`, 2: `0.129`, 3: `−0.140`, 4: `−0.068`, 5: `0.205`, 6: `0.137`, 7: `0.077`, 8: `0.054`.

**Animation steps**

1. At the start: `FadeIn` the network diagram with the input values and input fills. `FadeIn` the code panel S-C.
2. `unit0`: Set the four edges from inputs 0, 2, 7, 8 to hidden unit 0 to opacity 1.0, stroke width 3 (color `#E6E6E6`). `Indicate` the `hidden = [` block (lines 2 to 5 of the snippet). `Write` the four calculation lines one at a time.
3. `sum`: `Write` "= 0.167 + b1[0] (0.0)".
4. `tanh`: `Write` "tanh(0.167) = 0.166". `FadeIn` the green fill of hidden circle 0 and its label "0.166". Set the four bright edges back to opacity 0.15, stroke width 1.
5. `all`: `FadeOut` the calculation texts. Flash all 144 input-to-hidden edges once (opacity 0.15 → 0.5 → 0.15, run time 1.0 second). `FadeIn` the fills and labels for h9, h14, h15.
6. `logits`: `Indicate` the `logits = [` block (lines 6 to 9 of the snippet). Flash all 144 hidden-to-output edges once. `Write` the 9 logit labels (lag ratio 0.1).
7. `why`: `FadeIn` the small `tanh` graph with its dot. Hold to the end.

**Accuracy notes**

- The weights come from `NeuralPolicyLearner(learning_rate=0.1, rng=random.Random(0))`, the same seed as `x_net` in `main.py`, before training.
- The numbers must be exactly: weighted sum 0.167, `tanh` 0.166; h0 0.166, h9 0.507, h14 0.649, h15 −0.691; logits as listed.
- `b1` and `b2` are 0.0 before training.
- The logits here are before the mask. The occupied cells 0, 2, 7, 8 still have logits.
- "Without tanh, the two layers are equal to one weighted sum (plus a bias)." This is true for any two linear layers.

---

### E6S6: Mask and softmax

- **Scene ID:** E6S6
- **Class:** `E6S6MaskAndSoftmax`
- **Target duration:** 40 seconds

**Narration**

```text
The nine logits include the four occupied cells. <bookmark mark='mask'/> The function _mask_occupied sets those logits to minus one billion. <bookmark mark='softmax'/> Then _softmax changes the logits into probabilities. The probabilities add up to one. <bookmark mark='zero'/> An occupied cell gets a probability of zero. So the network cannot choose an illegal move. <bookmark mark='heat'/> The free cells get 0.14, 0.18, 0.19, 0.25, and 0.24. <bookmark mark='chance'/> Cell 5 blocks O, and it has the highest probability. But the weights are still random. That is only chance. The network has not learned anything yet.
```

**Visuals**

- Left half: a vertical list of the 9 logits at x = −5.0, y = 3.2 − 0.8·k, font size 24, main text: "0: 0.057", "1: −0.413", "2: 0.129", "3: −0.140", "4: −0.068", "5: 0.205", "6: 0.137", "7: 0.077", "8: 0.054".
- Left half: the example board at (−1.8, 0), cell side 1.2, with the X marks (blue) in cells 0 and 7 and O marks (orange) in cells 2 and 8.
- Right half: the code panel with snippet S-D, center (3.6, 1.4), scaled to a width of 6.4.
- Right half, under the code at (3.6, −1.6): code panel with snippet S-E, scaled to a width of 6.4.
- Right half at (3.6, −3.3): the text "forward → mask → softmax", main text, font size 28.

**Animation steps**

1. At the start: `FadeIn` the logit list and the board.
2. `mask`: `FadeIn` the code panel S-D. `Indicate` the line `logits[index] = _MASK`. `Transform` the logit texts of rows 0, 2, 7, 8 into "0: −1e9", "2: −1e9", "7: −1e9", "8: −1e9" in red `#E06C75`.
3. `softmax`: `Indicate` the `_softmax` function in the code panel. Move a copy of each logit text toward its board cell and `Transform` it into the probability text in that cell (two decimals, font size 24).
4. `zero`: `Write` "0.00" in grey `#9A9AB0` on top of the marks in cells 0, 2, 7, 8 (small, at the bottom right of each cell). `FadeIn` the code panel S-E. `Write` "forward → mask → softmax".
5. `heat`: Fill each free cell with green `#98C379` at an opacity equal to its probability: cell 1: 0.14, cell 3: 0.18, cell 4: 0.19, cell 5: 0.25, cell 6: 0.24. Write the probability in each free cell with two decimals, main text, font size 28.
6. `chance`: `Create` a purple `#C678DD` outline on cell 5 (stroke width 6). `Write` the text "random weights: chance" at (−1.8, −2.4), grey `#9A9AB0`, font size 26. Hold to the end.

**Accuracy notes**

- `_MASK = -1e9`. The mask changes the logit, not the probability.
- After softmax, the probability of a masked cell is exactly 0.0 in Python (`math.exp` underflows).
- The probabilities must be: cell 1: 0.14, cell 3: 0.18, cell 4: 0.19, cell 5: 0.25, cell 6: 0.24. Their sum is 1.00.
- The softmax subtracts the largest logit first (`peak`) so that `math.exp` does not overflow. This does not change the probabilities.
- Do not say that the untrained network "knows" to block. The high probability on cell 5 is chance.

---

### E6S7: Play a move

- **Scene ID:** E6S7
- **Class:** `E6S7PlayAMove`
- **Target duration:** 35 seconds

**Narration**

```text
To play, the network uses the same two modes as video 5. <bookmark mark='greedy'/> With explore set to false, it takes the free cell with the highest probability. Here, that is cell 5. <bookmark mark='sample'/> With explore set to true, it samples. It draws a random number. Here, the number is 0.41. <bookmark mark='walk'/> It adds the probabilities in cell order until the total is more than 0.41. That happens at cell 4. <bookmark mark='training'/> Training always uses this mode.
```

**Visuals**

- Left half: the example board at (−3.5, 0.6), cell side 1.2, with marks and the green heat map from E6S6 (cell 1: 0.14, cell 3: 0.18, cell 4: 0.19, cell 5: 0.25, cell 6: 0.24).
- Right half: the code panel with snippet S-F, center (3.6, 1.4), scaled to a width of 6.4.
- Bottom, full width at y = −2.8: a horizontal bar from x = −6.0 to x = 6.0 (length 12 units = probability 1.0). Split the bar into five segments in cell order: cell 1 (0.1367), cell 3 (0.1797), cell 4 (0.1930), cell 5 (0.2537), cell 6 (0.2369). Each segment has a green `#98C379` fill with opacity equal to its probability and a label above it: "1", "3", "4", "5", "6", font size 22.
- Tick labels under the bar at the running totals: "0.14" at 0.1367, "0.32" at 0.3164, "0.51" at 0.5094, "0.76" at 0.7631, "1.00" at 1.0. Font size 18, grey.
- A vertical arrow for the roll, main text `#E6E6E6`, at the position 0.4147 on the bar, label "roll = 0.41" above the arrow.

**Animation steps**

1. At the start: `FadeIn` the board with the heat map and the code panel S-F.
2. `greedy`: `Indicate` the lines `if not explore:` and `return Position.from_index(max(free, key=probabilities.__getitem__))`. Place a blue `#4C9BE8` X mark in cell 5 at 50% opacity with a label "greedy" under the board. Then `FadeOut` that mark and label.
3. `sample`: `Indicate` the line `roll = self._rng.random()`. `Create` the bar with its segments and labels. `GrowArrow` the roll arrow at 0.4147 and `Write` "roll = 0.41".
4. `walk`: `Indicate` the `for index in free:` loop. Move a small main-text dot along the bar from 0 to the end of each segment in order (cell 1, cell 3, cell 4). Stop at the end of the cell 4 segment (0.51). `Indicate` the cell 4 segment. Place a blue `#4C9BE8` X mark in cell 4 of the board.
5. `training`: `Write` the text "training: explore=True" at (−3.5, −1.5), main text, font size 26. Hold to the end.

**Accuracy notes**

- Greedy (`explore=False`) picks cell 5. Sampling with roll 0.4147 picks cell 4.
- The roll 0.4147 is the first `rng.random()` value of `random.Random(0)` after the weights are made.
- `Trainer.train` calls `choose_position(game)` without `explore`, so training uses `explore=True`. The demo games in `main.py` use `explore=False`.
- The walk goes over free cells only, in index order.

---

### E6S8: Advantage and the logit gradient

- **Scene ID:** E6S8
- **Class:** `E6S8AdvantageAndGradient`
- **Target duration:** 55 seconds

**Narration**

```text
Now the network learns. Suppose X plays cell 4, and then O wins at cell 5. <bookmark mark='reward'/> The reward for X is minus one. <bookmark mark='value'/> The value table has no entry for this board, so the value is zero. <bookmark mark='advantage'/> The advantage is the reward minus the value. That is minus one. The result was worse than expected. <bookmark mark='valueupdate'/> The value of this board moves toward the reward, to minus 0.1. <bookmark mark='onehot'/> Next, the logit gradient. Put a one at the chosen cell and a zero at the other cells. <bookmark mark='minuspi'/> Subtract the probabilities. <bookmark mark='times'/> Multiply by the advantage. <bookmark mark='result'/> Cell 4 gets minus 0.81, so its logit must go down. The other free cells get positive values, so their logits must go up. This is the same rule as in video 5.
```

**Visuals**

- Left half, top: the example board at (−4.2, 2.0), scaled to 0.6 (cell side 0.72), with X marks (blue) in cells 0, 4, 7 and O marks (orange) in cells 2, 5, 8. Draw a line through cells 2, 5, 8 in orange `#F2A541`.
- Under the board at (−4.2, 0.4): the text "O wins → reward −1", with "−1" in red `#E06C75`, font size 26.
- Left half, a small value table at (−4.2, −1.0), font size 24: "V(board) = 0.0", later "V(board) = −0.1" (red `#E06C75`).
- Left half at (−4.2, −2.0): "advantage = −1 − 0 = −1", with "−1" in red `#E06C75`, font size 26.
- Right half, top: code panel with snippet S-G1, center (3.6, 2.4), scaled to a width of 6.4.
- Right half, replaced at bookmark `onehot`: code panel with snippet S-G2 at the same place.
- Bottom half, a table of four rows at x from −1.5 to 6.5, y from −0.8 to −3.4, font size 22. Columns: cells 0 to 8. Rows:
  - "one_hot(4)": `0 0 0 0 1 0 0 0 0`
  - "− π": `0 −0.14 0 −0.18 −0.19 −0.25 −0.24 0 0`
  - "= one_hot − π": `0 −0.14 0 −0.18 +0.81 −0.25 −0.24 0 0`
  - "grad_logits (× −1)": `0 +0.14 0 +0.18 −0.81 +0.25 +0.24 0 0`
- In the last row, color positive values green `#98C379`, negative values red `#E06C75`, zero values grey `#9A9AB0`.

**Animation steps**

1. At the start: `FadeIn` the board with the O line. `FadeIn` the code panel S-G1.
2. `reward`: `Write` "O wins → reward −1".
3. `value`: `Indicate` the line `value = self._values.get(experience.board, 0.0)`. `Write` "V(board) = 0.0".
4. `advantage`: `Indicate` the line `advantage = experience.reward - value`. `Write` "advantage = −1 − 0 = −1".
5. `valueupdate`: `Indicate` the line `self._values[experience.board] = ...`. `Transform` "V(board) = 0.0" into the red "V(board) = −0.1".
6. `onehot`: `FadeOut` S-G1 and `FadeIn` S-G2. `Indicate` the line `grad_logits[experience.action.index] += 1.0`. `Write` the row "one_hot(4)".
7. `minuspi`: `Indicate` the line `grad_logits = [-probability for probability in probabilities]`. `Write` the row "− π", then the row "= one_hot − π".
8. `times`: `Indicate` the two lines `for index in range(_INPUT_SIZE):` and `grad_logits[index] *= advantage`. `Write` the row "grad_logits (× −1)" with its colors.
9. `result`: Draw a red down arrow over cell 4 in the last row and green up arrows over cells 1, 3, 5, 6. `Write` "grad_logits = advantage · (one_hot(chosen) − π)" at (0, 3.6), main text, font size 26. Hold to the end.

**Accuracy notes**

- This is an example step, not a real training step. In real training, `Trainer.train` calls `learn` for each move of the learner after the game ends, and earlier moves of the same game change the weights first.
- In the example, the value table is empty, so `value = 0.0` and `advantage = −1.0`. The new value is 0.9 · 0.0 + 0.1 · (−1.0) = −0.1.
- `grad_logits` must be: cell 1: +0.14, cell 3: +0.18, cell 4: −0.81, cell 5: +0.25, cell 6: +0.24, cells 0, 2, 7, 8: 0.
- The rule `advantage · (one_hot(chosen) − π)` is the same policy-gradient rule as video 5 (REINFORCE with a per-board value baseline). Video 5 multiplies by the learning rate in the same line. Video 6 multiplies by the learning rate in `update`.
- If `advantage` is exactly 0.0, `learn` returns before the gradient step.

---

### E6S9: Change the output layer

- **Scene ID:** E6S9
- **Class:** `E6S9OutputLayer`
- **Target duration:** 35 seconds

**Narration**

```text
Now the weights change, from right to left. <bookmark mark='outcode'/> The output layer is first. Each weight in W2 changes by the learning rate, times the logit gradient, times the hidden value. <bookmark mark='example'/> Look at output 4 and hidden unit 14. The change is 0.1 times minus 0.807 times 0.649. That is minus 0.052. <bookmark mark='bias'/> The bias of output 4 changes by 0.1 times minus 0.807. <bookmark mark='skip'/> The masked outputs have a gradient of zero, so the loop skips them.
```

**Visuals**

- The network diagram (shared object), on the left half. Specification: input column 9 circles radius 0.16 at x = −6.0, y = 3.2 − 0.8·i; hidden column 16 circles radius 0.11 at x = −3.5, y = 3.0 − 0.4·j; output column 9 circles radius 0.16 at x = −1.0, y = 3.2 − 0.8·k; circle stroke `#E6E6E6` width 2; 288 edges `#9A9AB0`, width 1, opacity 0.15; index labels font size 18 `#9A9AB0`; column titles at y = 3.7, font size 22, `#9A9AB0`.
- Gradient labels to the right of the output circles (font size 18): output 1: "+0.137", output 3: "+0.180", output 4: "−0.807", output 5: "+0.254", output 6: "+0.237" (green `#98C379` for positive, red `#E06C75` for negative); outputs 0, 2, 7, 8: "0" in grey `#9A9AB0`.
- Hidden label next to hidden circle 14: "h14 = 0.649", font size 18, green `#98C379`.
- Right half: code panel with snippet S-H1, center (3.6, 1.8), scaled to a width of 6.4.
- Right half at (3.6, −1.0), font size 24, main text: "ΔW2[4][14] = 0.1 · (−0.807) · 0.649".
- Under it at (3.6, −1.7): "= −0.052 (−0.092 → −0.144)", red `#E06C75`, font size 26.
- Under it at (3.6, −2.6): "Δb2[4] = 0.1 · (−0.807) = −0.081", red `#E06C75`, font size 24.

**Animation steps**

1. At the start: `FadeIn` the network diagram with the gradient labels on the outputs.
2. `outcode`: `FadeIn` the code panel S-H1. `Indicate` the line `row[hidden_index] += learning_rate * grad_logit * hidden[hidden_index]`. Flash the 16 edges into output 4 (opacity 0.15 → 0.6 → 0.15).
3. `example`: Set the edge from hidden 14 to output 4 to opacity 1.0, stroke width 4, red `#E06C75`. `Write` "h14 = 0.649". `Write` the two calculation lines.
4. `bias`: `Indicate` the line `self._b2[out_index] += learning_rate * grad_logit`. `Write` the `Δb2[4]` line.
5. `skip`: `Indicate` the lines `if grad_logit == 0.0:` and `continue`. Set output circles 0, 2, 7, 8 and their 64 incoming edges to opacity 0.05. Hold to the end.

**Accuracy notes**

- `W2[4][14]`: old −0.0919, change −0.0524, new −0.1443. On screen, round to −0.092 → −0.144 and a change of −0.052.
- `b2[4]` changes by −0.0807 (on screen −0.081).
- Masked outputs (0, 2, 7, 8) have `grad_logit == 0.0` exactly, so their `W2` rows and `b2` values do not change.
- The update uses `+=`. With a negative logit gradient and a positive hidden value, the weight goes down.

---

### E6S10: Backpropagation

- **Scene ID:** E6S10
- **Class:** `E6S10Backpropagation`
- **Target duration:** 80 seconds

**Narration**

```text
Now the important part: backpropagation. <bookmark mark='notnew'/> Backpropagation is not a new learning rule. It is the chain rule. It carries the same gradient back to W1. <bookmark mark='shares'/> Hidden unit 14 sends its value to every output. So its gradient collects a share from each output. Each share is the logit gradient times the W2 weight. <bookmark mark='numbers'/> The five free outputs give minus 0.018, plus 0.023, plus 0.074, minus 0.029, and plus 0.049. <bookmark mark='sum'/> The sum is 0.099. <bookmark mark='old'/> The code reads each W2 weight before it changes that weight. So the shares use the old weights. <bookmark mark='slope'/> Next, the gradient goes back through tanh. The slope of tanh is one minus h squared. For h equal to 0.649, the slope is 0.578. <bookmark mark='gz'/> 0.099 times 0.578 is 0.057. <bookmark mark='w1'/> Last, each weight in row 14 of W1 changes by 0.1, times 0.057, times its input. <bookmark mark='inputs'/> Inputs of plus one get plus 0.0057. Inputs of minus one get minus 0.0057. Empty cells have an input of zero, so their weights do not change. <bookmark mark='after'/> All sixteen hidden units do this. After this one update, the probability of cell 4 falls from 0.19 to 0.13.
```

**Visuals**

- The network diagram (shared object), on the left half. Specification: input column 9 circles radius 0.16 at x = −6.0, y = 3.2 − 0.8·i; hidden column 16 circles radius 0.11 at x = −3.5, y = 3.0 − 0.4·j; output column 9 circles radius 0.16 at x = −1.0, y = 3.2 − 0.8·k; circle stroke `#E6E6E6` width 2; 288 edges `#9A9AB0`, width 1, opacity 0.15; index labels font size 18 `#9A9AB0`; column titles at y = 3.7, font size 22, `#9A9AB0`.
- Gradient labels right of the outputs, as in E6S9: output 1 "+0.137", 3 "+0.180", 4 "−0.807", 5 "+0.254", 6 "+0.237" (green positive, red negative), 0, 2, 7, 8 "0" grey.
- Input values next to input circles: `1`, `0`, `−1`, `0`, `0`, `0`, `0`, `1`, `−1` (fills: blue `#4C9BE8` for 1, orange `#F2A541` for −1, none for 0).
- Put the title "backpropagation = chain rule" at (3.6, 3.5), main text, font size 32.
- Right half, the share table at (3.6, 1.6), font size 22, five lines, each colored by its sign (green `#98C379` positive, red `#E06C75` negative):
  - "out 1: +0.137 × (−0.130) = −0.018"
  - "out 3: +0.180 × (+0.128) = +0.023"
  - "out 4: −0.807 × (−0.092) = +0.074"
  - "out 5: +0.254 × (−0.113) = −0.029"
  - "out 6: +0.237 × (+0.205) = +0.049"
- Under it at (3.6, 0.0): "grad_hidden[14] = 0.099 (old W2)", green `#98C379`, font size 26.
- Right half at (3.6, −0.9): "slope = 1 − 0.649² = 0.578", main text, font size 26.
- Right half at (3.6, −1.6): "grad_z = 0.099 × 0.578 = 0.057", green `#98C379`, font size 26.
- Right half at (3.6, −2.5): "ΔW1[14][i] = 0.1 × 0.057 × x[i]", main text, font size 24.
- Right half at (3.6, −3.3): "cell 4: 0.19 → 0.13", red `#E06C75`, font size 28.
- Code panel with snippet S-H2: shown at bookmarks `slope` to `inputs`, at the right half center (3.6, 1.2), scaled to a width of 6.4. It replaces the share table while it is on screen.
- Small labels next to the input circles 0, 2, 7, 8 at bookmark `inputs` (font size 18): cell 0 "+0.0057" (green), cell 2 "−0.0057" (red), cell 7 "+0.0057" (green), cell 8 "−0.0057" (red). Next to input circles 1, 3, 4, 5, 6: "0" (grey).

**Animation steps**

1. At the start: `FadeIn` the network diagram with the output gradient labels and the input values. `Write` the title "backpropagation = chain rule".
2. `notnew`: Move a green `#98C379` dot along one edge from output 4 to hidden 14, then along one edge from hidden 14 to input 0 (right to left). Run time 1.5 seconds.
3. `shares`: Set the 5 edges from hidden 14 to outputs 1, 3, 4, 5, 6 to opacity 1.0, stroke width 3, main text color. Send one small dot from each of these outputs to hidden 14 at the same time (right to left).
4. `numbers`: `Write` the five share lines one at a time (lag 0.8 seconds).
5. `sum`: `Write` "grad_hidden[14] = 0.099 (old W2)". `Indicate` hidden circle 14.
6. `old`: `Indicate` the text "(old W2)". Then set the 5 bright edges back to opacity 0.15, stroke width 1.
7. `slope`: `FadeOut` the share table. `FadeIn` the code panel S-H2 at (3.6, 1.2). `Indicate` the line `grad_hidden[hidden_index] *= 1.0 - hidden[hidden_index] * hidden[hidden_index]`. `Write` "slope = 1 − 0.649² = 0.578".
8. `gz`: `Write` "grad_z = 0.099 × 0.578 = 0.057".
9. `w1`: `Indicate` the line `row[input_index] += learning_rate * grad_z * x[input_index]`. Set the 9 edges from the inputs to hidden 14 to opacity 1.0, stroke width 3. Send dots right to left along those 9 edges. `Write` "ΔW1[14][i] = 0.1 × 0.057 × x[i]".
10. `inputs`: `Write` the change labels next to the input circles. Set the edges from inputs 1, 3, 4, 5, 6 to hidden 14 back to opacity 0.15 (no change). Keep the edges from inputs 0, 2, 7, 8 bright: green `#98C379` for cells 0 and 7, red `#E06C75` for cells 2 and 8.
11. `after`: `FadeOut` the code panel S-H2. Flash all 144 input-to-hidden edges once. `Write` "cell 4: 0.19 → 0.13". Hold to the end.

**Accuracy notes**

- Backpropagation is the chain-rule method. It is not a separate learning rule. The learning rule is the policy gradient with a baseline from E6S8.
- `grad_hidden[14]` is the sum over outputs of `grad_logit · W2[o][14]`, with the **old** (pre-update) `W2` weights. The loop reads `weight` from `enumerate(row)` before it assigns `row[hidden_index]`. Script 5.9.B confirms this.
- Shares: −0.018, +0.023, +0.074, −0.029, +0.049. Sum 0.099 (0.0993). Masked outputs add nothing.
- Slope of `tanh` at h = 0.649 is 0.578. `grad_z` = 0.057 (0.0575).
- Change of `W1[14][i]` = 0.1 × 0.0575 × x[i] = +0.0057 for x = +1, −0.0057 for x = −1, 0 for x = 0. `b1[14]` changes by +0.0057.
- After this one example update: cell 4 probability 0.1930 → 0.1339 (on screen 0.19 → 0.13). Cell 5 goes from 0.25 to 0.27.
- Do not say that the input weights of empty cells never change. They do not change **in this update**, because their input is 0.

---

### E6S11: Which training opponent?

- **Scene ID:** E6S11
- **Class:** `E6S11WhichTeacher`
- **Target duration:** 45 seconds

**Narration**

```text
A learner can only learn what its training opponent teaches. <bookmark mark='naive'/> In video 5, the learner trained against FirstAvailableStrategy. That opponent never builds a threat on purpose. So the learner blocks almost no better than random. <bookmark mark='evidence'/> In the video 5 demo game, X did not block cell 7, and O won. <bookmark mark='selfplay'/> The project notes report that self-play did not fix this. The first player had too big an advantage. <bookmark mark='minimax'/> MinimaxStrategy is a strong opponent, but it is too slow. On our test machine, one early move took about 14 seconds. Six thousand training games would take many hours.
```

**Visuals**

- Left half: a board at (−3.5, 0.3), cell side 1.2, showing the final board of the video 5 demo game `PolicyLearner (X) vs PolicyLearner (O)`: X (blue) in cells 2, 4, 5; O (orange) in cells 6, 7, 8. An orange line through cells 6, 7, 8.
- Under the board at (−3.5, −1.9): "video 5: PolicyLearner (X) vs PolicyLearner (O)", grey `#9A9AB0`, font size 22.
- Right half: three option cards, stacked, each a rounded rectangle (width 6.0, height 1.4, stroke `#E6E6E6`) at (3.6, 2.2), (3.6, 0.3), (3.6, −1.6):
  - Card 1: "FirstAvailableStrategy" (bold) and "blocking ≈ random rate".
  - Card 2: "Self-play" (bold) and "first-player advantage (project notes)".
  - Card 3: "MinimaxStrategy" (bold) and "about 14 s for one early move".
- A red `#E06C75` cross (two lines) over each card when the narration rejects it.
- Bottom right at (3.6, −3.2): "we need: strong, fast, varied", green `#98C379`, font size 28.

**Animation steps**

1. At the start: nothing on screen.
2. `naive`: `FadeIn` card 1. Then `Create` the red cross over card 1.
3. `evidence`: `FadeIn` the video 5 board with marks in move order (X 2, O 6, X 4, O 8, X 5, O 7, 0.3 seconds each). `Create` a purple `#C678DD` outline on cell 7 before O plays it. `Create` the orange line through 6, 7, 8. `Write` the grey caption.
4. `selfplay`: `FadeIn` card 2. Then `Create` the red cross over card 2.
5. `minimax`: `FadeIn` card 3. Show a small clock icon (a circle with two hands) at the right end of card 3 and rotate the long hand one full turn in 1.5 seconds. `Create` the red cross over card 3. `Write` the green line "we need: strong, fast, varied". Hold to the end.

**Accuracy notes**

- `FirstAvailableStrategy` plays the first free cell. It can make a line by accident, but it never chooses a move to build a threat.
- Video 5 reports that the learners trained against `FirstAvailableStrategy` block a two-in-a-row at about the random rate (O: 29% against a random rate of 30%; X: 37% against a random rate of 33%). Say "almost no better than random". Do not say "never".
- The video 5 demo game moves are X 2, O 6, X 4, O 8, X 5, O 7 (O wins). Before X's third move (X 5), O threatens cell 7. X does not block.
- Self-play is a claim from `AGENTS.md` and the article. `main.py` has no self-play run. Say "the project notes report".
- Minimax timing on the test machine: about 14 seconds for one move after one mark, about 123 seconds on the empty board. Speed depends on the machine. Do not say "seconds per move" as an exact number for all moves. Later moves are much faster.
- "Many hours" is correct: with the learner as X, each game has at least one minimax move of about 14 seconds, so 6000 games take more than 23 hours.

---

### E6S12: The threat builder

- **Scene ID:** E6S12
- **Class:** `E6S12ThreatBuilder`
- **Target duration:** 50 seconds

**Narration**

```text
So the network trains against a new strategy: ThreatBuilderStrategy. <bookmark mark='ladder'/> It checks four rules in order. <bookmark mark='win'/> One: if a move wins, play it. <bookmark mark='block'/> Two: if the opponent can win, block that cell. <bookmark mark='fork'/> Three: if a move makes two threats at the same time, play it. That move is a fork. <bookmark mark='build'/> Four: if a move makes one threat, play it. <bookmark mark='fallback'/> If no rule applies, play a random free cell. <bookmark mark='random'/> When several moves tie in one rule, it picks one at random. So the network sees many different threats, not one fixed pattern. <bookmark mark='fast'/> One move takes about four milliseconds, because the strategy checks lines. It does not search the game tree.
```

**Visuals**

- Left half: a priority ladder of five stacked boxes (width 4.6, height 0.9, gap 0.25), centered at x = −3.6, from y = 2.4 down to y = −2.2. Box stroke purple `#C678DD`, text main `#E6E6E6`, font size 28:
  - "1. win"
  - "2. block"
  - "3. fork (2 threats)"
  - "4. build (1 threat)"
  - "5. random free cell"
- A down arrow between each pair of boxes, grey `#9A9AB0`, with the small label "none?" (font size 18).
- Left half at (−3.6, −3.3): a dice icon (a rounded square with dots) and the text "random tie-breaks", main text, font size 26.
- Right half: code panel with snippet S-I1, center (3.6, 0.6), scaled to a width of 6.6.
- Right half, replaced at bookmark `fork`: code panel with snippet S-I2 at (3.6, 1.2).
- Right half at (3.6, −2.6), shown at bookmark `fast`: "≈ 4 ms per move", green `#98C379`, font size 32, and under it "MinimaxStrategy: ≈ 14 s", red `#E06C75`, font size 26.

**Animation steps**

1. At the start: `Write` the class name "ThreatBuilderStrategy" at top center (0, 3.5), main text, font size 34.
2. `ladder`: `FadeIn` the code panel S-I1.
3. `win`: `Create` box 1. `Indicate` the lines `wins = [...]`, `if wins:`, and `return self.rng.choice(wins)`.
4. `block`: `GrowArrow` the arrow 1→2. `Create` box 2. `Indicate` the `blocks` lines.
5. `fork`: `FadeOut` S-I1. `FadeIn` S-I2. `GrowArrow` the arrow 2→3. `Create` box 3. `Indicate` the `forks` lines.
6. `build`: `GrowArrow` the arrow 3→4. `Create` box 4. `Indicate` the `builds` lines.
7. `fallback`: `GrowArrow` the arrow 4→5. `Create` box 5. `Indicate` the line `return self.rng.choice(free)`.
8. `random`: `FadeIn` the dice icon and "random tie-breaks". `Indicate` each `self.rng.choice` in the code panel. Rotate the dice icon 90 degrees two times.
9. `fast`: `FadeOut` the code panel. `Write` "≈ 4 ms per move" and "MinimaxStrategy: ≈ 14 s". Hold to the end.

**Accuracy notes**

- The order is win → block → fork → build → random free cell. The code returns from the first tier that is not empty.
- A fork is a move after which `_threat_count` is 2 or more. A build is a move after which `_threat_count` is 1 or more. A threat is a line with two marks of the player and one empty cell (snippet S-I3).
- `ThreatBuilderStrategy` is not a perfect player. It does not search. It can lose.
- `ThreatBuilderStrategy` holds an injected `random.Random`. Training uses `random.Random(7)` for the X run and `random.Random(8)` for the O run.
- Speed: about 4 ms per move on the empty board on the test machine (script 5.9.D).

---

### E6S13: Training results

- **Scene ID:** E6S13
- **Class:** `E6S13TrainingResults`
- **Target duration:** 60 seconds

**Narration**

```text
Each network trains for 6000 games against the threat builder. <bookmark mark='xseat'/> The X network won 1902, drew 3220, and lost 878. <bookmark mark='oseat'/> The O network won 3, drew 747, and lost 5250. It lost most of its games. <bookmark mark='why'/> Some facts help to explain this. O moves second. And these counts include every training game, with sampled moves, from the first game with random weights. <bookmark mark='honest'/> But tic-tac-toe is a draw with perfect play. A perfect O never loses. So the O network still has much to learn. <bookmark mark='linear'/> Now a fair comparison. The linear policy from video 5, trained in the same way, lost only 399 games as X, and 2245 as O. <bookmark mark='result'/> So in this small test, the network did not beat the linear policy. A network can represent combinations. That does not guarantee better results.
```

**Visuals**

- Top center (0, 3.4): code panel with snippet S-J, scaled to a width of 12.0.
- Left half: a stacked horizontal bar for the X network at (−3.2, 1.0), width 6.0, height 0.7. Segments: won 1902 (green `#98C379`), drew 3220 (grey `#9A9AB0`), lost 878 (red `#E06C75`). Segment widths are proportional to the counts (6000 = 6.0 units). Label at the left of the bar: "X network", blue `#4C9BE8`, font size 24. Numbers inside each segment: "1902", "3220", "878", font size 20.
- Left half: a stacked bar for the O network at (−3.2, 0.0), same size and colors. Segments: won 3, drew 747, lost 5250. Label "O network", orange `#F2A541`. Numbers: "3" (above the bar, because the segment is too thin), "747", "5250".
- Right half: two note cards (rounded rectangles, width 5.6, height 0.9, stroke `#9A9AB0`) at (3.6, 1.0) and (3.6, 0.0), font size 22: "O moves second · counts include all training games (explore=True)" and "perfect play = draw → a perfect O never loses". The second card has stroke purple `#C678DD` (a rule).
- Bottom half: a comparison table at (0, −2.2), font size 24, main text, grid lines grey `#9A9AB0`. Columns: "lost as X", "lost as O". Rows:
  - "NeuralPolicyLearner (network)": "878" | "5250"
  - "PolicyLearner (linear)": "399" | "2245"
- Color the smaller number in each column green `#98C379` and the larger number red `#E06C75`.
- Bottom center (0, −3.6): "network ≠ better results (this test)", main text, font size 26.

**Animation steps**

1. At the start: `FadeIn` the code panel S-J.
2. `xseat`: Grow the X bar segments from left to right (green, then grey, then red). `Write` the three numbers.
3. `oseat`: Grow the O bar segments from left to right. `Write` the three numbers. `Indicate` the red O segment.
4. `why`: `FadeOut` the code panel S-J. `FadeIn` note card 1.
5. `honest`: `FadeIn` note card 2.
6. `linear`: `Create` the comparison table grid. `Write` the network row, then the linear row.
7. `result`: `Indicate` the two green numbers. `Write` the bottom text. Hold to the end.

**Accuracy notes**

- The network numbers must be exactly: X: won 1902, drew 3220, lost 878. O: won 3, drew 747, lost 5250. Each sum is 6000.
- The linear numbers (script 5.9.G, same seeds, same opponents): X: won 1989, drew 3612, lost 399. O: won 5, drew 3750, lost 2245.
- The counts are training counts. Training uses `explore=True`, and the counts include the early games with random weights. They are not a test of the final network.
- Tic-tac-toe is a draw under perfect play. A perfect second player never loses.
- This is one seed and 6000 games. Say "in this small test". Do not say that networks are worse than linear policies in general.
- The article calls the X network "the success story" and the O network "under-converged". Do not use these words. Do not say that the network gets better results than the linear policy.

---

### E6S14: The demo games

- **Scene ID:** E6S14
- **Class:** `E6S14DemoGames`
- **Target duration:** 65 seconds

**Narration**

```text
After training, the demo plays with explore set to false. <bookmark mark='game1'/> Game one: FirstAvailableStrategy plays X, and the O network plays O. <bookmark mark='miss'/> Look at this board. O can win at cell 5. X can win at cell 6. The O network plays cell 7. It misses its win, and it does not block. <bookmark mark='naive'/> The naive X plays cell 4, not cell 6. <bookmark mark='owin'/> Then O plays cell 5 and wins. <bookmark mark='game2'/> Game two: the X network against the O network. <bookmark mark='blocks'/> The O network blocks two threats, at cell 1 and at cell 3. <bookmark mark='misses'/> But O also misses a win at cell 5 two times. And X leaves cell 5 open two times. <bookmark mark='draw'/> The game ends in a draw. <bookmark mark='test'/> In 1000 extra test games, the X network blocked 90 percent of threats. The O network blocked 39 percent. The networks block some threats, but they do not play perfectly.
```

**Visuals**

- Left half: board A at (−3.5, 0.3), cell side 1.2, for game 1.
- Right half: board B at (3.5, 0.3), cell side 1.2, for game 2.
- Titles above the boards at y = 2.6, font size 24, main text: "FirstAvailableStrategy (X) vs NeuralPolicyLearner (O)" above board A, "NeuralPolicyLearner (X) vs NeuralPolicyLearner (O)" above board B. Scale each title to a width of 6.0.
- Top center (0, 3.5): "explore=False", main text, font size 28.
- Win-cell markers: a small green `#98C379` dot in a cell where the player to move can win. Threat markers: a purple `#C678DD` outline on a cell where the opponent threatens to win.
- Result text under each board at y = −1.9: board A "O_WON" in orange `#F2A541`; board B "DRAW" in grey `#9A9AB0`. Font size 30.
- Bottom center (0, −2.8), shown at bookmark `test`: "1000 test games vs ThreatBuilderStrategy: X network blocked 90% · O network blocked 39%", main text, font size 24.
- Bottom center (0, −3.5): "blocks some threats · not perfect", main text, font size 28.

**Animation steps**

1. At the start: `Write` "explore=False".
2. `game1`: `Create` board A and its title. Place marks in order, 0.4 seconds each: X 0, O 2, X 1, O 8, X 3.
3. `miss`: `FadeIn` a green dot in cell 5 (O can win) and a purple outline on cell 6 (X threatens). Place O in cell 7. `Indicate` cell 5 and cell 6 in red `#E06C75` (missed win, missed block).
4. `naive`: Place X in cell 4. `Indicate` cell 6 (X did not take it).
5. `owin`: Place O in cell 5. Draw an orange line through cells 2, 5, 8. `Write` "O_WON". Remove the dot and the outline.
6. `game2`: `Create` board B and its title. Place marks in order, 0.4 seconds each: X 0, O 2, X 7, O 8, X 4.
7. `blocks`: `FadeIn` a purple outline on cell 1 (X threatens). Place O in cell 1. Place X in cell 6. `FadeIn` a purple outline on cell 3. Place O in cell 3. `Indicate` cells 1 and 3 in green `#98C379` (blocks).
8. `misses`: `FadeIn` a green dot in cell 5 of board B. `Indicate` cell 5 two times in red `#E06C75`.
9. `draw`: Place X in cell 5. `Write` "DRAW".
10. `test`: `Write` the test-game line. Then `Write` the bottom text. Hold to the end.

**Accuracy notes**

- Game 1 moves: X 0, O 2, X 1, O 8, X 3, O 7, X 4, O 5. Result `GameStatus.O_WON` (line 2-5-8).
- In game 1, before O plays 7: O can win at 5, and X can win at 6. O 7 misses both, but it makes a fork for O (5 and 6). The naive X plays 4 because 4 is its first free cell.
- Game 2 moves: X 0, O 2, X 7, O 8, X 4, O 1, X 6, O 3, X 5. Result `GameStatus.DRAW`.
- In game 2, O blocks at 1 (line 1-4-7) and at 3 (line 0-3-6). Both times, O could win at 5 (line 2-5-8). X does not block 5 with its moves 4 and 6. X plays 5 last because it is the only free cell.
- The article says that in game 1 "the net steps in on the open end" and that in game 2 "the defender holds the threats, and neither can force a win". The real output shows missed wins and missed blocks. Use the facts in these notes, not the article text.
- Test games (script 5.9.F): 1000 greedy games against `ThreatBuilderStrategy(random.Random(99))`. Blocks count only the positions where the opponent threatened and the network had no win of its own. X network: 841 of 931 (90%). O network: 515 of 1331 (39%). These test games are not in `main.py`.
- Each demo game is one game. Do not use one game as proof of a general skill.

---

### E6S15: Four brains, one game

- **Scene ID:** E6S15
- **Class:** `E6S15FourBrains`
- **Target duration:** 40 seconds

**Narration**

```text
Now compare four answers to the series question. <bookmark mark='first'/> FirstAvailableStrategy: a person wrote one rule. It does not learn, and it loses to simple threats. <bookmark mark='minimax'/> MinimaxStrategy: a person wrote a full search. It never loses, but one early move can take minutes. <bookmark mark='policy'/> PolicyLearner: training sets 90 weights by policy gradient. <bookmark mark='neural'/> NeuralPolicyLearner: training sets 313 numbers with the same rule and backpropagation. It can represent combinations. But in this project, the linear policy lost fewer games. <bookmark mark='seat'/> All four sit in the same seat: choose_position. The game rules never changed.
```

**Visuals**

- A table in the center, 5 columns × 5 rows, from x = −6.6 to x = 6.6, y = 2.8 to y = −2.2. Font size 20. Header row in main text, bold. Body rows in main text. Grid lines grey `#9A9AB0`, stroke width 1.
- Columns: "" (row names), "FirstAvailableStrategy", "MinimaxStrategy", "PolicyLearner", "NeuralPolicyLearner".
- Rows and cells:
  - "Who wrote the decision?": "a person: first free cell" | "a person: full search" | "training: 90 weights" | "training: 313 weights and biases"
  - "Does it learn?": "no" | "no" | "yes: policy gradient + baseline" | "yes: same rule + backpropagation"
  - "Speed": "instant" | "≈ 14 s to 123 s for an early move" | "fast" | "fast"
  - "Lost as X in 6000 training games vs ThreatBuilderStrategy": "not measured" | "not measured" | "399" | "878"
- Color "no" grey `#9A9AB0`, "yes" green `#98C379`, "not measured" grey `#9A9AB0`, "399" green `#98C379`, "878" red `#E06C75`.
- Under the table at (0, −2.6): "MinimaxStrategy never loses. FirstAvailableStrategy loses to simple threats.", grey `#9A9AB0`, font size 22.
- Bottom center (0, −3.4): a rounded rectangle labeled "the seat: choose_position(game)", stroke purple `#C678DD`, with four small boxes labeled "1", "2", "3", "4" above it.

**Animation steps**

1. At the start: `Create` the grid. `Write` the header row and the row names.
2. `first`: `Write` the "FirstAvailableStrategy" column cells from top to bottom (lag ratio 0.2).
3. `minimax`: `Write` the "MinimaxStrategy" column cells. `Write` the grey line under the table.
4. `policy`: `Write` the "PolicyLearner" column cells.
5. `neural`: `Write` the "NeuralPolicyLearner" column cells. `Indicate` the "399" and "878" cells.
6. `seat`: `Create` the purple seat box. Move the four small boxes into the seat box one after the other. Hold to the end.

**Accuracy notes**

- `FirstAvailableStrategy` and `MinimaxStrategy` do not learn. They have no weights. Their losses against `ThreatBuilderStrategy` were not measured, so the table says "not measured".
- `MinimaxStrategy` never loses, because it searches the full game tree. In the demo, `MinimaxStrategy` vs `MinimaxStrategy` ends in a draw. Timing on the test machine: about 14 s after one mark, about 123 s on the empty board.
- `PolicyLearner` is a linear softmax policy with 90 weights. Against `ThreatBuilderStrategy` as X: won 1989, drew 3612, lost 399 (script 5.9.G).
- `NeuralPolicyLearner` is a feedforward neural network with 313 weights and biases. It uses the same policy-gradient rule (REINFORCE with a per-board value baseline). Backpropagation carries the gradient to `W1`. Against `ThreatBuilderStrategy` as X: won 1902, drew 3220, lost 878.
- `PolicyLearner` and `NeuralPolicyLearner` have `choose_position(game, explore=True)`. The extra argument has a default, so they fit the `Strategy` protocol `choose_position(game)`.
- Do not claim that the network "generalizes to boards it has never seen". Section 5.10 shows that it does not block well on random boards.

---

### E6S16: Closing: who decides?

- **Scene ID:** E6S16
- **Class:** `E6S16Closing`
- **Target duration:** 30 seconds

**Narration**

```text
So who decides the next move? For the network, no person wrote the move rule. Rewards from 6000 games set the weights. <bookmark mark='ideas'/> If you want to go further, here are some ideas. Add a second hidden layer. Train the O network longer, or against a mix of opponents. Replace the value table with a value network. <bookmark mark='end'/> The model can change. The seat stays the same.
```

**Visuals**

- Center (0, 2.6): "Who decides the next move?", main text, font size 40.
- Under it at (0, 1.6): "rewards from 6000 games", green `#98C379`, font size 32.
- Center, three idea cards (rounded rectangles, width 3.8, height 1.3, stroke `#9A9AB0`, dashed) at (−4.4, −0.4), (0, −0.4), (4.4, −0.4), font size 22, main text:
  - "a second hidden layer"
  - "train O longer / mix of opponents"
  - "a value network"
- Above the cards at (0, 0.7): "ideas to try", grey `#9A9AB0`, font size 24.
- Bottom center (0, −2.6): "The model can change. The seat stays the same.", main text, font size 30.

**Animation steps**

1. At the start: `Write` the question. Then `Write` "rewards from 6000 games".
2. `ideas`: `Write` "ideas to try". `FadeIn` the three idea cards one at a time (lag 1.5 seconds), in sync with the narration.
3. `end`: `Write` the bottom line. Hold for 2 seconds. `FadeOut` all objects.

**Accuracy notes**

- This is the last video of the series. Do not add a hook to a next video.
- Present the three ideas as ideas for the viewer. Do not say that the project will add them or that they will work.
- A value network is a network that estimates the value of a board. The project does not contain one.

---

## 7. Closing and hook

Scene E6S16 is the closing scene. This is the series finale, so the scene does not name a problem for a next video. It returns to the series question, "Who decides the next move?", and gives three ideas that a viewer can try: a second hidden layer, a longer or more varied training for the O network, and a value network in place of the value table.

## 8. Checks

Answer each question with yes or no. Every answer must be "yes".

1. Does the video call the `NeuralPolicyLearner` a feedforward neural network with 9 inputs, 16 hidden units with `tanh`, and 9 outputs?
2. Does the video say that the network uses the same policy-gradient rule as video 5 (REINFORCE with a per-board value baseline)?
3. Does the video say that backpropagation is the chain-rule method that carries the gradient back, and not a separate learning rule?
4. Does the video say that the input has 9 values with no bias feature, and that the layers have the biases `b1` and `b2`?
5. Is the total number of weights and biases on screen 313, and is the video 5 count on screen 90?
6. Is the example board X in cells 0 and 7, O in cells 2 and 8, with X to move, and is the input vector `1, 0, −1, 0, 0, 0, 0, 1, −1`?
7. Are the probabilities on screen 0.14, 0.18, 0.19, 0.25, 0.24 for cells 1, 3, 4, 5, 6, and 0.00 for the occupied cells?
8. Does E6S6 say that the high probability on cell 5 before training is chance?
9. Does E6S7 show greedy play picking cell 5 and sampling with roll 0.41 picking cell 4?
10. Is `grad_logits` on screen +0.14, +0.18, −0.81, +0.25, +0.24 for cells 1, 3, 4, 5, 6, and 0 for cells 0, 2, 7, 8?
11. Does E6S10 show the five shares −0.018, +0.023, +0.074, −0.029, +0.049, the sum 0.099, the slope 0.578, and `grad_z` 0.057?
12. Does E6S10 say that the shares use the old `W2` weights?
13. Does the video show the `ThreatBuilderStrategy` order as win, block, fork, build, then a random free cell, with random tie-breaks?
14. Are the training results exactly X: 1902 / 3220 / 878 and O: 3 / 747 / 5250?
15. Does the video say that the training counts include exploration and early games, and that the O network still has much to learn?
16. Does E6S14 show that the O network missed a win and a block in game 1, and missed a win at cell 5 two times in game 2?
17. Does the video avoid the claims "the network learned to block in general" and "the network generalizes to new boards"?
18. Does E6S13 say that, in this small test, the linear `PolicyLearner` lost fewer games than the network (399 against 878 as X, 2245 against 5250 as O), and does the video avoid any claim that the network gets better results?
19. Does E6S14 give the test-game blocking rates as 90% for the X network and 39% for the O network?
20. Does E6S11 say that the naive-trained learners block "almost no better than random", and not "never"?
21. Does the video avoid any claim that a policy without the baseline oscillates?
22. Is every code panel identical to the snippet in section 5.1?
23. Does the final scene return to the question "Who decides the next move?" and give ideas without promises and without a hook to a next video?
24. Does the narration use the exact names `NeuralPolicyLearner`, `PolicyLearner`, `ThreatBuilderStrategy`, `FirstAvailableStrategy`, and `MinimaxStrategy`, with no other names for them?
25. Does every scene stay between 20 and 90 seconds, and is the full episode 13 minutes or less?
