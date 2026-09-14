# Replacing the Table with a Neural Net: A Hand-Written Policy Network

## Who decides the next move?

Every article in this series has asked the same question — *who decides the next move?* — and answered it with a different brain in the same seat: a human, two hand-written strategies, a table of move-scores. This is the last brain: a **neural network** — but not an imported one. We build it by hand from Python lists and the `math` module, no numpy, no PyTorch, so you can see every number that changes and why.

And here is what keeps this article gentle: **nothing about the learning is new.** Article 3's recipe — pick a move, play the game, get a reward, nudge the policy toward the surprisingly good moves — works *unchanged*. The only new thing is the *container*: article 3 scored each cell with a single weighted sum; this article scores it with a small net that can *combine* several cells at once. Same nudge, more weights, a hidden layer in between — **share the recipe, change the substrate.**

## Why a net instead of a table

Article 3 ended on two limits, and each gets its own section here. This one is about the *memory*; the *teacher* gets its turn later.

The tabular learner had two memories: a **linear policy** (weights that turned a board into move-probabilities with a dot product) and a **per-board value table** (the critic). The table was fine only because tic-tac-toe is tiny. The linear policy could score a board it had never seen, but only *linearly*: one weighted sum per cell can add evidence up but cannot *combine* it — it could learn "my piece here is good" but not "this square matters because my two pieces sit on that line *and* the third is empty."

Article 3 reached for a phone book to name the table's limit, and the contrast is the point. A **table** keeps one stored page per exact board — one page per exact face — and that is all it is: ask it about a board with no page and it has no answer. A **net** keeps records the other way. Instead of a page per face, it keeps a shared set of *features* — eye color, height, hair — and describes every board by combining them. A board you have never seen still has its cells in the same arrangement, so the net can say something sensible about it by recombining those features, with no page of its own. That is why a net generalizes where a table cannot.

So what *is* a net, concretely? A stack of layers that pass a list of numbers from one to the next. Each layer does the same small thing with the numbers it receives: multiply each number by its own weight, add the products up, add one extra constant, then squash the result into a fixed range. That constant is the **bias** — a "starting position" added to the layer's sum before it squashes, so the layer can tilt its answer even when every input is zero.

The squashing is what makes the stack more than a pile of dot products. Because each layer's output is bent before the next layer multiplies it, the layers can no longer be flattened into one weighted sum, and the middle layer ends up holding *combined* readings — patterns like "two of mine on a line, the third still open" — that no single weighted sum can produce. Feed nine numbers in, nine come out, one per cell. That is the whole machine.

The net here is deliberately tiny: **nine inputs** (one per cell), **sixteen hidden numbers**, **nine outputs** (one score per cell) — a `9 → 16 → 9` net. Its constructor:

```python
    def __init__(
        self,
        hidden_size: int = 16,
        learning_rate: float = 0.1,
        value_rate: float = 0.9,
        rng: random.Random | None = None,
    ) -> None:
        self._learning_rate = learning_rate
        self._value_rate = value_rate
        self._rng = rng if rng is not None else random.Random()
        self._net = _Feedforward(_INPUT_SIZE, hidden_size, _INPUT_SIZE, self._rng)
        self._values: dict[Board, float] = {}
```

Two things to notice. First, `self._net` is a `_Feedforward` (nine in, sixteen hidden, nine out). Second — the continuity article 3 set up — `self._values` is **the same per-board value table the tabular learner had**. The critic, the baseline, and the reward are all reused; the net's single gain over the flat policy is **nonlinearity**.

The net itself is just four plain Python lists: two weight matrices and two bias lists.

```python
    def __init__(self, input_size: int, hidden_size: int, output_size: int, rng: random.Random) -> None:
        input_scale = 1.0 / math.sqrt(input_size)
        hidden_scale = 1.0 / math.sqrt(hidden_size)
        self._w1 = [[rng.uniform(-input_scale, input_scale) for _ in range(input_size)] for _ in range(hidden_size)]
        self._b1 = [0.0 for _ in range(hidden_size)]
        self._w2 = [[rng.uniform(-hidden_scale, hidden_scale) for _ in range(hidden_size)] for _ in range(output_size)]
        self._b2 = [0.0 for _ in range(output_size)]
```

`_w1` is sixteen rows of nine numbers (input → hidden); `_b1` is one bias per hidden number. `_w2` is nine rows of sixteen (hidden → output); `_b2`, one bias per output. Each weight starts small and random, so the net begins nearly neutral.

