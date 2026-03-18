import random
import json
import os
import pandas as pd
import altair as alt
import streamlit as st

HIGHSCORE_PATH = "highscore.json"


# FIX: AI identified that Hard range (1-50) was smaller than Normal (1-100), making Hard
# easier to guess. AI suggested scaling ranges so each level is genuinely harder.
# Verified by reading get_range_for_difficulty and comparing all three levels side by side.
def get_range_for_difficulty(difficulty: str):
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 200
    return 1, 100


# FIX: AI spotted that floats like 3.7 were silently converted to 3 via int(float(raw))
# instead of being rejected. AI suggested checking for "." first and returning an error.
# FIX: AI also noticed there was no range check — negative numbers and values above the
# difficulty ceiling were accepted. AI suggested adding a low/high boundary check and
# passing those values in as parameters. Verified by typing "-5" and "999" in Easy mode.
def parse_guess(raw: str, low: int, high: int):
    if raw is None:
        return False, None, "Enter a guess."

    if raw == "":
        return False, None, "Enter a guess."

    if "." in raw:
        return False, None, "Please enter a whole number, not a decimal."

    try:
        value = int(raw)
    except Exception:
        return False, None, "That is not a number."

    if value < low or value > high:
        return False, None, f"Please enter a number between {low} and {high}."

    return True, value, None


# FIX: AI caught that hint messages were backwards — "Go HIGHER!" was shown when the
# guess was too high (should say "Go LOWER!") and vice versa. Verified by guessing a
# number I knew was above the secret and confirming the corrected hint made sense.
def check_guess(guess, secret):
    if guess == secret:
        return "Win", "🎉 Correct!"

    try:
        if guess > secret:
            return "Too High", "📉 Go LOWER!"
        else:
            return "Too Low", "📈 Go HIGHER!"
    except TypeError:
        g = str(guess)
        if g == secret:
            return "Win", "🎉 Correct!"
        if g > secret:
            return "Too High", "📉 Go LOWER!"
        return "Too Low", "📈 Go HIGHER!"


# FIX: AI identified that on even-numbered attempts, a "Too High" outcome incorrectly
# awarded +5 points instead of subtracting. Being wrong should always cost points.
# AI suggested removing the even/odd branch entirely. Verified via pytest.
def update_score(current_score: int, outcome: str, attempt_number: int):
    if outcome == "Win":
        points = 100 - 10 * (attempt_number + 1)
        if points < 10:
            points = 10
        return current_score + points

    if outcome == "Too High":
        return current_score - 5

    if outcome == "Too Low":
        return current_score - 5

    return current_score


