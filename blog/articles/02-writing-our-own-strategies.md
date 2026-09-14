# Two Ways to Play: A Dumb Strategy and an Optimal Search

## Who decides the next move?

Last article we built the floor: a domain model that knows whose turn it is, which cells are free, and when the game is over — and it does all of that without ever picking a single cell. It ended on an empty seat. That `pick(...)` line in the match loop, handing the game to *something*, is the whole question of this series: **who decides the next move?**

This article fills that seat twice, with two "brains" written by hand. The first plays almost blindly — it grabs the first free cell and never thinks. The second is mathematically unbeatable — it imagines the entire rest of the game before every move. Both plug into exactly the same one-method slot, and the gap between them is the gap between losing and never losing. Along the way we'll meet the tension that runs through the rest of the series: *you can buy strength, but it costs time.*

## The seam: a strategy is one function

Here is the entire contract a brain has to satisfy:

```python
class Strategy(Protocol):
    def choose_position(self, game: Game) -> Position: ...
```

That's it. One method: look at the game, hand back a `Position`. Two things about this contract do all the work.

First, it's a *structural* interface. A `Protocol` (from Python's `typing` module) means: any object that has a `choose_position` method taking a `Game` and returning a `Position` **is** a strategy — no inheritance, no registration, no base class to inherit from. The analogy is a socket that fits any plug with the right two prongs; the socket doesn't care what the plug is made of, only what it exposes.

Second, notice what the method *doesn't* take: no player. A strategy doesn't play "for X" or "for O" — it plays for whoever `game.current_player` is at the moment it's asked. It's a driver's seat that fits any driver: the seat doesn't care who sits in it, it just hands the controls to whoever's turn it is. That's why one `MinimaxStrategy` object can sit in the X seat in one match and the O seat in the next — the same object, a different turn.

This is the seam the rest of the series keeps reusing. `strategies.py` holds several concrete classes that fit this one slot: the two we'll meet now, and a third — `ThreatBuilderStrategy`, a strong and varied opponent we save for article 4.

## The dumb baseline: first available cell

The simplest possible brain is this:

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

Read it as English: walk the nine cells in reading order, top-left to bottom-right, collect the empty ones, and return the first. That's the whole strategy.

Three properties are worth naming. It's **tiny** — the whole logic is a list comprehension and a return. It's **deterministic** — the same board always produces the same move, every time, no coin flips, no mood swings. And it's **completely unstrategic**: it never looks at the board's shape, never notices a threat, never plays for the center. The analogy is grabbing the first empty parking spot without ever glancing at the view, the exit, or the dumpster you're about to be parked next to. Fast. Zero thinking.

Notice what the code *doesn't* do: it re-implements no rules. It asks the model exactly one question — `board.is_occupied(...)` — and does the rest with plain Python. The domain model from article 1 is doing the work, as designed; the brain just asks it.

A strategy this bad sounds useless, but it isn't. It's the **baseline** — the reference point that makes "smart" measurable. A strategy that beats the first-available player is playing *something*; one that doesn't is playing nothing. It's also a sparring partner, and in article 3 it becomes a learner's training opponent.

## Show it loses

The demo puts it in the ring in `main.py`, right after the engine is wired up:

```python
    run_match(engine, FirstAvailableStrategy(), MinimaxStrategy())
    run_match(engine, MinimaxStrategy(), MinimaxStrategy())
```

