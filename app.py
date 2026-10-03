"""
app.py — AgriSecure AI entry point.

Responsibilities:
  1. Configure the Streamlit page (mobile-first, 360 px).
  2. Initialise all session-state keys with safe defaults.
  3. Route to the correct screen based on st.session_state["screen"].
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Page config (must be the first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AgriSecure AI",
    page_icon="🌾",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Session-state defaults
# ---------------------------------------------------------------------------
_DEFAULTS: dict = {
    "screen":           "lang",      # "lang" | "input" | "results"
    "lang":             "en",        # "en" | "ta" | "hi"
    "state":            None,        # selected Indian state
    "season":           None,        # selected season
    "crop":             None,        # selected crop
    "acres":            1.0,         # land size in acres
    "cost_overrides":   {},          # {component: value} from user edits
    "own_capital":      0.0,         # ₹ farmer's own funds
    "moneylender_rate": None,        # % pa; None → use config default
    "baseline":         None,        # results dict before what-if
    "whatif":           None,        # current what-if modifier
    "results":          None,        # last computed results dict
}

for _key, _default in _DEFAULTS.items():
    if _key not in st.session_state:
        st.session_state[_key] = _default

# ---------------------------------------------------------------------------
# Screen router
# ---------------------------------------------------------------------------
from ui.screens import show_language_picker, show_input_screen, show_results_screen  # noqa: E402 — import after page config

_screen = st.session_state["screen"]

if _screen == "lang":
    show_language_picker()
elif _screen == "input":
    show_input_screen()
elif _screen == "results":
    show_results_screen()
else:
    # Unknown screen: reset to language picker
    st.session_state["screen"] = "lang"
    st.rerun()
