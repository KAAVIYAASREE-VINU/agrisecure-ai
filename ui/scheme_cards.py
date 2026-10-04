"""
ui/scheme_cards.py — AgriSecure AI
====================================

Renders one card per government scheme (KCC, PM-KISAN, PMFBY).
Cards show: name, benefit, eligibility points, documents needed, where to
apply — all from the language file via t().

When a farmer's land or crop makes a scheme ineligible the card is greyed
with a one-sentence ineligibility reason from the language file.

A "Learn More" link (URL from config.py) opens in a new tab.  The link is
hidden if the URL is missing or empty.  Any missing text field shows
"PLACEHOLDER – verify" as per project rules.

Requirements: 11 (Government Schemes panel)
"""

from __future__ import annotations

import streamlit as st

from ui.i18n import t
from config import get_config
from core.schemes import (
    check_kcc_eligibility,
    check_pmkisan_eligibility,
    check_pmfby_eligibility,
)

# ---------------------------------------------------------------------------
# Scheme definitions — all text keys come from lang/*.json
# ---------------------------------------------------------------------------

_PLACEHOLDER = "PLACEHOLDER – verify"


def _safe_t(key: str, lang: str) -> str:
    """Return t(key, lang), substituting PLACEHOLDER if the key is absent."""
    val = t(key, lang)
    # t() returns "[{key}]" for truly missing keys
    if val.startswith("[") and val.endswith("]"):
        return _PLACEHOLDER
    return val


