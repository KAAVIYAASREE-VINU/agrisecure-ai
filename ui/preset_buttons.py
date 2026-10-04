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

Requirements: 12 (preset question buttons, no LLM, <= 1 second response)
"""

import streamlit as st

from ui.i18n import t


def _render_question(
    *,
    lang: str,
    results,
    emoji: str,
    label_key: str,
    missing_key: str,
    button_key: str,
    tts_key: str,
    active_name: str,
    answer_fn,
) -> None:
    """Render one preset button and, if it is active, its answer.

    answer_fn is a zero-argument callable that returns the answer string,
    or None if the required results are not available yet.
    """
    from ui.speaker_button import render_speaker_button

    label = t(label_key, lang)

    if st.button(f"{emoji} {label}", key=button_key, use_container_width=True):
        st.session_state["preset_active"] = active_name

    if st.session_state.get("preset_active") != active_name:
        return

    with st.container():
        # Show the question the farmer asked
        st.markdown(
            "<div style='background:#f0f4f8; border-radius:0.6rem; "
            "padding:0.7rem 1rem; margin-bottom:0.6rem; font-size:0.95rem;'>"
            f"<strong>{t('you_asked', lang)}</strong> {label}</div>",
            unsafe_allow_html=True,
        )

        if results is None:
            st.warning(t(missing_key, lang))
            return

        answer = answer_fn()
        if answer is None:
            st.warning(t(missing_key, lang))
            return

        # Shows the answer text and the speaker button
        render_speaker_button(
            text=answer,
            lang=lang,
            button_key=tts_key,
        )


def render_preset_buttons(
    lang: str,
    *,
    df_yield_price,
    df_msp,
    df_cost,
) -> None:
    """Render the three preset question buttons with inline answers.

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

    results = st.session_state.get("results")

    def t_fn(key):
        return t(key, lang)

    # Section header
    st.markdown(
        "<h3 style='font-size:1.1rem; margin-bottom:0.4rem;'>"
        f"💬 {t('quick_questions_header', lang)}</h3>",
        unsafe_allow_html=True,
    )

    # Q1: Can I repay on time?
    _render_question(
        lang=lang,
        results=results,
        emoji="💳",
        label_key="preset_repay_label",
        missing_key="preset_missing_repay",
        button_key="btn_preset_repay",
        tts_key="tts_preset_repay",
        active_name="repay",
        answer_fn=lambda: answer_repay_on_time(
            results=results,
            df_yield_price=df_yield_price,
            df_msp=df_msp,
            df_cost=df_cost,
            t_fn=t_fn,
        ),
    )

    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    # Q2: What if rain fails?
    _render_question(
        lang=lang,
        results=results,
        emoji="🌧️",
        label_key="preset_rain_label",
        missing_key="preset_missing_rain",
        button_key="btn_preset_rain",
        tts_key="tts_preset_rain",
        active_name="rain",
        answer_fn=lambda: answer_rain_fails(
            results=results,
            df_yield_price=df_yield_price,
            df_msp=df_msp,
            t_fn=t_fn,
        ),
    )

    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

    # Q3: Is the moneylender worth it?
    _render_question(
        lang=lang,
        results=results,
        emoji="💰",
        label_key="preset_moneylender_label",
        missing_key="preset_missing_moneylender",
        button_key="btn_preset_ml",
        tts_key="tts_preset_moneylender",
        active_name="moneylender",
        answer_fn=lambda: answer_moneylender_worth_it(
            results=results,
            df_cost=df_cost,
            t_fn=t_fn,
        ),
    )