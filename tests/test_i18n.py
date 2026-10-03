"""Tests for ui/i18n.py — translation lookup, fallback, and key parity."""

import json
import warnings
from pathlib import Path

import pytest

from ui.i18n import load_lang, t, _LANG_CACHE, SUPPORTED_LANGS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LANG_DIR = PROJECT_ROOT / "lang"


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the in-process language cache before every test."""
    _LANG_CACHE.clear()
    yield
    _LANG_CACHE.clear()


# ---------------------------------------------------------------------------
# load_lang
# ---------------------------------------------------------------------------

class TestLoadLang:
    def test_returns_dict_for_en(self):
        data = load_lang("en")
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_returns_dict_for_ta(self):
        data = load_lang("ta")
        assert isinstance(data, dict)

    def test_returns_dict_for_hi(self):
        data = load_lang("hi")
        assert isinstance(data, dict)

    def test_caches_result(self):
        d1 = load_lang("en")
        d2 = load_lang("en")
        assert d1 is d2  # same object from cache

    def test_raises_for_unknown_lang(self):
        with pytest.raises(ValueError, match="Unknown language code"):
            load_lang("fr")

    def test_raises_file_not_found_if_file_missing(self, tmp_path, monkeypatch):
        """Simulate a supported lang code whose file has been removed."""
        import ui.i18n as i18n_mod
        monkeypatch.setattr(i18n_mod, "_LANG_DIR", tmp_path)
        with pytest.raises(FileNotFoundError):
            load_lang("en")


# ---------------------------------------------------------------------------
# t() — normal lookups
# ---------------------------------------------------------------------------

class TestTNormalLookup:
    def test_english_app_title(self):
        assert t("app_title", "en") == "AgriSecure AI"

    def test_tamil_app_title(self):
        assert t("app_title", "ta") == "AgriSecure AI"

    def test_hindi_app_title(self):
        assert t("app_title", "hi") == "AgriSecure AI"

    def test_english_subtitle(self):
        result = t("app_subtitle", "en")
        assert "farmer" in result.lower() or len(result) > 0

    def test_tamil_subtitle_differs_from_english(self):
        en_val = t("app_subtitle", "en")
        ta_val = t("app_subtitle", "ta")
        # Tamil subtitle should be a different string (localised)
        assert ta_val != en_val

    def test_hindi_subtitle_differs_from_english(self):
        en_val = t("app_subtitle", "en")
        hi_val = t("app_subtitle", "hi")
        assert hi_val != en_val

    def test_default_lang_is_english(self):
        assert t("app_title") == t("app_title", "en")


# ---------------------------------------------------------------------------
# t() — fallback behaviour
# ---------------------------------------------------------------------------

class TestTFallback:
    def test_missing_key_in_ta_falls_back_to_english(self, monkeypatch):
        """Patch ta dict to remove a key; confirm fallback to English."""
        ta_data = load_lang("ta").copy()
        ta_data.pop("app_title", None)
        monkeypatch.setitem(_LANG_CACHE, "ta", ta_data)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = t("app_title", "ta")

        # Should have returned the English value
        assert result == "AgriSecure AI"
        # Should have emitted at least one warning about the missing key
        messages = [str(w.message) for w in caught]
        assert any("app_title" in m and "ta" in m for m in messages)

    def test_missing_key_in_hi_falls_back_to_english(self, monkeypatch):
        hi_data = load_lang("hi").copy()
        hi_data.pop("btn_calculate", None)
        monkeypatch.setitem(_LANG_CACHE, "hi", hi_data)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = t("btn_calculate", "hi")

        en_value = load_lang("en")["btn_calculate"]
        assert result == en_value
        messages = [str(w.message) for w in caught]
        assert any("btn_calculate" in m for m in messages)

    def test_missing_key_in_english_returns_bracketed_key(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = t("nonexistent_key", "en")

        assert result == "[nonexistent_key]"
        messages = [str(w.message) for w in caught]
        assert any("nonexistent_key" in m for m in messages)

    def test_missing_key_everywhere_returns_bracketed_key(self, monkeypatch):
        """Key absent from both ta and en should return '[key]'."""
        ta_data = load_lang("ta").copy()
        en_data = load_lang("en").copy()
        ta_data.pop("app_title", None)
        en_data.pop("app_title", None)
        monkeypatch.setitem(_LANG_CACHE, "ta", ta_data)
        monkeypatch.setitem(_LANG_CACHE, "en", en_data)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = t("app_title", "ta")

        assert result == "[app_title]"
        messages = [str(w.message) for w in caught]
        assert any("app_title" in m for m in messages)


# ---------------------------------------------------------------------------
# t() — unknown language code
# ---------------------------------------------------------------------------

class TestTUnknownLang:
    def test_unknown_lang_falls_back_to_english(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = t("app_title", "de")  # German — not supported

        assert result == "AgriSecure AI"
        messages = [str(w.message) for w in caught]
        assert any("de" in m for m in messages)

    def test_unknown_lang_with_missing_key_returns_bracketed(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = t("no_such_key", "zz")

        assert result == "[no_such_key]"


# ---------------------------------------------------------------------------
# Key parity: ta.json and hi.json must cover every key in en.json
# ---------------------------------------------------------------------------

class TestKeyParity:
    def _load_json(self, lang_code: str) -> dict:
        path = LANG_DIR / f"{lang_code}.json"
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)

    def test_ta_has_all_english_keys(self):
        en_keys = set(self._load_json("en").keys())
        ta_keys = set(self._load_json("ta").keys())
        missing = en_keys - ta_keys
        assert not missing, f"Keys missing from ta.json: {sorted(missing)}"

    def test_hi_has_all_english_keys(self):
        en_keys = set(self._load_json("en").keys())
        hi_keys = set(self._load_json("hi").keys())
        missing = en_keys - hi_keys
        assert not missing, f"Keys missing from hi.json: {sorted(missing)}"

    def test_no_extra_keys_in_ta(self):
        """ta.json should not contain keys absent from en.json (keep parity clean)."""
        en_keys = set(self._load_json("en").keys())
        ta_keys = set(self._load_json("ta").keys())
        extra = ta_keys - en_keys
        assert not extra, f"Extra keys in ta.json not in en.json: {sorted(extra)}"

    def test_no_extra_keys_in_hi(self):
        en_keys = set(self._load_json("en").keys())
        hi_keys = set(self._load_json("hi").keys())
        extra = hi_keys - en_keys
        assert not extra, f"Extra keys in hi.json not in en.json: {sorted(extra)}"
