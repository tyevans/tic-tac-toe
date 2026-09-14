# Learning to Play: A Table of Move-Scores the Program Builds Itself

## Who decides the next move?

Last article we filled the empty seat with two brains written by hand: a nearly-blind first-free-cell player and an unbeatable minimax search. Both answered the series' question, **who decides the next move?**, the same way — a human wrote the decision logic before a single game was played. This time the program decides, and *changes how it decides* as it plays.

That is the family of techniques called **reinforcement learning**: learning by **trial and error with rewards**. Think of a dog learning a trick. It tries a wobble, gets no treat; tries another, gets a treat; and the wobble that earns treats happens more often. The skill *emerges* from near-misses and the feedback that follows — nobody writes the trick down first.

Three words do all the work in this article:

- A **state** is a particular board position — one specific arrangement of Xs, Os, and empty cells.
- A **policy** is the program's current *habit*: given a board, which moves it is disposed to make — just a word for a set of preferences.
- A **reward** is how the game turned out, from the learner's point of view — a win is good, a loss is bad, a draw is neutral — fed back to the moves that led there. Good habits strengthen; bad habits weaken.

That is the whole theory. The rest is plumbing: a small, readable implementation of exactly that loop.

## The new seam: a learner is a strategy that remembers

Article 2 established the slot a brain plugs into: one method, `choose_position` — look at the game, hand back a `Position`. The learner plugs into a slightly bigger slot:

```python
class ReinforcementLearner(Protocol):
    def choose_position(self, game: Game) -> Position: ...

    def learn(self, experience: Experience) -> None: ...
```

A `Protocol`, in the same sense as article 2's `Strategy`: any object exposing these methods *is* a reinforcement learner — no inheritance, no registration.

Two methods instead of one. The first is *identical* to the strategy's — same name, same signature — and that is the hinge: **a learner is also a strategy**, plugging into the very same seat as the hand-coded brains, because the move is still one `choose_position` call. The second, `learn`, is new: after the game ends, the caller hands the learner an `Experience` — one of its moves plus how the game turned out — and the learner adjusts its habits.

`Experience` is a frozen record in the same family as article 1's value objects — it can never change once made — though, unlike `Position`, it does no self-checking:

```python
@dataclass(frozen=True, slots=True)
class Experience:
    board: Board
    player: Player
    action: Position
    reward: float
```

Four fields, reading as a sentence: *in this board, this player made this move, and the game was worth this much.* A fixed strategy is a thermostat you set once and never touch; the learner is one that *adjusts itself* on what has been happening.

## The policy: a table of move-scores

Now the learner itself, `PolicyLearner`, and the "table" of the title. For any board, the learner assigns a **score to each free cell** — how tempting that cell looks *in that situation* — and picks among the free cells in proportion to those scores.

First the learner has to *read* the board, and it reads it in a way worth pausing on: **player-relative**. The same object can sit in the X seat or the O seat, so the board is always described from the perspective of *the player about to move*:

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

Walk the nine cells in reading order: the mover's own mark scores **+1**, the opponent's **−1**, an empty cell **0** — and a fixed `1` is tacked on the end, a small starting position so every cell has a baseline to tilt rather than a pure reaction to the board. The same board reads differently depending on who is to move: to X, X's pieces are +1; to O, they are −1. The learner never asks "am I X or O?" — it thinks "my pieces versus theirs," which is what lets one learner serve either seat.

The scores themselves live in a set of weights, created when the learner is born:

```python
class PolicyLearner:
    def __init__(self, learning_rate: float = 0.1, value_rate: float = 0.9, rng: random.Random | None = None) -> None:
        self._learning_rate = learning_rate
        self._value_rate = value_rate
        self._values: dict[Board, float] = {}
        self._rng = rng if rng is not None else random.Random()
        self._weights = [[0.0 for _ in range(_FEATURES)] for _ in range(_ACTIONS)]
```

