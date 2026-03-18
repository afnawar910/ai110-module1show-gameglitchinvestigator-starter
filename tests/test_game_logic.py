import sys
from unittest.mock import MagicMock

# Mock streamlit before importing app so the UI code doesn't execute during tests
st_mock = MagicMock()
st_mock.sidebar.selectbox.return_value = "Normal"
st_mock.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
sys.modules["streamlit"] = st_mock

from app import parse_guess, check_guess, update_score, get_range_for_difficulty


# ---------------------------------------------------------------------------
# Existing baseline tests
# ---------------------------------------------------------------------------

def test_winning_guess():
    outcome, _ = check_guess(50, 50)
    assert outcome == "Win"

def test_guess_too_high():
    outcome, _ = check_guess(60, 50)
    assert outcome == "Too High"

def test_guess_too_low():
    outcome, _ = check_guess(40, 50)
    assert outcome == "Too Low"


# ---------------------------------------------------------------------------
# Bug fix 1 — float inputs must be rejected, not silently converted
# ---------------------------------------------------------------------------

def test_float_input_is_rejected():
    """3.7 should not be silently rounded to 3 and accepted."""
    ok, value, err = parse_guess("3.7", 1, 20)
    assert ok is False
    assert value is None
    assert err is not None

def test_float_with_zero_decimal_is_rejected():
    """5.0 still contains a decimal point and should be rejected."""
    ok, value, err = parse_guess("5.0", 1, 20)
    assert ok is False


# ---------------------------------------------------------------------------
# Bug fix 2 — out-of-range inputs must be rejected
# ---------------------------------------------------------------------------

def test_negative_number_rejected():
    """Negative numbers are outside the valid range and should be rejected."""
    ok, value, err = parse_guess("-5", 1, 20)
    assert ok is False
    assert value is None

def test_number_above_range_rejected():
    """999 is above the Easy ceiling of 20 and should be rejected."""
    ok, value, err = parse_guess("999", 1, 20)
    assert ok is False

def test_number_at_low_boundary_accepted():
    """1 is the lowest valid value on Easy and should be accepted."""
    ok, value, err = parse_guess("1", 1, 20)
    assert ok is True
    assert value == 1

def test_number_at_high_boundary_accepted():
    """20 is the highest valid value on Easy and should be accepted."""
    ok, value, err = parse_guess("20", 1, 20)
    assert ok is True
    assert value == 20


# ---------------------------------------------------------------------------
# Bug fix 3 — hints must always be correct (no string comparison flip)
# ---------------------------------------------------------------------------

def test_hint_too_high_says_go_lower():
    """Guessing 60 when secret is 50: outcome Too High, hint should say go LOWER."""
    outcome, message = check_guess(60, 50)
    assert outcome == "Too High"
    assert "LOWER" in message

def test_hint_too_low_says_go_higher():
    """Guessing 30 when secret is 50: outcome Too Low, hint should say go HIGHER."""
    outcome, message = check_guess(30, 50)
    assert outcome == "Too Low"
    assert "HIGHER" in message

def test_hint_not_flipped_by_string_comparison():
    """
    The original bug converted secret to a string on even attempts.
    String comparison makes "9" > "50" (True) which flips the hint.
    This test confirms integer comparison is always used.
    """
    # 9 < 50, so result must be Too Low regardless of attempt number
    outcome, _ = check_guess(9, 50)
    assert outcome == "Too Low"


# ---------------------------------------------------------------------------
# Bug fix 4 — wrong guess (Too High) must always subtract points
# ---------------------------------------------------------------------------

def test_too_high_always_subtracts_score():
    """Guessing too high on any attempt should subtract 5, never add."""
    score_after = update_score(100, "Too High", 2)  # attempt 2 (even) was the bug
    assert score_after == 95

def test_too_high_odd_attempt_subtracts_score():
    score_after = update_score(100, "Too High", 3)
    assert score_after == 95

def test_too_low_subtracts_score():
    score_after = update_score(100, "Too Low", 1)
    assert score_after == 95


# ---------------------------------------------------------------------------
# Bug fix 5 — difficulty ranges must scale correctly
# ---------------------------------------------------------------------------

def test_easy_range():
    low, high = get_range_for_difficulty("Easy")
    assert low == 1 and high == 20

def test_normal_range():
    low, high = get_range_for_difficulty("Normal")
    assert low == 1 and high == 100

def test_hard_range_is_larger_than_normal():
    """Hard must have a wider range than Normal to actually be harder."""
    _, normal_high = get_range_for_difficulty("Normal")
    _, hard_high = get_range_for_difficulty("Hard")
    assert hard_high > normal_high
