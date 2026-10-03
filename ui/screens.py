"""
ui/screens.py — AgriSecure AI
Screen rendering functions for Streamlit.

All UI text comes from lang/*.json via ui.i18n.t().
No hardcoded display strings anywhere in this file.
"""

import os

import streamlit as st

from ui.i18n import t
from config import get_config

# ---------------------------------------------------------------------------
# Crop icon mapping
# ---------------------------------------------------------------------------

CROP_ICONS: dict[str, str] = {
    "paddy":     "🌾",
    "maize":     "🌽",
    "groundnut": "🥜",
    "wheat":     "🌾",
    "cotton":    "🌿",
    "sugarcane": "🎋",
    "soybean":   "🫘",
    "jowar":     "🌾",
    "bajra":     "🌾",
    "sunflower": "🌻",
    "turmeric":  "🌿",
    "onion":     "🧅",
    "tomato":    "🍅",
}

_DEFAULT_ICON = "🌱"


def _crop_icon(crop_name: str) -> str:
    """Return the emoji icon for *crop_name* (matched case-insensitively)."""
    return CROP_ICONS.get(crop_name.lower(), _DEFAULT_ICON)


def _crop_i18n_key(crop_name: str) -> str:
    """Return the i18n key for a crop name, e.g. 'paddy' -> 'crop_paddy'."""
    return f"crop_{crop_name.lower()}"


# ---------------------------------------------------------------------------
# Cached data helpers (st.cache_data lives here in the UI layer)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _load_yield_price() -> "pd.DataFrame":  # type: ignore[name-defined]
    import pandas as pd
    from core.data_loader import load_yield_price
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return load_yield_price(os.path.join(_root, "data", "yield_price.csv"))


@st.cache_data(show_spinner=False)
def _load_cost() -> "pd.DataFrame":  # type: ignore[name-defined]
    import pandas as pd
    from core.data_loader import load_cost
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return load_cost(os.path.join(_root, "data", "cost.csv"))