`run_match` is the same match loop article 1 traced end to end — a header naming both brains, a board after every move, and the final status when the game ends. You saw this exact match in the last article; here is the ending again, with the event names the bus prints (the trailing whitespace `render` leaves at each line's end is removed):

X dutifully takes the first free cell in reading order every time — the top-left corner, then the top-middle, then the middle-left — no matter what. O, meanwhile, threads the game and completes a diagonal on its third move:

```text
MarkPlaced
GameWon
 X | X | O
---+---+---
 X | O |
---+---+---
 O |   |

GameStatus.O_WON
```

The parking-lot player meets a grandmaster and gets swept off the board. Reproducible with `uv run main.py`.

That match is the whole point of a baseline in one screen: a strategy that's trivial to write and trivial to beat. So the obvious next question is — what does a strategy that *can't* be beaten look like?

## The optimal player: minimax, in plain English

Meet `MinimaxStrategy`. Before the code, the idea, in plain English:

Imagine you could see the whole rest of the game before you move. For every cell you could play, imagine the opponent's reply, then your reply to that, and so on until the game ends. Each finished game has a score from your point of view: you won, **+10**; you lost, **−10**; it was a draw, **0**. Now work backwards. When it's *your* turn in an imagined future, you'd pick the branch with the best score. When it's *their* turn, they're trying to beat you, so assume they pick the branch that's worst for you. Keep alternating — my turn, best case; their turn, worst case — all the way back to the present. The move to play is the one whose branch is still good *even in the worst case*: best for me, given that the opponent also plays optimally.

That's the whole algorithm. The analogy is a chess player mentally simulating "if I play here, they play there, I play here, …" all the way to the end, then choosing the line where they do best *assuming the opponent plays their best*. It's a tree of "what if" branches: at your turns you keep the best branch, at their turns you assume they keep the branch that's worst for you.

Here is `choose_position` — the part that actually picks a move:

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

Same shape as the dumb strategy — walk the free cells — with one big difference: for each candidate it tentatively plays it (`board.with_mark` builds the *new* board, the no-mutation rule doing its job) and asks `_score` "how good is this board, for me?" Then it keeps the highest score. Two things to notice. `me = game.current_player`: the strategy scores from the perspective of whoever is to move, which is what makes it player-agnostic. And the call passes `me.opponent` as the player to move: after you place a mark, it's the opponent's turn in that imagined future, so the recursion starts with *them* to move.

The looking-ahead lives in `_score`, a method of the same class:

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

It's **recursion** — a function that calls itself on a smaller version of the problem — and it reads exactly like the plain-English version. Three base cases, in order: if `me` has a winning line on this board, the game is over and it's worth `10`; if the opponent has one, it's worth `−10`; if the board is full with no line, it's a draw worth `0`. Otherwise the game continues: play each free cell for whoever `player_to_move` is, score each resulting board, and — the line that is the entire algorithm — return `max(scores)` if it's *my* turn to move, `min(scores)` if it's *theirs*.

Two details keep it honest. `me` never changes: no matter how deep the recursion goes, every score is still from the original player's point of view. What alternates is `player_to_move` — each recursive call hands the turn to the other side (`player_to_move.opponent`), so the max/min flips at every level. And the base cases are never home-brewed rules: `winning_line` and `is_full` are the model's own queries. Minimax never re-implements tic-tac-toe; it just asks the model, over and over, "if we get here, who won?" The brain from article 1's foundation is doing the real work.

## Show it draws itself, and pay for it

Now the second match from the demo:

```python
    run_match(engine, MinimaxStrategy(), MinimaxStrategy())
```

The header reads `MinimaxStrategy (X) vs MinimaxStrategy (O)`, a board comes out after every move, and the ending looks like this (trailing whitespace removed):

```text
MarkPlaced
GameDrawn
 X | X | O
---+---+---
 O | O | X
---+---+---
 X | O | X

GameStatus.DRAW
```

Unbeatable — as it must be. Two perfect players can't beat each other, so optimal play in tic-tac-toe is a draw, and the code delivers exactly that.

But watch what it costs. Minimax doesn't *guess* good moves; it **checks every game that could follow**. Tic-tac-toe's tree of possible games is finite: count every legal game to its end and you get exactly 255,168 — every legal sequence of moves from an empty board. The nested `for index in range(SIZE * SIZE)` loops in `choose_position` and `_score` walk that whole tree, one branch at a time, building a brand-new `Board` at every node (the no-mutation rule is lovely for correctness and expensive for speed).

The cost is **front-loaded**. The most expensive move is the very first one: from an empty board, the whole tree of 255,168 possible games is still ahead of it, and on a given machine that first move alone takes a couple of minutes. But every later move faces a smaller tree, so each one is faster than the last — the second move still takes a dozen seconds or so, the third about a second, and the rest of the game collapses to fractions of a second, then mere milliseconds. The expensive part of minimax is concentrated in the opening.

The `FirstAvailableStrategy` move, by contrast, takes microseconds — a tiny fraction of a millisecond — because it never looks ahead at all.

So here is the tradeoff, and it's the centerpiece of this article:

- **First-available**: instant, deterministic, two lines of code — and it loses to a grandmaster.
- **Minimax**: unbeatable, provably so — and it pays for that strength by simulating every possible rest of the game, with the bill coming due hardest on the first few moves.

You can buy strength, but it costs time. That's the central tension the rest of the series exists to escape: is there a way to get play that's *close to* optimal without brute-forcing the entire tree on the expensive opening moves?

## What if it learned instead?

Notice what the two brains have in common: both were **written by a human**. Before either one ever played a game, we had already decided, in advance, exactly how each one behaves — one by a fixed rule, the other by a fixed search. The analogy is the difference between a chef following a written recipe and a cook who gets better at seasoning simply by cooking a lot and tasting the results: the recipe never changes, whatever the food turns out tasting like.

What if we didn't want to decide that up front? What if the program figured out which moves are good on its own — by playing a lot of games, keeping score, and adjusting? Instead of hand-coding ever-smarter logic, the program *learns* to play from experience. The next article builds the simplest possible version of that idea: a policy reinforcement learner that keeps a plain table of move-preferences and updates it from nothing but the results of the games it has already played — plugging into the very same `choose_position` slot these two strategies use.
