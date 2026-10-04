"""
ui/preset_buttons.py — AgriSecure AI
======================================

Preset question buttons panel for the results screen.

Three full-width buttons let the farmer ask a quick question about their
computed plan.  Each button calls the matching pure function from
assistant/presets.py, which reads session state results and returns a
formatted answer string without any LLM call.

All visible text comes from lang/*.json via ui.i18n.t().
No hardcoded display strings in this file.

Requirements: 12 (preset question buttons, no LLM, ≤ 1 second response)
"""

import streamlit as st

from ui.i18n import t


# ---------------------------------------------------------------------------
# Panel renderer
# ---------------------------------------------------------------------------

def render_preset_buttons(
    lang: str,
    *,
    df_yield_price,
    df_msp,
    df_cost,
) -> None:
    """Render the three preset question buttons with inline answers.

    The buttons are full-width and labelled from the language file.
    On click, the matching answer function from assistant/presets.py is
    called with the current session results dict.  The answer is displayed
    prefixed by t("you_asked") + the question label.

    If the answer function returns None (required results not yet computed),
    a localised error message is shown that names the missing step.

    Parameters
    ----------
    lang : str
        Active language code ("en", "ta", "hi").
    df_yield_price, df_msp, df_cost : pd.DataFrame
        Pre-loaded DataFrames forwarded to the answer functions.
    """
    from assistant.presets import (
        answer_repay_on_time,
        answer_rain_fails,
        answer_moneylender_worth_it,
    )
    from ui.speaker_button import render_speaker_button

    results = st.session_state.get("results")

    # Section header
    st.markdown(
        f"<h3 style='font-size:1.1rem; margin-bottom:0.4rem;'>"
        f"💬 Quick Questions</h3>",
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------------------------
    # Q1 — Can I repay on time?
    # -----------------------------------------------------------------------
    q1_label = t("preset_repay_label", lang)
    if st.button(f"💳 {q1_label}", key="btn_preset_repay", use_container_width=True):
        st.session_state["preset_active"] = "repay"

    if st.session_state.get("preset_active") == "repay":
        with st.container():
            st.markdown(
                f"<div style='background:#f0f4f8; border-radius:0.6rem; "
                f"padding:0.7rem 1rem; margin-bottom:0.6rem; font-size:0.95rem;'>"
                f"<strong>{t('you_asked', lang)}</strong> {q1_label}</div>",
                unsafe_allow_html=True,
            )
            if results is None:
                st.warning(t("preset_missing_repay", lang))
            else:
                answer = answer_repay_on_time(
                    results=results,
                    df_yield_price=df_yield_price,
                    df_msp=df_msp,
                    df_cost=df_cost,
                    t_fn=lambda key: t(key, lang),
                )
                if answer is None:
                    st.warning(t("preset_missing_repay", lang))
                else:
                    st.markdown(
                        f"<div style='background:#fff; border:1px solid #ddd; "
                        f"border-radius:0.6rem; padding:0.7rem 1rem; "
                        f"font-size:0.95rem; line-height:1.5;'>"
                        f"{answer}</div>",
                        unsafe_allow_html=True,
                    )
                    render_speaker_button(
                        text=answer,
                        lang=lang,
                        button_key="tts_preset_repay",
                    )

    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # Q2 — What if rain fails?
    # -----------------------------------------------------------------------
    q2_label = t("preset_rain_label", lang)
    if st.button(f"🌧️ {q2_label}", key="btn_preset_rain", use_container_width=True):
        st.session_state["preset_active"] = "rain"

    if st.session_state.get("preset_active") == "rain":
        with st.container():
            st.markdown(
                f"<div style='background:#f0f4f8; border-radius:0.6rem; "
                f"padding:0.7rem 1rem; margin-bottom:0.6rem; font-size:0.95rem;'>"
                f"<strong>{t('you_asked', lang)}</strong> {q2_label}</div>",
                unsafe_allow_html=True,
            )
            if results is None:
                st.warning(t("preset_missing_rain", lang))
            else:
                answer = answer_rain_fails(
                    results=results,
                    df_yield_price=df_yield_price,
                    df_msp=df_msp,
                    t_fn=lambda key: t(key, lang),
                )
                if answer is None:
                    st.warning(t("preset_missing_rain", lang))
                else:
                    st.markdown(
                        f"<div style='background:#fff; border:1px solid #ddd; "
                        f"border-radius:0.6rem; padding:0.7rem 1rem; "
                        f"font-size:0.95rem; line-height:1.5;'>"
                        f"{answer}</div>",
                        unsafe_allow_html=True,
                    )
                    render_speaker_button(
                        text=answer,
                        lang=lang,
                        button_key="tts_preset_rain",
                    )

    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # Q3 — Is moneylender worth it?
    # -----------------------------------------------------------------------
    q3_label = t("preset_moneylender_label", lang)
    if st.button(f"💰 {q3_label}", key="btn_preset_ml", use_container_width=True):
        st.session_state["preset_active"] = "moneylender"

    if st.session_state.get("preset_active") == "moneylender":
        with st.container():
            st.markdown(
                f"<div style='background:#f0f4f8; border-radius:0.6rem; "
                f"padding:0.7rem 1rem; margin-bottom:0.6rem; font-size:0.95rem;'>"
                f"<strong>{t('you_asked', lang)}</strong> {q3_label}</div>",
                unsafe_allow_html=True,
            )
            if results is None:
                st.warning(t("preset_missing_moneylender", lang))
            else:
                answer = answer_moneylender_worth_it(
                    results=results,
                    df_cost=df_cost,
                    t_fn=lambda key: t(key, lang),
                )
                if answer is None:
                    st.warning(t("preset_missing_moneylender", lang))
                else:
                    st.markdown(
                        f"<div style='background:#fff; border:1px solid #ddd; "
                        f"border-radius:0.6rem; padding:0.7rem 1rem; "
                        f"font-size:0.95rem; line-height:1.5;'>"
                        f"{answer}</div>",
                        unsafe_allow_html=True,
                    )
                    render_speaker_button(
                        text=answer,
                        lang=lang,
                        button_key="tts_preset_moneylender",
                    )