## How the net reads the board

This is the *same* player-relative reading from article 3, and it is what lets one net play either seat. The board is always described from the point of view of **the player about to move**: their own mark is **+1**, the opponent's is **−1**, an empty cell is **0**.

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

One deliberate difference from article 3's `_features`: the tabular learner tacked a fixed `1` on the end of the feature list, a small constant "starting position"; the net drops it, because its learned bias terms (`_b1` and `_b2`) now do that job — the constant has moved from the input into the layers, where it can be tuned.

The forward pass runs the board in and raw scores out. The first layer builds the sixteen hidden numbers: a weighted sum of the nine cell values plus a bias, squashed with `tanh` into the range −1 to +1. Those sixteen are the net's learned *features* — patterns like "a live threat along a line," not tied to any single cell. The second layer turns them back into nine raw scores, one per cell:

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

That `tanh` is the curved squashing function the plain-English picture promised. Because it is curved rather than straight, the two layers can no longer be collapsed into one weighted sum — the net can now say things a linear policy cannot, like "this cell is good *only when* those two cells are also in this arrangement." That is the nonlinearity, the whole point of the hidden layer.

The nine raw scores are the **logits** — a raw score, before it is turned into a probability, the net's "how tempting is this cell" number. Before they become probabilities, two things happen. **Masking** first: a cell that is already taken cannot be chosen, so its score is forced to a very negative number — like blotting the unavailable options on a multiple-choice question before you answer, so the net is *legal* by construction and can never "pick" a filled square. **Softmax** second: turn the raw scores into probabilities that add up to exactly 1.

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

