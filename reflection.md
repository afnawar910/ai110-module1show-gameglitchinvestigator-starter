# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

When I first ran the game it appeared to work on the surface — the UI loaded, I could type a number and get a hint. But after playing a few rounds I noticed several things that were clearly wrong.

**Bug 1 — Float inputs were silently accepted as whole numbers**
- Expected: If I typed `7.5`, the game should reject it and say "Please enter a whole number."
- Actual: The game silently converted `7.5` to `7` and accepted it as a valid guess with no warning.
- Fix: `parse_guess` now checks for a `.` in the input and immediately returns an error message instead of converting.

**Bug 2 — Negative numbers and out-of-range inputs were accepted**
- Expected: On Easy difficulty (range 1–20), typing `-5` or `999` should be rejected since those numbers are outside the valid range.
- Actual: The game accepted any integer — positive, negative, or far outside the range — without any validation error.
- Fix: `parse_guess` now takes `low` and `high` as parameters and returns an error if the value falls outside that range.

**Bug 3 — Attempt counter started at 1 instead of 0**
- Expected: The attempt counter should start at 0 so the full number of allowed guesses are available from the beginning.
- Actual: `attempts` was initialized to `1`, so the first game silently gave one fewer guess than advertised.
- Fix: Changed the initialization from `1` to `0`.

**Bug 4 — New Game button did not fully reset the game**
- Expected: Clicking New Game should clear history, reset the score, restore status to "playing", and pick a secret within the correct difficulty range.
- Actual: `status`, `history`, and `score` were never reset, so a finished game locked up immediately after clicking New Game. The new secret was also always picked from 1–100 regardless of difficulty.
- Fix: New Game now resets `status`, `history`, `score`, and uses `low`/`high` from the selected difficulty when generating the new secret.

**Bug 5 — Hints were backwards on even-numbered attempts**
- Expected: The hint should always correctly say "Go Higher" when the guess is too low and "Go Lower" when the guess is too high.
- Actual: On every 2nd, 4th, and 6th guess the secret was converted to a string before comparison. String comparison (`"9" > "50"` evaluates to `True`) caused the hints to flip direction.
- Fix: Removed the string conversion entirely. The secret is always compared as an integer.

**Bug 6 — Hints said the wrong direction ("Go Higher" when you should go lower)**
- Expected: When `guess > secret` (guess is too high), the message should say "Go LOWER." When `guess < secret` (guess is too low), it should say "Go HIGHER."
- Actual: The messages were swapped — guessing too high showed "Go HIGHER!" and guessing too low showed "Go LOWER!", actively misleading the player.
- Fix: Swapped the messages so each outcome points the player in the correct direction.

**Bug 7 — Guessing too high on even attempts rewarded points instead of penalizing**
- Expected: Any wrong guess should always subtract from the score.
- Actual: In `update_score`, a "Too High" outcome on an even-numbered attempt added `+5` points, rewarding incorrect guesses.
- Fix: Removed the even/odd branch — "Too High" now always subtracts 5 points.

**Bug 8 — Difficulty ranges did not scale correctly (Hard was easier than Normal)**
- Expected: Easy should have the smallest range with the most attempts; Hard should have the largest range with the fewest attempts.
- Actual: Hard used 1–50 (smaller than Normal's 1–100) and Easy had fewer attempts (6) than Normal (8), so the difficulties were backwards.
- Fix: Updated ranges to Easy 1–20 (8 attempts), Normal 1–100 (6 attempts), Hard 1–200 (4 attempts).

---

## 2. How did you use AI as a teammate?

I used Claude (Claude Code) as my AI teammate throughout this project. I pasted code into the chat and asked it to explain what each function was doing, identify bugs, and suggest fixes. I also asked it to write pytest cases after each fix so I could confirm the repair actually worked.

**Correct AI suggestion — hint messages were backwards**
- What the AI suggested: Claude read `check_guess` and noticed that when `guess > secret` (too high), the message said `"📈 Go HIGHER!"` instead of `"📉 Go LOWER!"`, and the opposite for too low. It suggested swapping the messages so they point the player in the right direction.
- Was it correct? Yes, completely correct.
- How I verified it: I played the game manually, guessed a number I knew was above the secret, and confirmed the hint now correctly told me to go lower. I also added `test_hint_too_high_says_go_lower` and `test_hint_too_low_says_go_higher` to the pytest suite and both passed.

**Incorrect/misleading AI suggestion — float inputs**
- What the AI suggested: Claude initially suggested using `int(float(raw))` to handle decimal inputs, which it described as a way to "gracefully handle floats by converting them to integers."
- Was it correct? No — this was the original bug. Silently converting `3.7` to `3` is misleading to the user, who receives no feedback that their input was changed. The game should reject decimals entirely, not quietly round them down.
- How I verified it: I typed `7.5` into the game with the original code and confirmed it was accepted as `7` with no error shown. After rejecting the AI suggestion and instead returning an error message for any input containing a `.`, I retyped `7.5` and saw the proper error: "Please enter a whole number, not a decimal."

---

## 3. Debugging and testing your fixes

I decided a bug was really fixed only when two things were true: the game behaved correctly when I played it manually, and a pytest test targeting that specific bug passed.

**Manual testing**
For the New Game bug, I played a full game until I won, then clicked New Game. Before the fix, the game immediately showed "You already won" and blocked play. After resetting `status`, `history`, `score`, and using the correct difficulty range for the new secret, clicking New Game started a fresh game as expected.

For input validation, I typed `"5g]"`, `-5`, `999`, and `7.5` into Easy mode. Before the fix, all of these were either accepted or added to history. After the fix, each one displayed a specific error message and did not increment the attempt counter or appear in history.

**Pytest testing**
I ran `python -m pytest tests/test_game_logic.py -v` after each group of fixes. The test `test_too_high_always_subtracts_score` specifically targeted the score bug by calling `update_score(100, "Too High", 2)` — attempt 2 was the even-numbered case that previously added `+5` instead of subtracting. The test asserted the result was `95`, and it passed after the fix. Similarly, `test_float_input_is_rejected` called `parse_guess("3.7", 1, 20)` and asserted `ok is False`, confirming floats are now rejected rather than silently converted.

**AI help with tests**
Claude suggested the overall structure of the pytest file and recommended mocking the streamlit module using `unittest.mock.MagicMock` so the test file could import functions from `app.py` without triggering the UI code. It also recommended testing boundary values (exactly `1` and exactly `20` on Easy) in addition to out-of-range values, which caught a subtle edge case in the range validation logic.

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