`self._weights` is ten numbers per cell — nine cells (the nine *actions*), ten features each (the nine cell values plus the constant). Every number starts at zero: a new learner has no preferences, every free cell equally tempting. (`self._values`, the *second* memory, gets its own section.) `learning_rate` sets how boldly the learner changes; `rng` is the injected coin-flipper.

To turn a board into move-probabilities, the learner takes each free cell's row of weights and combines it with the board's features — a dot product, "multiply the matching pairs and add":

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

Collect the free cells, encode the board, and score each free cell with a dot product — one raw number per cell, a **logit** — where the weights decide how much each reading is worth. The raw scores become probabilities summing to exactly 1 via **softmax**: raise *e* to each raw score (subtracting the largest first, so the numbers don't blow up), then divide by the total. A scorecard with a scribbled score per square becomes percentages adding to 100, gaps preserved — a raw gap of about 2 becomes roughly an 88–12 split.

That is the entire policy — the "table of move-scores" of the title, though not a stored table: a set of weights that *computes* a score for each free cell of any board, seen before or not. Article 4 swaps it for a neural net — same job, different container.

## How it plays a move (and why it sometimes explores)

With the policy in hand, playing a move is one function:

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

Two modes. When `explore` is false the learner plays **greedily**: take the most likely cell — the `max` over the free cells — no noise. When `explore` is true (the default, and what training uses) it **samples**: roll a number between 0 and 1, walk down the free cells adding probabilities until the running total passes the roll, take that cell.

The analogy is a slot-machine player: mostly you pull your best lever, but now and then you try a different one, because a barely-tried lever might pay out *more*. Exploring is how the learner discovers it was wrong; being greedy is how it cashes in — without it, a slightly wrong habit could never be corrected.

This duality is what the demo relies on, and article 4 reuses it: **we explore while training, and we play greedily when we show off the result.**

## The training loop: play games, stamp the moves

The missing piece is the loop that plays games, collects rewards, and hands out lessons — the `Trainer`:

```python
class Trainer:
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

For each episode, start a fresh game and play it to the end. On each turn, if it is the learner's seat the learner picks a move — *recorded* in `moves` with the board it was played from — otherwise the opponent strategy from article 2 picks. The game advances through the same aggregate article 1 built — `game.place_mark(action).game` — but with no front desk: no engine, no bus, no event stream. Training doesn't need events; it needs games.

When the game ends, the lessons go out. Every move the learner made becomes an `Experience` — the board it was played from, the seat, the move, the reward — and `learn` is called on each. Notice: **every one of the learner's moves gets the same reward, the outcome of the whole game.** The reward comes from a small helper, always from the learner's point of view:

```python
def _reward(player: Player, status: GameStatus) -> float:
    if status is GameStatus.DRAW:
        return 0.0
    winner = X if status is GameStatus.X_WON else O
    return 1.0 if player == winner else -1.0
```

Win: +1. Loss: −1. Draw: 0.

The analogy is a coach who, after each game, stamps *every* call "good" or "bad" by how the game ended — the same stamp on every call, because the coach judges the whole outing, not each play. (The next two sections fix exactly that roughness.) The loop also tallies episodes into a `TrainingSummary(wins, draws, losses)` — and this same `Trainer.train` drives the neural learner in article 4 unchanged. One harness, two kinds of brain.

## The nudge: how a move's score changes

The lesson itself — what `learn` does with one `Experience` — is the shortest important function in the project:

```python
    def learn(self, experience: Experience) -> None:
        value = self._values.get(experience.board, 0.0)
        advantage = experience.reward - value
        self._values[experience.board] = self._value_rate * value + (1.0 - self._value_rate) * experience.reward
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

The top three lines belong to the next section (the value baseline). For now, read `advantage` as "how surprised the outcome was." The rest is the nudge.

The learner recomputes the probabilities for the experience's board with its current weights, and walks every free cell. For each it builds an **indicator**: 1 if this is the move played, 0 otherwise. Then the key expression: `scale = self._learning_rate * advantage * (indicator - probabilities[position])`.

For the **played** cell, `indicator − probability` is 1 minus its probability — positive, largest when the cell was an underdog. For every **unplayed** cell it is 0 minus its probability — negative, biggest for the most probable unplayed cells. One expression does two jobs: the played cell is pushed *up*, every other cell *down*, sized by how surprising the outcome was (`advantage`) and how bold a step (`learning_rate`). Better than expected, `advantage` is positive and the signs stand as written; worse, it flips — the played cell down, the others up.

The push itself, `weight[feature_index] += scale * features[feature_index]`, moves the cell's whole row of weights a little toward — or away from — the features of *this* board: "in boards like *this*, this cell turned out better (or worse) than expected."

The analogy is a row of dials, one per cell: better than expected, turn its dial up a little and the others down; worse, reverse. Small turns, repeated thousands of times, add up to a habit — and the balancing act is built in, because the alternatives are suppressed in proportion to how likely each was.

## The value baseline: reacting to the surprise, not the score

Now the top three lines of `learn`, the part that keeps the whole thing from wobbling:

```python
        value = self._values.get(experience.board, 0.0)
        advantage = experience.reward - value
        self._values[experience.board] = self._value_rate * value + (1.0 - self._value_rate) * experience.reward
```

Start with the problem. A game has four or five moves by the learner, with many causes — its own moves, the opponent's, who went first. Score each move by the raw outcome alone and every move in a win gets +1, every move in a loss gets −1 — but not every move in a win was good, and not every move in a loss was bad. A raw outcome is a **noisy** teacher: it credits and blames indiscriminately.

The fix is to compare the outcome to an *expectation*. The learner keeps a second memory — the one that really is a table — `self._values`: one stored number per board it has seen, an estimate of "how good is this position on average, from my side?" between −1 and +1. Line one looks up this board's value (0 if new); line two is the comparison: **advantage = reward − value** — how much the outcome beat or missed the expectation. A win from a position already expected to win has advantage near zero: nothing surprising, so the moves get almost no credit or blame. A win from a position expected to lose is a big positive surprise: a big nudge. That is the whole trick — react to the *surprise*, not the raw score.

Line three is how the expectation improves: the value moves a little toward the observed reward. With the default `value_rate` of 0.9, the new value is 90% of the old estimate plus 10% of the new evidence.

There is a name for this: **actor-critic**. The **actor** is the policy — the weights that pick moves. The **critic** is the value table — the running estimate of how good each position is. The actor only changes a lot when the result beat or missed the critic's expectation. The analogy: judging a student not by the raw score but by how much *better or worse* they did than their average — a 90 when they average 90 is nothing; a 90 when they average 60 is a big deal.

So there are the two memories, side by side: the weights that decide *which move to try*, and the table that decides *how hard to react* when the game ends. The second one is not optional — without a baseline, learning breaks. A raw reward stamps every move in a game the same, so the learner alternately strengthens and weakens the same moves as different games wash over them; it oscillates, and can even *unlearn*. The baseline keeps updates small when they should be small and large when they should be large — what lets thousands of episodes converge into a stable habit instead of a tremor. (The same `_values` map and advantage are reused verbatim by the neural learner in article 4.)

## What it learns — and where it stops

Time for the demo. In `main.py`, the tabular learners are trained against the naive opponent from article 2, the first-available player:

```python
    x_learner = PolicyLearner(learning_rate=0.1, rng=random.Random(0))
    x_summary = Trainer().train(x_learner, X, FirstAvailableStrategy(), EPISODES)
    o_learner = PolicyLearner(learning_rate=0.1, rng=random.Random(1))
    o_summary = Trainer().train(o_learner, O, FirstAvailableStrategy(), EPISODES)
    print(f"tabular X vs naive: won {x_summary.wins}, drew {x_summary.draws}, lost {x_summary.losses}")
    print(f"tabular O vs naive: won {o_summary.wins}, drew {o_summary.draws}, lost {o_summary.losses}")
```

`EPISODES` is 6000, and each learner plays the naive opponent for every episode. The printed summaries read:

```text
tabular X vs naive: won 5968, drew 7, lost 25
tabular O vs naive: won 5960, drew 11, lost 29
```

Out of six thousand games each, each learner wins on the order of five thousand nine hundred and sixty. From all-zero weights, with nobody writing a single rule, the program has taught itself to almost never lose to the parking-lot player — reproducible with `uv run main.py`.

Then the demo shows off, in greedy mode — the `explore=False` flag from the "how it plays a move" section:

```python
    run_match(engine, FirstAvailableStrategy(), o_learner, explore=False)
    run_match(engine, x_learner, o_learner, explore=False)
```

The trained O-learner against the naive player, and the two trained learners against each other.

And now the honest part: **the learner learned to beat one specific opponent.** The first-available player is completely predictable — it always grabs the lowest-numbered free square, top-left first — so the learner never faced a threat, because its opponent never built one. It never had to learn to *block* a two-in-a-row; it learned the handful of habits that beat a player that walks into the first empty spot. In the reactive seat — the one that must *block* — those habits run out.

The analogy is a boxer who only spars with a beginner: excellent at beating *that* beginner, but never practiced defending, because they never got hit — in a real fight they get caught flat-footed, their training never containing the thing they now need.

The lesson is the one this series keeps circling: **a learner is only as good as the opponents it trained against.** Article 2 showed hand-coding doesn't scale — you can buy strength with search, but pay in time. This article shows the mirror image: learning doesn't scale either if the teacher is weak — you can buy strength with experience, but only the kind the experience contained. That limit is about the *teacher*; the next section is about the *memory*.

## A table can't grow with the game

The second limit is about the memory, not the teacher. Step back and the learner has exactly **two** memories, and they behave very differently.

The first is the policy's weights — the ninety numbers (ten per cell) that turn a board into move-probabilities with a dot product. They already generalize: the same ninety numbers score a board the learner has never seen.

The second is the critic's value table, from the baseline section:

```python
        self._values: dict[Board, float] = {}
```

A dictionary keyed by the *entire* `Board` — one stored number per exact position. This is the true lookup table, and it is tolerable only because tic-tac-toe is tiny: each of the nine cells is X, O, or empty, so at most 3⁹ = 19,683 distinct boards — fewer in practice, some arrangements being illegal mid-game. A table with under twenty thousand rows fits in memory and in your head.

The policy has its own limit, subtler than the table's. It scores *any* board, but only **linearly**: one weighted sum per cell, which can add up evidence but can't *combine* it. It can learn "my piece here is good" or "their piece there is bad," but not that "this square matters *because* my two pieces sit on that line *and* the third is empty" — a judgment that depends on several cells *together*, which no single weighted sum can express.

The analogy is a phone book: one page per exact person works in a small town, but for a whole country you need a way to say "this stranger *looks like* someone I know" — recognize patterns, not just recall entries. The moment the game gets bigger, the number of positions explodes past anything a per-board table can store, and the deciding patterns stop fitting in a single weighted sum.

So here is the question the next article answers — the same question as this one's, asked of a bigger game: **who decides the next move?**

And now the answer has to *generalize*. The linear policy scores a board with one weighted sum per cell and can't combine cells, so the next article replaces it with a small neural network — a model that has never seen a particular board but can still guess a reasonable move by recognizing patterns in it. The net is built entirely by hand, no libraries, just Python lists and the `math` module. And it keeps the thing that made all of this work: the same per-board value table, and the same learning recipe. Same learner, same critic, same reward — only the linear policy is swapped for a nonlinear net. The next article shows that swap, and trains it against an opponent that actively builds threats, so the skill it picks up is the kind a real opponent demands.