def _scheme_card(
    *,
    lang: str,
    name_key: str,
    benefit_key: str,
    eligibility_keys: list[str],
    documents_key: str,
    where_key: str,
    learn_more_label_key: str,
    verify_note_key: str,
    eligible: bool,
    reason_key: str,
    url: str,
) -> None:
    """Render a single scheme card.

    Parameters
    ----------
    lang:
        Active language code.
    name_key, benefit_key, documents_key, where_key, …:
        i18n keys for each text field.
    eligibility_keys:
        List of i18n keys for eligibility bullet points.
    eligible:
        Whether the farmer is eligible.  Ineligible cards are visually greyed.
    reason_key:
        i18n key for the eligibility result sentence (shown below the name).
    url:
        "Learn More" URL from config.py; hidden when empty/None.
    """
    name = _safe_t(name_key, lang)
    benefit = _safe_t(benefit_key, lang)
    documents = _safe_t(documents_key, lang)
    where_to_apply = _safe_t(where_key, lang)
    learn_more_label = _safe_t(learn_more_label_key, lang)
    verify_note = _safe_t(verify_note_key, lang)
    reason = _safe_t(reason_key, lang)

    eligibility_points = [_safe_t(k, lang) for k in eligibility_keys]

    # Visual style: grey out card when ineligible
    if eligible:
        border_color = "#2e7d32"
        bg_color = "#f6ffed"
        name_color = "#1e8449"
        status_icon = "✅"
        opacity = "1"
    else:
        border_color = "#bbb"
        bg_color = "#f5f5f5"
        name_color = "#888"
        status_icon = "🚫"
        opacity = "0.6"

    # Build eligibility bullet list HTML
    bullets_html = "".join(
        f"<li style='font-size:0.85rem; margin-bottom:0.2rem;'>{point}</li>"
        for point in eligibility_points
    )

    # Build "Learn more" link HTML (hidden if URL is missing/empty)
    learn_more_html = ""
    if url and url.strip():
        learn_more_html = (
            f"<a href='{url}' target='_blank' rel='noopener noreferrer' "
            f"style='display:inline-block; margin-top:0.5rem; font-size:0.85rem; "
            f"font-weight:600; color:#1a5276; text-decoration:none; "
            f"border:1px solid #1a5276; border-radius:0.4rem; "
            f"padding:0.2rem 0.6rem;'>"
            f"{learn_more_label}"
            f"</a>"
        )

    st.markdown(
        f"""
        <div style="
            border: 2px solid {border_color};
            background: {bg_color};
            border-radius: 0.8rem;
            padding: 0.9rem 1rem;
            margin-bottom: 0.8rem;
            opacity: {opacity};
        ">
            <div style="font-size:1.05rem; font-weight:700; color:{name_color};
                        margin-bottom:0.3rem;">
                {status_icon} {name}
            </div>

            <div style="font-size:0.88rem; color:#555; margin-bottom:0.5rem;
                        font-style:italic;">
                {reason}
            </div>

            <div style="font-size:0.9rem; font-weight:600; margin-bottom:0.3rem;">
                {benefit}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Use an expander for the detail rows (always shown but collapsed by default)
    # — keeps the card compact on mobile while allowing the user to expand
    with st.expander(f"📋 {name} — " + t("scheme_card_verify", lang).replace("⚠ ", "")):
        # Eligibility points
        st.markdown("**Eligibility**")
        st.markdown(f"<ul>{bullets_html}</ul>", unsafe_allow_html=True)

        # Documents
        st.markdown("**Documents needed**")
        st.write(documents)

        # Where to apply
        st.markdown("**Where to apply**")
        st.write(where_to_apply)

        # Verify note
        st.caption(verify_note)

        # Learn more link
        if learn_more_html:
            st.markdown(learn_more_html, unsafe_allow_html=True)

    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_scheme_cards(
    acres: float,
    crop: str,
    season: str,
    lang: str,
) -> None:
    """Render the Government Schemes panel (Requirement 11).

    Shows one card each for KCC, PM-KISAN, and PMFBY.  Eligibility is
    determined by the core/schemes.py functions; ineligible cards are greyed
    with the reason from the language file.

    Parameters
    ----------
    acres:
        Farmer's land size in acres.
    crop:
        Crop name (used by PMFBY eligibility check).
    season:
        Season name (used by PMFBY eligibility check).
    lang:
        Active language code (``"en"``, ``"ta"``, or ``"hi"``).
    """
    st.markdown(
        f"<h3 style='font-size:1.1rem; margin-bottom:0.6rem;'>"
        f"🏛️ {t('schemes_header', lang)}</h3>",
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # KCC
    # ------------------------------------------------------------------
    kcc_result = check_kcc_eligibility(acres=acres, crop=crop)
    _scheme_card(
        lang=lang,
        name_key="scheme_kcc_name",
        benefit_key="scheme_kcc_benefit",
        eligibility_keys=[
            "scheme_kcc_eligibility_1",
            "scheme_kcc_eligibility_2",
            "scheme_kcc_eligibility_3",
        ],
        documents_key="scheme_kcc_documents",
        where_key="scheme_kcc_where_to_apply",
        learn_more_label_key="scheme_card_learn_more",
        verify_note_key="scheme_kcc_verify_note",
        eligible=kcc_result["eligible"],
        reason_key=kcc_result["reason"],
        url=_safe_url("SCHEME_KCC_URL"),
    )

    # ------------------------------------------------------------------
    # PM-KISAN
    # ------------------------------------------------------------------
    pmkisan_result = check_pmkisan_eligibility(acres=acres)
    _scheme_card(
        lang=lang,
        name_key="scheme_pmkisan_name",
        benefit_key="scheme_pmkisan_benefit",
        eligibility_keys=[
            "scheme_pmkisan_eligibility_1",
            "scheme_pmkisan_eligibility_2",
            "scheme_pmkisan_eligibility_3",
        ],
        documents_key="scheme_pmkisan_documents",
        where_key="scheme_pmkisan_where_to_apply",
        learn_more_label_key="scheme_card_learn_more",
        verify_note_key="scheme_pmkisan_verify_note",
        eligible=pmkisan_result["eligible"],
        reason_key=pmkisan_result["reason"],
        url=_safe_url("SCHEME_PMKISAN_URL"),
    )

    # ------------------------------------------------------------------
    # PMFBY
    # ------------------------------------------------------------------
    pmfby_result = check_pmfby_eligibility(crop=crop, season=season)
    _scheme_card(
        lang=lang,
        name_key="scheme_pmfby_name",
        benefit_key="scheme_pmfby_benefit",
        eligibility_keys=[
            "scheme_pmfby_eligibility_1",
            "scheme_pmfby_eligibility_2",
            "scheme_pmfby_eligibility_3",
        ],
        documents_key="scheme_pmfby_documents",
        where_key="scheme_pmfby_where_to_apply",
        learn_more_label_key="scheme_card_learn_more",
        verify_note_key="scheme_pmfby_verify_note",
        eligible=pmfby_result["eligible"],
        reason_key=pmfby_result["reason"],
        url=_safe_url("SCHEME_PMFBY_URL"),
    )

    # Verify notice footer
    st.caption(t("scheme_card_verify", lang))


def _safe_url(config_key: str) -> str:
    """Return the URL from config, or empty string on any error."""
    try:
        url = get_config(config_key)
        return str(url) if url else ""
    except Exception:
        return ""