`_MASK` is `−1e9`, effectively negative infinity: after the softmax, a masked cell's probability is so close to zero it might as well be zero. The softmax is article 3's: raise *e* to each raw score (subtracting the largest first, so the numbers don't blow up), then divide by the total — a raw gap of about 2 becomes roughly an 88–12 split. All three steps run in one small method:

```python
    def _probabilities(self, board: Board, player: Player) -> list[float]:
        logits = self._net.forward(_features(board, player))[1]
        _mask_occupied(logits, board)
        return _softmax(logits)
```

Read it as a pipeline: **forward → mask → softmax.** The output is a probability for every cell, the taken ones at (effectively) zero.

## How the net plays a move

With a probability for every cell in hand, playing a move is the same shape it was in article 3. A tiny helper lists the empty squares — the only cells that could ever be chosen:

```python
def _free_indices(board: Board) -> tuple[int, ...]:
    return tuple(index for index, cell in enumerate(board.cells) if cell.player is None)
```

Then `choose_position` turns the board into probabilities and plays one of two ways:

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

Two modes, exactly as article 3. With `explore` false the net plays **greedily** — `max(free, key=probabilities.__getitem__)` takes the free cell with the highest probability. With `explore` true (what training uses) it **samples**: roll a number between 0 and 1, walk the free cells adding up probabilities until the running total passes the roll, take that cell. We explore while training and play greedily when we show off.

Because `choose_position` and `learn` are the two `ReinforcementLearner` methods, this object drops into the same seat as article 2's strategies and article 3's table — and the same `Trainer` trains it unchanged.

## How the net learns: the same nudge, delivered to more weights

This is the heart of the article, and the only genuinely new mechanics in the series. When the game ends, the `Trainer` hands the net an `Experience` for each move it made: the board, the move, and the game's reward (+1 win / −1 loss / 0 draw). The net reacts to the **surprise**, not the raw score: it looks up this board's value from the reused critic, computes the **advantage** as `reward − value`, and nudges the value toward the reward. Better than expected is a positive advantage; worse, a negative one.

```python
    def learn(self, experience: Experience) -> None:
        value = self._values.get(experience.board, 0.0)
        advantage = experience.reward - value
        self._values[experience.board] = self._value_rate * value + (1.0 - self._value_rate) * experience.reward
        if advantage == 0.0:
            return
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

The first three lines are *identical* to the tabular learner: look up the value, `advantage = reward − value`, nudge the value toward the reward. If the outcome was exactly as expected, `advantage` is zero and the function returns — nothing surprising, nothing to learn.

Everything after the early return is the nudge, expressed as one vector. The net rebuilds the probabilities, then builds the gradient:

```python
        grad_logits = [-probability for probability in probabilities]
        grad_logits[experience.action.index] += 1.0
        for index in range(_INPUT_SIZE):
            grad_logits[index] *= advantage
```

Unpacked, that vector is `advantage · (one_hot(chosen) − π)`, where `π` is the probability list and `one_hot(chosen)` is a 1 at the move played and 0 elsewhere. `-probability` starts every entry negative — every move pushed *down* in proportion to how likely it was — and `+= 1.0` at the chosen index flips that entry to `1 − π`, large when the chosen move was an underdog. So the chosen move is nudged **up** by how *unlikely* it was (`1 − π[chosen]`), every other **free** move **down** by how likely it was (`π[i]`), and the occupied cells — (effectively) zero probability after masking — get (effectively) no nudge. Multiplying by `advantage` sets *amount* and *direction*: a better-than-expected game pushes the chosen move up and the free rivals down; a worse one flips it.

Compare that to article 3's line — `scale = learning_rate · advantage · (indicator − probabilities[position])`, computed once per free cell. The expression is the same, just assembled into a vector, with the learning rate applied where the weights move instead of in the nudge itself.

That function is **backpropagation**, the one new idea to hold onto. The nudge was defined at the *output*, but the output isn't produced directly by the inputs — it's produced by the sixteen hidden numbers, which are produced by the inputs. So to move the output the right way, the net must also move the hidden and input dials, working *backwards* to find each one's share of the error. Think of adjusting a recipe after you taste the dish: the output came out too salty, so you trace the salt backwards through the sauce, the broth, the base, trimming a little at each stage.

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

Read it in two passes. The first loop walks the **output** layer: for each output, nudge its row of weights (a weight moves more when its hidden number was active) while *accumulating* how much each hidden number should change — that accumulation is the chain rule at work, since a hidden unit affects an output only through its weight on that output. The second pass is the **input** layer: nudge each hidden row's input weights by that accumulated amount, times the input `x`. The bias lists get the same treatment.

Between the two passes is the single new line of math in this entire series:

```python
            grad_hidden[hidden_index] *= 1.0 - hidden[hidden_index] * hidden[hidden_index]
```

This is the **derivative of tanh**. The error has to pass *through* the squashing curve to reach the hidden layer, and `1 − h²` (where `h` is the squashed hidden value) tells you how steep the curve is there — flat where the hidden number is pinned near ±1, steep near zero. That is the whole of backpropagation in this net: carry the output nudge back through the weights, scaled by the local slope, and let every dial take its share. The same surprise, the same advantage, now delivered to a wall of dials at once.

## Why it trains against a threat-building opponent

Article 3's other limit is about the *teacher*: a learner is only as good as the opponents it trained against. Trained against the naive first-available player, the tabular learner learned to beat *that* player and nothing else — because that player never built a threat, the learner never had to learn to *block* a two-in-a-row. The net needs a better teacher. The obvious one, minimax, is the wrong one: unbeatable, but it explores the whole game tree and takes seconds per move in pure Python, so you can't run six thousand training games against it.

The answer is a third strategy, new to this article: `ThreatBuilderStrategy`. A fast heuristic that, in strict priority order, (1) **takes a winning move** if one exists, (2) **blocks** the opponent's winning move, (3) **makes a fork** — a move that creates two threats at once — or (4) **builds** a single threat, picking at random whenever several moves tie within a tier.

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
        forks = [position for position in free if self._threat_count(board.with_mark(position, me), me) >= 2]
        if forks:
            return self.rng.choice(forks)
        builds = [position for position in free if self._threat_count(board.with_mark(position, me), me) >= 1]
        if builds:
            return self.rng.choice(builds)
        return self.rng.choice(free)

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

The cascade just walks that priority in order — `wins`, then `blocks`, then `forks`, then `builds` — returning a random pick from the first non-empty list. The only non-obvious piece is `_threat_count`, which counts a player's two-in-a-rows with an open end: two such lines is a fork (undefendable in one reply), one is a build. If no tier qualifies, fall back to a random free cell.

That injected `rng` is what matters. It makes the strategy **stateful** — it holds a random generator, just like the learners — and it is what makes the teacher *diverse*. A fixed opponent plays the same way every game, so a learner can memorize its habits. Randomizing the tie-breaks means the threat-builder reaches for the same *kind* of move but not always the *same* move, so the net learns to block *in general* rather than dodge one pattern. That is article 3's lesson, applied: strong enough to force blocking, fast enough (a handful of line checks, no search) to run thousands of games, and varied enough that the skill transfers.

## The results

In `main.py` the two deep learners are trained the way the tabular ones were — six thousand episodes each, one in the X seat, one in the O seat — but against the threat-builder:

```python
    x_net = NeuralPolicyLearner(learning_rate=0.1, rng=random.Random(0))
    x_net_summary = Trainer().train(x_net, X, ThreatBuilderStrategy(random.Random(7)), EPISODES)
    o_net = NeuralPolicyLearner(learning_rate=0.1, rng=random.Random(1))
    o_net_summary = Trainer().train(o_net, O, ThreatBuilderStrategy(random.Random(8)), EPISODES)
    print(f"deep X vs threat-builder: won {x_net_summary.wins}, drew {x_net_summary.draws}, lost {x_net_summary.losses}")
    print(f"deep O vs threat-builder: won {o_net_summary.wins}, drew {o_net_summary.draws}, lost {o_net_summary.losses}")
```

Both run 6000 episodes (`EPISODES = 6000`). The printed summaries read:

```text
deep X vs threat-builder: won 1902, drew 3220, lost 878
deep O vs threat-builder: won 3, drew 747, lost 5250
```

Read them honestly, seat by seat. The **first-player** net is the success story: against a strong, diverse opponent that actively builds and forks, it wins nearly a third (1902), draws more than half (3220), and loses only 878 — it has learned both to win and to defend, and the high draw rate is the mark of a player that stops the other side's threats.

The **second-player** net is the honest one. It mostly loses (5250), with 747 draws and 3 wins. Two things explain it. The first is the seat: tic-tac-toe is a draw under perfect play, and going *second* against a strong attacker is hard to turn into a win — the second player has no initiative, only the chance to hold. The second is that the net is also genuinely under-converged: a well-trained second player should draw most games against a non-perfect first player, and 5250 losses out of 6000 says this one has not yet learned everything it could. The 747 draws are the defensible part — a net that never blocked would lose almost all of them — so the draw count is the skill, and the loss count is the seat *and* the unfinished learning.

Then the demo shows off, greedily — the `explore=False` flag from earlier:

```python
    run_match(engine, FirstAvailableStrategy(), o_net, explore=False)
    run_match(engine, x_net, o_net, explore=False)
```

The first match pits the trained O-net against the naive first-available player; it ends `GameStatus.O_WON` — the net, playing greedily, beats the parking-lot player outright. (Watch it: when X lines up a two-in-a-row, the net steps in on the open end — and that very move completes the net's own line.) The second pits the two trained nets against each other, X-net versus O-net; it ends `GameStatus.DRAW`. That draw is the payoff of the blocking story: the net trained as the *attacker* meets the net trained as the *defender*, the defender holds the threats, and neither can force a win. Two hand-built nets, trained only by playing thousands of games, reach a draw — no human wrote a single rule about what a move should be. All of it is reproducible with `uv run main.py`.

## Four brains, one game

Every article asked *who decides the next move?* and answered with a different brain in the same seat:

1. **A human** driving `main.py`, deciding every move by hand.
2. **Two hand-written strategies** — a nearly-dumb first-free-cell player and an unbeatable minimax search.
3. **A lookup-table policy learner** the program updates from its own experience, nudge by nudge.
4. **A small neural network** we wrote from scratch, generalizing to boards it has never seen.

The picture is one driver's seat, four drivers, the same car. The **seat** is the seam — the `Strategy` protocol, and the slightly bigger `ReinforcementLearner` hat a learner wears over it. The **car** is the domain model from article 1: the value objects that check themselves on creation, the `Game` aggregate that is the only place the rules live, the one-way flow of command → engine → aggregate → transition → bus. Because a learner is also a strategy, the net slides into the very seat the minimax did, and the `Trainer` that taught the table teaches the net without a line changed. Swap the driver and the car is untouched — the interface never moves; only the thing behind it does.

That contrast is the point of the series. The same game, played by a person, by hand-coded rules, by a table, and by a neural net, shows that reinforcement learning is a *range*: from a policy that fits on a sheet of paper to a network you can write out by hand with nothing but lists and `math`. And because we built the net by hand, you now know what a framework would hide — what "training" actually touches (a vector of nudges, a backward pass through a squashing curve, a handful of weight updates) and the recipe (pick a move, get a reward, react to the surprise).

From here the road is clear. Grow the board to 4×4 and feel the value table break and the net earn its keep; log the critic's estimates over episodes to watch the "value" converge; swap the opponent or the seed and watch the summaries shift. The substrate is yours to change — a table, a net, a bigger net, a different teacher. The question, and the seat, stay where article 1 left them.