@st.cache_data(show_spinner=False)
def _load_msp() -> "pd.DataFrame":  # type: ignore[name-defined]
    import pandas as pd
    from core.data_loader import load_msp
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return load_msp(os.path.join(_root, "data", "msp.csv"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lang() -> str:
    """Return the currently selected language code (default 'en')."""
    return st.session_state.get("lang", "en")


_MOBILE_CSS = """
<style>
/* Mobile-first layout: constrain width and centre */
.block-container {
    max-width: 360px !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}
/* Make Streamlit buttons full-width and tall */
div.stButton > button {
    width: 100%;
    min-height: 3.2rem;
    font-size: 1.15rem;
    font-weight: 600;
    border-radius: 0.6rem;
}
/* Crop card grid */
.crop-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 0.6rem 0.3rem;
    border: 2px solid #ddd;
    border-radius: 0.7rem;
    cursor: pointer;
    background: #fafafa;
    font-size: 0.88rem;
    text-align: center;
    min-height: 4.5rem;
    transition: border-color 0.15s, background 0.15s;
}
.crop-card.selected {
    border-color: #2e7d32;
    background: #e8f5e9;
    font-weight: 700;
}
.crop-card .crop-emoji {
    font-size: 1.8rem;
    line-height: 1;
    margin-bottom: 0.25rem;
}
</style>
"""


# ---------------------------------------------------------------------------
# Screen: Language Picker  (task 6.1)
# ---------------------------------------------------------------------------

def show_language_picker() -> None:
    """Render the language selection screen.

    The farmer sees three large buttons for English, Tamil, and Hindi.
    Tapping a button sets ``st.session_state.lang`` and navigates to the
    input screen.  All visible text comes from lang/en.json (always used for
    the picker because no language has been chosen yet).
    """
    # The picker always shows the English strings (language not yet chosen)
    lang = "en"

    st.markdown(
        """
        <style>
        /* Mobile-first layout: constrain width and centre */
        .block-container {
            max-width: 360px !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        /* Make Streamlit buttons full-width and tall */
        div.stButton > button {
            width: 100%;
            min-height: 3.2rem;
            font-size: 1.15rem;
            font-weight: 600;
            border-radius: 0.6rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # App title and subtitle
    st.markdown(
        f"<h1 style='text-align:center; font-size:2rem; margin-bottom:0.2rem;'>🌾 {t('app_title', lang)}</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align:center; color:#555; margin-bottom:2rem;'>{t('app_subtitle', lang)}</p>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<h3 style='text-align:center; margin-bottom:1rem;'>{t('lang_picker', lang)}</h3>",
        unsafe_allow_html=True,
    )

    # Three language buttons — full width, one per row
    if st.button(f"🇬🇧  {t('lang_english', lang)}", key="btn_lang_en", use_container_width=True):
        st.session_state["lang"] = "en"
        st.session_state["screen"] = "input"
        st.rerun()

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    if st.button(f"🇮🇳  {t('lang_tamil', lang)}", key="btn_lang_ta", use_container_width=True):
        st.session_state["lang"] = "ta"
        st.session_state["screen"] = "input"
        st.rerun()

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    if st.button(f"🇮🇳  {t('lang_hindi', lang)}", key="btn_lang_hi", use_container_width=True):
        st.session_state["lang"] = "hi"
        st.session_state["screen"] = "input"
        st.rerun()


# ---------------------------------------------------------------------------
# Screen: Input  (task 6.2)
# ---------------------------------------------------------------------------

def show_input_screen() -> None:
    """Render the farmer input screen.

    Sections
    --------
    1. Header — title + Back button to language picker.
    2. State dropdown — unique states from yield_price CSV.
    3. Season dropdown — seasons for the selected state.
    4. Crop icon cards — 3-column grid; clicking selects the crop.
    5. Land size stepper — acres with min/max/step from config.
    6. Optional inputs — collapsible expander (own capital, moneylender rate).
    7. Calculate button — disabled until state + season + crop are all set.
       On click, runs core calculations and routes to the results screen.

    All visible text comes from lang/*.json via ``t(key, lang)``.
    Requirements: 2.1–2.6, 3.1–3.3, 4.1–4.2.
    """
    lang = _lang()

    st.markdown(_MOBILE_CSS, unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # 1. Header — title + Back button
    # -----------------------------------------------------------------------
    col_back, col_title = st.columns([1, 4])
    with col_back:
        if st.button(f"← {t('btn_back', lang)}", key="btn_back_to_lang"):
            st.session_state["screen"] = "lang"
            st.rerun()
    with col_title:
        st.markdown(
            f"<h2 style='margin:0; font-size:1.3rem; line-height:2.2rem;'>🌾 {t('input_title', lang)}</h2>",
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='margin:0.5rem 0 1rem 0;'>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # 2. State dropdown
    # -----------------------------------------------------------------------
    df_yp = _load_yield_price()
    states = sorted(df_yp["state"].unique().tolist())

    current_state = st.session_state.get("state")
    state_index = 0  # "— select —" placeholder
    if current_state in states:
        state_index = states.index(current_state) + 1  # +1 for placeholder

    state_options = [f"— {t('select_state', lang)} —"] + states
    chosen_state_raw = st.selectbox(
        label=t("select_state", lang),
        options=state_options,
        index=state_index,
        key="selectbox_state",
        label_visibility="visible",
    )
    chosen_state: str | None = (
        None if chosen_state_raw == state_options[0] else chosen_state_raw
    )

    # Update session state only if changed, to avoid unnecessary reruns
    if chosen_state != st.session_state.get("state"):
        st.session_state["state"] = chosen_state
        # Reset downstream selections when state changes
        st.session_state["season"] = None
        st.session_state["crop"] = None

    # -----------------------------------------------------------------------
    # 3. Season dropdown — only shown once state is selected
    # -----------------------------------------------------------------------
    chosen_season: str | None = None
    if chosen_state:
        state_df = df_yp[df_yp["state"] == chosen_state]
        seasons = sorted(state_df["season"].unique().tolist())

        current_season = st.session_state.get("season")
        season_index = 0
        if current_season in seasons:
            season_index = seasons.index(current_season) + 1

        season_options = [f"— {t('select_season', lang)} —"] + seasons
        chosen_season_raw = st.selectbox(
            label=t("select_season", lang),
            options=season_options,
            index=season_index,
            key="selectbox_season",
            label_visibility="visible",
        )
        chosen_season = (
            None if chosen_season_raw == season_options[0] else chosen_season_raw
        )

        if chosen_season != st.session_state.get("season"):
            st.session_state["season"] = chosen_season
            st.session_state["crop"] = None  # reset crop when season changes

    # -----------------------------------------------------------------------
    # 4. Crop icon cards — 3-column grid
    # -----------------------------------------------------------------------
    chosen_crop: str | None = None
    if chosen_state and chosen_season:
        from core.crops import available_crops as _available_crops

        crops = _available_crops(chosen_state, chosen_season, df_yp)

        if crops:
            st.markdown(
                f"<p style='font-weight:600; margin-bottom:0.4rem;'>"
                f"{t('select_crop', lang)}</p>",
                unsafe_allow_html=True,
            )

            selected_crop = st.session_state.get("crop")
            cols = st.columns(3)

            for idx, crop in enumerate(crops):
                icon = _crop_icon(crop)
                crop_label = t(_crop_i18n_key(crop), lang)
                col = cols[idx % 3]

                is_selected = selected_crop == crop
                # Use a button styled as a card
                card_style = (
                    "border:2px solid #2e7d32; background:#e8f5e9; border-radius:0.7rem;"
                    "padding:0.5rem; width:100%; cursor:pointer; font-weight:700;"
                    if is_selected
                    else
                    "border:2px solid #ddd; background:#fafafa; border-radius:0.7rem;"
                    "padding:0.5rem; width:100%; cursor:pointer;"
                )
                with col:
                    if st.button(
                        f"{icon}\n{crop_label}",
                        key=f"crop_card_{crop}",
                        use_container_width=True,
                        help=crop_label,
                        type="primary" if is_selected else "secondary",
                    ):
                        st.session_state["crop"] = crop
                        st.rerun()

            chosen_crop = st.session_state.get("crop")
            # Guard: if saved crop is not in current crops list, clear it
            if chosen_crop and chosen_crop not in crops:
                st.session_state["crop"] = None
                chosen_crop = None
        else:
            st.info(t("error_no_data", lang))

    # -----------------------------------------------------------------------
    # 5. Land size stepper
    # -----------------------------------------------------------------------
    land_min = get_config("LAND_MIN_ACRES")
    land_max = get_config("LAND_MAX_ACRES")
    land_step = get_config("LAND_STEP_ACRES")

    current_acres = st.session_state.get("acres", 1.0)
    acres = st.number_input(
        label=f"{t('land_size_label', lang)} ({t('land_size_unit', lang)})",
        min_value=float(land_min),
        max_value=float(land_max),
        step=float(land_step),
        value=float(current_acres),
        key="input_acres",
        format="%.1f",
    )
    st.session_state["acres"] = acres

    # -----------------------------------------------------------------------
    # 6. Optional inputs — collapsible expander
    # -----------------------------------------------------------------------
    ml_rate_min = get_config("MONEYLENDER_RATE_MIN")
    ml_rate_max = get_config("MONEYLENDER_RATE_MAX")

    with st.expander("⚙️ " + t("own_capital_label", lang).split("(")[0].strip() + " & " +
                     t("moneylender_rate_label", lang).split("(")[0].strip()):
        own_capital = st.number_input(
            label=t("own_capital_label", lang),
            min_value=0.0,
            step=500.0,
            value=float(st.session_state.get("own_capital", 0.0)),
            key="input_own_capital",
            format="%.0f",
        )
        st.session_state["own_capital"] = own_capital

        ml_rate_default = st.session_state.get("moneylender_rate") or 0.0
        ml_rate_raw = st.number_input(
            label=t("moneylender_rate_label", lang),
            min_value=0.0,
            max_value=float(ml_rate_max),
            step=1.0,
            value=float(ml_rate_default),
            key="input_ml_rate",
            format="%.1f",
            help=f"{ml_rate_min}–{ml_rate_max}%",
        )
        # 0.0 means "not entered" → store as None
        if ml_rate_raw <= 0.0:
            st.session_state["moneylender_rate"] = None
        elif ml_rate_raw < ml_rate_min or ml_rate_raw > ml_rate_max:
            st.error(t("error_rate_range", lang))
            st.session_state["moneylender_rate"] = None
        else:
            st.session_state["moneylender_rate"] = float(ml_rate_raw)

    # -----------------------------------------------------------------------
    # 7. Calculate button — disabled until state + season + crop are selected
    # -----------------------------------------------------------------------
    all_selected = bool(
        st.session_state.get("state")
        and st.session_state.get("season")
        and st.session_state.get("crop")
    )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    if st.button(
        f"🧮 {t('btn_calculate', lang)}",
        key="btn_calculate",
        disabled=not all_selected,
        use_container_width=True,
        type="primary",
    ):
        _run_calculations(lang)

    if not all_selected:
        st.caption(
            "⬆️ " + t("select_state", lang) + " → " +
            t("select_season", lang) + " → " +
            t("select_crop", lang)
        )

    # -----------------------------------------------------------------------
    # Footer — placeholder notice
    # -----------------------------------------------------------------------
    st.markdown("<hr style='margin:1.5rem 0 0.5rem 0;'>", unsafe_allow_html=True)
    st.caption(t("footer_placeholder_note", lang))


# ---------------------------------------------------------------------------
# Calculation runner — called when the Calculate button is clicked
# ---------------------------------------------------------------------------

def _run_calculations(lang: str) -> None:
    """Run all core calculations and store results in session state.

    Loads DataFrames, calls estimate_costs and rank_top3, assembles a
    ``results`` dict, and sets ``screen = "results"`` before rerunning.

    Satisfies Requirements 3.1–3.3, 4.1–4.2.
    """
    from core.costs import estimate_costs
    from core.crops import rank_top3

    state = st.session_state["state"]
    season = st.session_state["season"]
    crop = st.session_state["crop"]
    acres = float(st.session_state.get("acres", 1.0))
    overrides = st.session_state.get("cost_overrides") or {}

    df_cost = _load_cost()
    df_yp = _load_yield_price()
    df_msp = _load_msp()

    # --- Cost estimate for the selected crop ---
    cost_result = estimate_costs(
        cost_df=df_cost,
        crop=crop,
        state=state,
        season=season,
        acres=acres,
        overrides=overrides if overrides else None,
    )

    # --- Top-3 crop ranking for state+season ---
    top3 = rank_top3(
        state=state,
        season=season,
        land_acres=acres,
        df_yield_price=df_yp,
        df_msp=df_msp,
        cost_per_acre=cost_result["total"] / acres if acres > 0 else None,
    )

    # --- Assemble results dict ---
    st.session_state["results"] = {
        "state": state,
        "season": season,
        "crop": crop,
        "acres": acres,
        "costs": cost_result,
        "top3": top3,
        "own_capital": st.session_state.get("own_capital", 0.0),
        "moneylender_rate": st.session_state.get("moneylender_rate"),
    }

    st.session_state["screen"] = "results"
    st.rerun()


# ---------------------------------------------------------------------------
# Screen: Results  (task 6.3)
# ---------------------------------------------------------------------------

def show_results_screen() -> None:
    """Render the results screen.

    Sections
    --------
    1. Header — title + Back button to input screen.
    2. Top-3 crop recommendation cards with risk/rank badges.
    3. Cost breakdown with editable number_inputs.
    4. Funding gap section (gap, KCC limit, residual).
    5. Repayment window (months until harvest).
    6. Footer — data notes + Recalculate button.

    Requirements: 3, 4, 5, 7.
    """
    from core.formatting import indian_format
    from core.costs import estimate_costs, COST_COMPONENTS
    import core.loans as loans

    lang = _lang()
    results = st.session_state.get("results")

    st.markdown(_MOBILE_CSS, unsafe_allow_html=True)

    # Guard: if somehow we land here with no results, bounce back
    if not results:
        st.session_state["screen"] = "input"
        st.rerun()
        return

    state = results["state"]
    season = results["season"]
    crop = results["crop"]
    acres = results["acres"]
    costs = results["costs"]
    top3 = results["top3"]
    own_capital = results["own_capital"]

    # -----------------------------------------------------------------------
    # 1. Header — title + Back button
    # -----------------------------------------------------------------------
    col_back, col_title = st.columns([1, 4])
    with col_back:
        if st.button(f"← {t('btn_back', lang)}", key="btn_back_results"):
            st.session_state["screen"] = "input"
            st.rerun()
    with col_title:
        st.markdown(
            f"<h2 style='margin:0; font-size:1.3rem; line-height:2.2rem;'>"
            f"🌾 {t('results_title', lang)}</h2>",
            unsafe_allow_html=True,
        )

    st.markdown("<hr style='margin:0.5rem 0 1rem 0;'>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # 2. Top-3 crop recommendation cards
    # -----------------------------------------------------------------------
    st.markdown(
        f"<h3 style='font-size:1.1rem; margin-bottom:0.6rem;'>"
        f"🏆 {t('top_crops_header', lang)}</h3>",
        unsafe_allow_html=True,
    )

    _RANK_BADGES = {1: "🥇", 2: "🥈", 3: "🥉"}
    _RISK_DOTS = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
    _RISK_LABELS = {"green": "risk_low", "yellow": "risk_medium", "red": "risk_high"}

    for entry in top3:
        crop_name: str = entry["crop"]
        rank: int = entry.get("rank", 0)
        risk_colour: str = entry.get("risk_colour", "red")
        min_rev: float = entry.get("min_revenue_per_acre", 0.0)
        max_rev: float = entry.get("max_revenue_per_acre", 0.0)

        icon = _crop_icon(crop_name)
        crop_label = t(_crop_i18n_key(crop_name), lang)
        rank_badge = _RANK_BADGES.get(rank, "")
        risk_dot = _RISK_DOTS.get(risk_colour, "🔴")
        risk_label = t(_RISK_LABELS.get(risk_colour, "risk_unknown"), lang)

        is_selected = crop_name.lower() == crop.lower()

        # Card border colour: green highlight for the chosen crop
        border_colour = "#2e7d32" if is_selected else "#ddd"
        bg_colour = "#e8f5e9" if is_selected else "#fafafa"
        selected_marker = "✅ " if is_selected else ""

        rev_range_str = (
            f"{indian_format(min_rev * acres)} – {indian_format(max_rev * acres)}"
        )

        st.markdown(
            f"""
            <div style="border:2px solid {border_colour}; background:{bg_colour};
                        border-radius:0.8rem; padding:0.8rem 1rem; margin-bottom:0.6rem;">
              <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.2rem;">
                <span style="font-size:1.6rem; line-height:1;">{icon}</span>
                <span style="font-size:1.05rem; font-weight:700;">{selected_marker}{rank_badge} {crop_label}</span>
              </div>
              <div style="display:flex; gap:0.6rem; flex-wrap:wrap; margin-bottom:0.3rem;">
                <span style="background:#fff; border:1px solid #ccc; border-radius:1rem;
                             padding:0.15rem 0.6rem; font-size:0.85rem;">{risk_dot} {risk_label}</span>
              </div>
              <div style="font-size:0.82rem; color:#555;">
                {t('funding_gap_label', lang)}: <strong>{rev_range_str}</strong>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("❓ " + t("why_risk", lang)):
        st.write(t("why_risk_text", lang))

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # 3. Cost breakdown — editable fields
    # -----------------------------------------------------------------------
    st.markdown(
        f"<h3 style='font-size:1.1rem; margin-bottom:0.6rem;'>"
        f"💰 {t('cost_breakdown_header', lang)}</h3>",
        unsafe_allow_html=True,
    )

    # Retrieve existing overrides from session state (persisted across reruns)
    overrides: dict = st.session_state.get("cost_overrides") or {}

    _COST_ICONS = {
        "seed": "🌱",
        "fertilizer": "🧪",
        "labour": "👷",
        "irrigation": "💧",
        "other": "📦",
    }

    cost_min = get_config("COST_COMPONENT_MIN")
    cost_max = get_config("COST_COMPONENT_MAX")
    edited_values: dict = {}

    for component in COST_COMPONENTS:
        comp_icon = _COST_ICONS.get(component, "•")
        comp_label = t(f"cost_{component}", lang)
        # Use the override value if already set, else use the original computed cost
        default_val = float(overrides.get(component, costs.get(component, 0.0)))

        edited_val = st.number_input(
            label=f"{comp_icon} {comp_label}",
            min_value=float(cost_min),
            max_value=float(cost_max),
            value=default_val,
            step=100.0,
            format="%.0f",
            key=f"cost_override_{component}",
        )
        edited_values[component] = edited_val

    # Persist non-default overrides; only store if different from the original
    new_overrides = {}
    for component in COST_COMPONENTS:
        original_val = float(costs.get(component, 0.0))
        edited_val = edited_values[component]
        if abs(edited_val - original_val) > 0.01:
            new_overrides[component] = edited_val

    st.session_state["cost_overrides"] = new_overrides

    # Recompute total using edited values (merges original + overrides)
    effective_costs = {c: edited_values[c] for c in COST_COMPONENTS}
    computed_total = sum(effective_costs.values())

    st.markdown(
        f"<div style='background:#f0f4f8; border-radius:0.6rem; padding:0.7rem 1rem; "
        f"margin-top:0.5rem; font-size:1.05rem;'>"
        f"<strong>{t('cost_total', lang)}:</strong> "
        f"<span style='color:#1a5276; font-size:1.15rem; font-weight:800;'>"
        f"{indian_format(computed_total)}</span></div>",
        unsafe_allow_html=True,
    )

    st.caption(t("disclaimer_estimate", lang))

    if costs.get("placeholder"):
        st.warning(t("placeholder_notice", lang))

    with st.expander("❓ " + t("why_cost", lang)):
        st.write(t("why_cost_text", lang))

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # 4. Funding gap section
    # -----------------------------------------------------------------------
    st.markdown(
        f"<h3 style='font-size:1.1rem; margin-bottom:0.6rem;'>"
        f"🏦 {t('funding_gap_header', lang)}</h3>",
        unsafe_allow_html=True,
    )

    gap = loans.funding_gap(computed_total, own_capital)
    kcc_limit = loans.institutional_loan_limit(acres)
    residual = loans.residual_gap(gap, kcc_limit)

    _funding_rows = [
        (t("funding_gap_label", lang), gap, "🔴" if gap > 0 else "🟢"),
        (t("lender_kcc", lang) + " (KCC " + t("funding_gap_header", lang) + ")", kcc_limit, "🟢"),
        (t("residual_gap_label", lang), residual, "🔴" if residual > 0 else "🟢"),
    ]

    for label, value, indicator in _funding_rows:
        col_lbl, col_val = st.columns([3, 2])
        with col_lbl:
            st.write(f"{indicator} {label}")
        with col_val:
            st.markdown(
                f"<div style='text-align:right; font-weight:700; font-size:1.05rem;'>"
                f"{indian_format(value)}</div>",
                unsafe_allow_html=True,
            )

    st.caption(t("disclaimer_loans", lang))

    with st.expander("❓ " + t("why_funding_gap", lang)):
        st.write(t("why_funding_gap_text", lang))

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # 5. Repayment window
    # -----------------------------------------------------------------------
    st.markdown(
        f"<h3 style='font-size:1.1rem; margin-bottom:0.6rem;'>"
        f"📅 {t('repayment_window_header', lang)}</h3>",
        unsafe_allow_html=True,
    )

    df_cost = _load_cost()
    months = loans.harvest_window(crop, season, df_cost)

    if months is not None:
        st.markdown(
            f"<div style='background:#e8f5e9; border-radius:0.6rem; padding:0.7rem 1rem; "
            f"font-size:1.05rem;'>"
            f"🌿 {t('harvest_window_months', lang)}: "
            f"<strong style='font-size:1.15rem; color:#2e7d32;'>{months}</strong> "
            f"{'month' if months == 1 else 'months'}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.info(t("error_no_data", lang))

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # 6. Footer
    # -----------------------------------------------------------------------
    st.markdown("<hr style='margin:1rem 0 0.5rem 0;'>", unsafe_allow_html=True)
    st.caption(t("footer_data_note", lang))
    st.caption(t("footer_placeholder_note", lang))

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    if st.button(
        f"🔄 {t('btn_recalculate', lang)}",
        key="btn_recalculate",
        use_container_width=True,
        type="primary",
    ):
        st.session_state["screen"] = "input"
        st.rerun()
