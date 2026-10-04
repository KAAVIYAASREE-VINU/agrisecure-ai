"""
ui/speaker_button.py — AgriSecure AI
======================================

A reusable 🔊 speaker button that speaks a given text via TTS and falls
back gracefully to a localised text notice when audio is unavailable.

Public API
----------
render_speaker_button(text, lang, button_key)
    Render a 🔊 button.  On click, calls voice.tts.speak() and either
    plays the audio with st.audio() or shows t("tts_failed_notice").
    The source *text* is always visible regardless of TTS outcome.

Design decisions
----------------
- The original text is always shown so the farmer can always read it.
- st.audio() is called with format="audio/mp3" matching gTTS output.
- A spinner (t("tts_loading")) is shown while synthesis is in progress.
- On failure the farmer sees t("tts_failed_notice") as a caption below
  the text — never a hard error.

Requirements: 14
"""

from __future__ import annotations

import streamlit as st

from ui.i18n import t


def render_speaker_button(
    text: str,
    lang: str,
    button_key: str,
) -> None:
    """Render a 🔊 button that speaks *text* in *lang*.

    The original *text* is always displayed above the button so the farmer
    can read it regardless of whether TTS succeeds.

    Parameters
    ----------
    text : str
        The human-readable text to display and optionally speak.
    lang : str
        Language code (``"en"``, ``"ta"``, or ``"hi"``).
    button_key : str
        A unique Streamlit widget key for this button instance.
    """
    # Always show the text so the farmer can read it
    st.markdown(
        f"<div style='font-size:0.95rem; line-height:1.5; margin-bottom:0.4rem;'>"
        f"{text}</div>",
        unsafe_allow_html=True,
    )

    # Speaker button
    if st.button(
        t("tts_button_label", lang),
        key=button_key,
        use_container_width=True,
    ):
        with st.spinner(t("tts_loading", lang)):
            from voice.tts import speak
            audio_bytes = speak(text, lang)

        if audio_bytes is not None:
            st.audio(audio_bytes, format="audio/mp3")
        else:
            st.caption(t("tts_failed_notice", lang))
