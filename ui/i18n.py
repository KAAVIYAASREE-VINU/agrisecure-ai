"""
Internationalisation helpers for AgriSecure AI.

Deliberately does NOT import streamlit so the module is testable in isolation.
"""

import json
import warnings
from pathlib import Path

# Cache: lang_code -> dict
_LANG_CACHE: dict[str, dict] = {}

# Resolve the project root once (two levels up from this file: ui/ -> project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LANG_DIR = _PROJECT_ROOT / "lang"

SUPPORTED_LANGS = ("en", "ta", "hi")


def load_lang(lang_code: str) -> dict:
    """Load and cache the JSON translation file for *lang_code*.

    Parameters
    ----------
    lang_code:
        One of ``"en"``, ``"ta"``, or ``"hi"``.

    Returns
    -------
    dict
        Mapping of translation keys to translated strings.

    Raises
    ------
    FileNotFoundError
        If the corresponding ``lang/{lang_code}.json`` file does not exist.
    ValueError
        If *lang_code* is not one of the recognised language codes.
    """
    if lang_code in _LANG_CACHE:
        return _LANG_CACHE[lang_code]

    if lang_code not in SUPPORTED_LANGS:
        raise ValueError(
            f"Unknown language code '{lang_code}'. "
            f"Supported codes: {SUPPORTED_LANGS}"
        )

    lang_file = _LANG_DIR / f"{lang_code}.json"
    if not lang_file.exists():
        raise FileNotFoundError(
            f"Translation file not found: {lang_file}"
        )

    with lang_file.open(encoding="utf-8") as fh:
        data = json.load(fh)

    _LANG_CACHE[lang_code] = data
    return data


def t(key: str, lang: str = "en") -> str:
    """Look up *key* in the specified language, falling back to English.

    Behaviour
    ---------
    1. If *lang* is valid and *key* exists in that language → return the value.
    2. If *key* is missing in *lang* (but *lang* is valid) → warn and fall back
       to the English value.
    3. If *key* is missing in English too → warn and return ``"[{key}]"``.
    4. If *lang* is unknown → warn and fall back to English (steps 1 or 3 apply
       from there).

    Parameters
    ----------
    key:
        The translation key to look up.
    lang:
        Language code (``"en"``, ``"ta"``, ``"hi"``). Defaults to ``"en"``.

    Returns
    -------
    str
        The translated string, the English fallback, or ``"[{key}]"`` if the
        key is absent from all languages.
    """
    # --- resolve requested language dict ---
    if lang not in SUPPORTED_LANGS:
        warnings.warn(
            f"i18n: unknown language code '{lang}'. Falling back to English.",
            stacklevel=2,
        )
        lang = "en"

    lang_dict = load_lang(lang)

    # --- happy path ---
    if key in lang_dict:
        return lang_dict[key]

    # --- missing in requested language: try English fallback ---
    if lang != "en":
        warnings.warn(
            f"i18n: key '{key}' missing in '{lang}'. Falling back to English.",
            stacklevel=2,
        )
        en_dict = load_lang("en")
        if key in en_dict:
            return en_dict[key]

    # --- missing everywhere ---
    warnings.warn(
        f"i18n: key '{key}' not found in any language. Returning '[{key}]'.",
        stacklevel=2,
    )
    return f"[{key}]"
