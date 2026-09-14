# Video Series: Who Decides the Next Move?

This folder holds the plan for a series of six explainer videos. The videos follow the blog articles in `blog/articles/`. Each video adds one new part to the project.

Read `WORKFLOW.md` for the production procedure. This file gives the series structure, the shared visual rules, and the episode file format.

## The series question

Each video answers one question: **who decides the next move?** Each video gives a different answer.

| # | File | Title | New idea | Source article |
|---|------|-------|----------|----------------|
| 1 | `01-modeling-the-game.md` | The Parts of the Game | Value objects, the `Board` invariants, the `Game` aggregate, immutability | `01-modeling-the-game.md` (first half) |
| 2 | `02-how-a-move-happens.md` | How a Move Happens | Commands, domain events, the `GameEngine`, the event bus, the one-way flow | `01-modeling-the-game.md` (second half) |
| 3 | `03-the-naive-opponent.md` | The Naive Opponent | The `Strategy` protocol, `FirstAvailableStrategy`, why it loses | `02-writing-our-own-strategies.md` (first half) |
| 4 | `04-the-perfect-player.md` | The Perfect Player | Minimax search, the game tree, the cost of a full search | `02-writing-our-own-strategies.md` (second half) |
| 5 | `05-learning-from-rewards.md` | Learning from Rewards | Reinforcement learning, a linear softmax policy, policy gradient with a value baseline | `03-policy-learner.md` |
| 6 | `06-a-neural-network-policy.md` | A Neural Network Policy | A feedforward network with one hidden layer, backpropagation, a threat-building training opponent | `04-deep-learner.md` |

## Correct names for the learners

Use these names in all scripts. Do not use other names.

- **Video 5.** The `PolicyLearner` is a **linear softmax policy**. It keeps a table of weights: 9 moves × 10 features (9 cells plus 1 bias). It is not a lookup table of scores for each board, and it is not a feedforward network. It learns by **policy gradient** (the REINFORCE rule) with a **per-board value baseline**.
- **Video 6.** The `NeuralPolicyLearner` is a **feedforward neural network**: 9 inputs, 16 hidden units with `tanh`, 9 outputs, then softmax. It uses the same policy-gradient rule as video 5. **Backpropagation** is not a separate learning rule. It is the method that sends the policy gradient back through the hidden layer.
- **The baseline.** The code and `AGENTS.md` call the method "actor-critic". The more exact name is **REINFORCE with a learned baseline**. The value table moves toward the final game reward. It does not use the value of the next board (no bootstrapping). A script can say "a simple form of actor-critic", but it must name REINFORCE with a baseline first.
- **The articles.** The blog uses the word "tabular" for the video 5 learner. The weights are in a table, but each move score is a weighted sum of board features. Say "a table of weights", not "a table of move scores for each board".

## Audience

The audience knows basic Python. The audience does not know domain-driven design, search algorithms, or machine learning. Each video must stand alone. Each video starts with a recap of 20 seconds or less.

## Target length

Each video is 8 to 12 minutes. A scene is 20 to 90 seconds.

## Language rules

All prose, including narration, follows Simplified Technical English (ASD-STE100):

- Use short sentences. Procedural sentences have a maximum of 20 words. Descriptive sentences have a maximum of 25 words.
- Use the active voice.
- Use one word for one meaning. Do not use synonyms for a technical name.
- Use the imperative in procedures ("Render the scene.").
- Write code names exactly as they are in the source, in backticks in the files.

## Shared visual language

All videos use the same visual rules. The rules make the series look like one product.

### Canvas

- 1920 × 1080, 30 fps for the final render.
- Background: `#1E1E2E`.
- Main text: `#E6E6E6`. Secondary text: `#9A9AB0`.
- Font for labels: the Manim default. Font for code: the `Code` mobject default (monospace).

### Colors with a fixed meaning

| Meaning | Hex | Use |
|---------|-----|-----|
| Player X | `#4C9BE8` (blue) | X marks, X labels |
| Player O | `#F2A541` (orange) | O marks, O labels |
| Invariant or rule | `#C678DD` (purple) | Rule boxes, validation checks |
| Command | `#61AFEF` (light blue) | Command cards |
| Domain event | `#98C379` (green) | Event cards |
| Error or illegal state | `#E06C75` (red) | Rejected moves, broken invariants |
| Reward or positive value | `#98C379` (green) | +1, high probabilities |
| Negative value | `#E06C75` (red) | −1, low values |
| Neutral value | `#9A9AB0` (grey) | 0, draws |

Do not use a color with a fixed meaning for a different purpose.

### Fixed objects

- **The board.** A 3 × 3 grid of squares, side 1.2 units, stroke `#E6E6E6`, stroke width 4. The board shows cell indices 0 to 8 in small grey text when the script asks for them. Index 0 is top left. Index 8 is bottom right.
- **Marks.** X is two crossed lines. O is a circle. Each mark fills 70% of its cell.
- **Code panel.** Use `Code(code_string=..., language="python", background="window", add_line_numbers=False)`. Put the code panel on the right half of the screen. Put the board or diagram on the left half.
- **Cards.** A command or event is a rounded rectangle with the class name in bold and the fields below it.
- **Probability heat map.** When a script shows move probabilities, color each free cell with an opacity equal to the probability. Write the probability as a number with two decimal places in the cell.

## Episode file format

Each episode file uses these sections in this order. A production LLM reads one episode file and `WORKFLOW.md` only. Thus each episode file must contain all the facts that the production LLM needs.

1. **Header.** Title, number, target length, source files, source article sections.
2. **Goal.** One paragraph: what the viewer can do or explain after the video.
3. **Recap from the last video.** Maximum 20 seconds. Video 1 has a series introduction here, with a maximum of 40 seconds.
4. **Terms.** Each new technical name with a one-sentence definition.
5. **Source facts.** The exact code snippets for the video, copied from `src/tictactoe/`, with the file name. Also the facts and numbers that the narration uses.
6. **Scenes.** For each scene:
   - Scene ID (`E<episode>S<scene>`, for example `E3S2`) and a Manim class name (for example `E3S2StrategySeam`).
   - Target duration.
   - Narration: the exact text, split into short blocks. Put `<bookmark mark='name'/>` tags where an animation must start.
   - Visuals: the objects on screen, with position (left, right, center, top) and color.
   - Animation steps: a numbered list. Each step names the bookmark that starts it.
   - Accuracy notes: facts that the production LLM must not change.
7. **Closing and hook.** The last scene names the problem that the next video solves.
8. **Checks.** A list of yes/no questions for the review step in `WORKFLOW.md`.