# NEW FEATURE: High score helpers — load and save best scores per difficulty to a file.
# Note: on hosted/cloud environments the filesystem may be ephemeral, so scores may not
# persist across restarts. The app still runs correctly if the file is missing.
def load_high_scores():
    if os.path.exists(HIGHSCORE_PATH):
        try:
            with open(HIGHSCORE_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_high_scores(scores: dict):
    try:
        with open(HIGHSCORE_PATH, "w") as f:
            json.dump(scores, f, indent=2)
    except IOError:
        pass


# NEW FEATURE: Guess history chart — renders a bar chart in the sidebar showing each
# guess colored by result (red=too high, blue=too low, green=correct). When the game
# ends, a dashed gold line marks the secret number so the player can see how close
# each guess was.
def render_guess_chart(history: list, secret: int, status: str, low: int, high: int):
    if not history:
        st.sidebar.caption("No guesses yet.")
        return

    results = []
    for g in history:
        if g == secret:
            results.append("Correct")
        elif g > secret:
            results.append("Too High")
        else:
            results.append("Too Low")

    df = pd.DataFrame({
        "Attempt": list(range(1, len(history) + 1)),
        "Guess": history,
        "Result": results,
    })

    color_scale = alt.Scale(
        domain=["Too High", "Too Low", "Correct"],
        range=["#e74c3c", "#3498db", "#2ecc71"],
    )

    bars = alt.Chart(df).mark_bar().encode(
        x=alt.X("Attempt:O", title="Attempt #"),
        y=alt.Y("Guess:Q", title="Guess Value",
                scale=alt.Scale(domain=[low, high])),
        color=alt.Color("Result:N", scale=color_scale),
        tooltip=["Attempt", "Guess", "Result"],
    )

    if status in ("won", "lost"):
        secret_line = (
            alt.Chart(pd.DataFrame({"secret": [secret]}))
            .mark_rule(color="gold", strokeDash=[4, 4], strokeWidth=2)
            .encode(y="secret:Q")
        )
        chart = (bars + secret_line).properties(title="Guess History", height=200)
    else:
        chart = bars.properties(title="Guess History", height=200)

    st.sidebar.altair_chart(chart, use_container_width=True)


# ── Page setup ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

# FIX: AI flagged that Easy had fewer attempts (6) than Normal (8), which made no sense.
# Updated so attempts decrease as difficulty increases.
attempt_limit_map = {
    "Easy": 8,
    "Normal": 6,
    "Hard": 4,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

# NEW FEATURE: Display high scores in the sidebar.
st.sidebar.divider()
st.sidebar.subheader("🏆 High Scores")
high_scores = load_high_scores()
for diff in ["Easy", "Normal", "Hard"]:
    best = high_scores.get(diff)
    st.sidebar.metric(label=diff, value=best if best is not None else "—")

# ── Session state defaults ────────────────────────────────────────────────────

if "secret" not in st.session_state:
    st.session_state.secret = random.randint(low, high)

# FIX: AI noticed attempts was initialized to 1 instead of 0.
if "attempts" not in st.session_state:
    st.session_state.attempts = 0

if "score" not in st.session_state:
    st.session_state.score = 0

if "status" not in st.session_state:
    st.session_state.status = "playing"

if "history" not in st.session_state:
    st.session_state.history = []

# NEW FEATURE: Render guess history chart in sidebar (updates after every guess).
with st.sidebar:
    st.divider()
    render_guess_chart(
        st.session_state.history,
        st.session_state.secret,
        st.session_state.status,
        low,
        high,
    )

# ── Main game UI ──────────────────────────────────────────────────────────────

st.subheader("Make a guess")

# FIX: AI noticed the info message always said "1 to 100" regardless of difficulty.
st.info(
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempt_limit - st.session_state.attempts}"
)

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}"
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

# FIX: AI identified that New Game didn't reset status, history, score, or use the
# correct difficulty range. All four are now reset properly.
if new_game:
    st.session_state.attempts = 0
    st.session_state.secret = random.randint(low, high)
    st.session_state.status = "playing"
    st.session_state.history = []
    st.session_state.score = 0
    st.success("New game started.")
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

if submit:
    ok, guess_int, err = parse_guess(raw_guess, low, high)

    if not ok:
        # FIX: AI noticed invalid inputs were still appended to history and counted as
        # attempts. Moved attempts increment into the else block so only valid guesses
        # count. Verified by typing "abc" and confirming history and counter unchanged.
        st.error(err)
    else:
        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)

        secret = st.session_state.secret
        outcome, message = check_guess(guess_int, secret)

        if show_hint:
            st.warning(message)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"

            # NEW FEATURE: Save high score if this run beat the previous best.
            high_scores = load_high_scores()
            current_best = high_scores.get(difficulty)
            if current_best is None or st.session_state.score > current_best:
                high_scores[difficulty] = st.session_state.score
                save_high_scores(high_scores)
                st.sidebar.success("🏆 New high score!")

            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )

        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error("Out of attempts! Better luck next time.")
                # NEW FEATURE + improved answer reveal: show the secret prominently
                # using st.metric so it is impossible to miss, then show the score.
                st.metric(label="The secret number was", value=st.session_state.secret)
                st.markdown(f"Final score: **{st.session_state.score}**")

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
