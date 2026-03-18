# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

You asked an AI to build a simple "Number Guessing Game" using Streamlit.
It wrote the code, ran away, and now the game is unplayable. 

- You can't win.
- The hints lie to you.
- The secret number seems to have commitment issues.

## 🛠️ Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run the broken app: `python -m streamlit run app.py`

## 🕵️‍♂️ Your Mission

1. **Play the game.** Open the "Developer Debug Info" tab in the app to see the secret number. Try to win.
2. **Find the State Bug.** Why does the secret number change every time you click "Submit"? Ask ChatGPT: *"How do I keep a variable from resetting in Streamlit when I click a button?"*
3. **Fix the Logic.** The hints ("Higher/Lower") are wrong. Fix them.
4. **Refactor & Test.** - Move the logic into `logic_utils.py`.
   - Run `pytest` in your terminal.
   - Keep fixing until all tests pass!

## 📝 Document Your Experience

### What does the game do?
Game Glitch Investigator is a number-guessing game built with Streamlit. The player selects a difficulty level (Easy, Normal, or Hard), then tries to guess a randomly chosen secret number within a limited number of attempts. After each guess the game gives a hint — Too High or Too Low — to guide the next guess. Points are awarded for winning and deducted for wrong guesses; the fewer attempts it takes, the higher the score.

### Bugs found
| # | Bug | Where |
|---|-----|-------|
| 1 | Float inputs (e.g. `3.7`) were silently converted to `3` instead of rejected | `parse_guess` |
| 2 | Negative numbers and values outside the difficulty range were accepted | `parse_guess` |
| 3 | Hint messages were backwards — Too High said "Go HIGHER!", Too Low said "Go LOWER!" | `check_guess` |
| 4 | Wrong guesses on even-numbered attempts rewarded +5 points instead of subtracting | `update_score` |
| 5 | Attempt counter started at 1 instead of 0, silently removing one guess per fresh game | session state init |
| 6 | New Game button did not reset `status`, `history`, or `score`, and always picked secret from 1–100 | New Game block |
| 7 | Invalid inputs were still appended to history and counted as attempts even when rejected | submit block |
| 8 | Hard difficulty range (1–50) was smaller than Normal (1–100), making Hard easier to guess | `get_range_for_difficulty` and `attempt_limit_map` |

### Fixes applied
- **Input validation:** `parse_guess` now rejects decimals and enforces the `low`/`high` range for the selected difficulty.
- **Hint direction:** swapped the messages in `check_guess` so Too High → "Go LOWER!" and Too Low → "Go HIGHER!".
- **Score logic:** removed the even/odd branch in `update_score`; all wrong guesses now subtract 5 points.
- **Attempt counter:** changed initialization from `1` to `0`.
- **New Game reset:** resets `status`, `history`, `score`, and picks the new secret using the correct difficulty range.
- **Invalid input handling:** moved `attempts +=1` and `history.append` inside the `else` block so only valid guesses count.
- **Difficulty scaling:** Easy 1–20 / 8 attempts, Normal 1–100 / 6 attempts, Hard 1–200 / 4 attempts.

### New features added
- **High Score Tracker** — saves the best score per difficulty to `highscore.json` and displays it in the sidebar. Updates automatically when a new record is set.
- **Guess History Chart** — live Altair bar chart in the sidebar showing every guess colored by result (red = too high, blue = too low, green = correct). When the game ends, a dashed gold line marks the secret number.
- **Prominent Answer Reveal** — on loss, the secret number is displayed as a large `st.metric` so it is impossible to miss.

### Testing
18 pytest cases in `tests/test_game_logic.py` cover every bug fix. Run them with:
```
python -m pytest tests/test_game_logic.py -v
```

## 📸 Demo

> Add a screenshot of your fixed, winning game below.
- [ ] [Insert a screenshot of your fixed, winning game here]

## 🚀 Stretch Features

> Add a screenshot of your enhanced game UI below.
- [ ] [If you choose to complete Challenge 4, insert a screenshot of your Enhanced Game UI here]
