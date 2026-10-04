"""
tests/test_tts.py — AgriSecure AI
====================================

Unit tests for voice/tts.py.

Covers
------
1. Language code mapping — speak() passes the correct gTTS lang code.
2. Cache hit — calling speak() twice with the same input returns identical bytes
   without calling _synthesise a second time.
3. Cache miss — different inputs produce different cache entries.
4. Timeout fallback — when synthesis exceeds TTS_TIMEOUT_SECONDS, speak()
   returns None without raising.
5. gTTS error fallback — when _synthesise raises, speak() returns None without raising.
6. Empty text — speak("") returns None immediately.
7. Cache eviction (LRU) — adding more entries than TTS_CACHE_MAX_SIZE evicts
   the least-recently-used entry.
8. None-safe — speak() with an unsupported lang code falls back to "en" and
   still returns bytes (or None on network failure) without raising.

All external I/O is mocked via voice.tts._synthesise so tests run offline
and deterministically.
"""

from __future__ import annotations

import concurrent.futures
from unittest.mock import MagicMock, patch, call

import pytest

import voice.tts as tts_module
from voice.tts import speak, clear_cache, _cache, _cache_key, _GTTS_LANG_MAP


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_MP3 = b"ID3\x00\x00FAKE_AUDIO_BYTES"  # deterministic fake MP3 payload


def _fake_synthesise(text: str, gtts_lang: str) -> bytes:
    """Stand-in for _synthesise that returns FAKE_MP3 instantly."""
    return FAKE_MP3


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def fresh_cache():
    """Clear the TTS LRU cache before and after every test."""
    clear_cache()
    yield
    clear_cache()


# ---------------------------------------------------------------------------
# 1. Language code mapping
# ---------------------------------------------------------------------------

class TestLanguageCodeMapping:
    """speak() should pass the correct gTTS lang code to _synthesise."""

    @pytest.mark.parametrize("lang,expected_gtts", [
        ("en", "en"),
        ("ta", "ta"),
        ("hi", "hi"),
    ])
    def test_known_lang_codes(self, lang, expected_gtts):
        """speak() calls _synthesise with the mapped gTTS lang code."""
        mock_synth = MagicMock(return_value=FAKE_MP3)
        with patch.object(tts_module, "_synthesise", mock_synth):
            result = speak("hello", lang)

        assert result == FAKE_MP3
        mock_synth.assert_called_once()
        _, actual_gtts_lang = mock_synth.call_args.args
        assert actual_gtts_lang == expected_gtts

    def test_unknown_lang_falls_back_to_en(self):
        """An unrecognised lang code should silently map to 'en', not raise."""
        mock_synth = MagicMock(return_value=FAKE_MP3)
        with patch.object(tts_module, "_synthesise", mock_synth):
            result = speak("hello", "xx")

        assert result == FAKE_MP3
        _, actual_gtts_lang = mock_synth.call_args.args
        assert actual_gtts_lang == "en"

    def test_lang_map_completeness(self):
        """All three supported language codes must be present in the mapping."""
        for code in ("en", "ta", "hi"):
            assert code in _GTTS_LANG_MAP
            assert _GTTS_LANG_MAP[code] == code  # identity mapping for all three


# ---------------------------------------------------------------------------
# 2 & 3. Cache behaviour
# ---------------------------------------------------------------------------

class TestCacheBehaviour:
    def test_cache_hit_same_bytes(self):
        """Second call with the same (text, lang) must return identical bytes
        without calling _synthesise again."""
        mock_synth = MagicMock(return_value=FAKE_MP3)
        with patch.object(tts_module, "_synthesise", mock_synth):
            first = speak("test text", "en")
            second = speak("test text", "en")

        assert first == second == FAKE_MP3
        # _synthesise should have been called only once
        assert mock_synth.call_count == 1

    def test_cache_miss_different_text(self):
        """Different text strings must each call _synthesise."""
        mock_synth = MagicMock(return_value=FAKE_MP3)
        with patch.object(tts_module, "_synthesise", mock_synth):
            speak("text A", "en")
            speak("text B", "en")

        assert mock_synth.call_count == 2

    def test_cache_miss_different_lang(self):
        """Same text but different lang must each call _synthesise."""
        mock_synth = MagicMock(return_value=FAKE_MP3)
        with patch.object(tts_module, "_synthesise", mock_synth):
            speak("paddy", "en")
            speak("paddy", "ta")

        assert mock_synth.call_count == 2

    def test_cache_key_includes_lang(self):
        """Cache keys for the same text in different languages must differ."""
        key_en = _cache_key("rice", "en")
        key_ta = _cache_key("rice", "ta")
        key_hi = _cache_key("rice", "hi")
        assert len({key_en, key_ta, key_hi}) == 3

    def test_cache_key_same_text_same_lang(self):
        """Cache key is deterministic for the same (text, lang)."""
        assert _cache_key("wheat", "hi") == _cache_key("wheat", "hi")

    def test_cached_bytes_are_stored(self):
        """After speak(), the result should be findable in the cache."""
        mock_synth = MagicMock(return_value=FAKE_MP3)
        with patch.object(tts_module, "_synthesise", mock_synth):
            speak("cache me", "en")

        key = _cache_key("cache me", "en")
        assert key in _cache
        assert _cache[key] == FAKE_MP3


# ---------------------------------------------------------------------------
# 4. Timeout fallback
# ---------------------------------------------------------------------------

class TestTimeoutFallback:
    def test_returns_none_on_timeout(self):
        """speak() must return None (not raise) when synthesis times out."""
        with patch.object(
            tts_module, "_synthesise",
            side_effect=concurrent.futures.TimeoutError()
        ):
            result = speak("this will time out", "en")

        assert result is None

    def test_timeout_does_not_populate_cache(self):
        """A timeout must not leave a partial entry in the cache."""
        with patch.object(
            tts_module, "_synthesise",
            side_effect=concurrent.futures.TimeoutError()
        ):
            speak("slow text", "en")

        assert len(_cache) == 0

    def test_timeout_does_not_raise(self):
        """TimeoutError must be swallowed — speak() should never raise."""
        with patch.object(
            tts_module, "_synthesise",
            side_effect=concurrent.futures.TimeoutError()
        ):
            try:
                speak("no raise please", "en")
            except Exception as exc:
                pytest.fail(f"speak() raised unexpectedly: {exc}")


# ---------------------------------------------------------------------------
# 5. gTTS error fallback
# ---------------------------------------------------------------------------

class TestGTTSErrorFallback:
    def test_returns_none_on_synthesis_error(self):
        """speak() must return None when _synthesise raises any exception."""
        with patch.object(
            tts_module, "_synthesise",
            side_effect=Exception("connection refused")
        ):
            result = speak("will fail", "en")

        assert result is None

    def test_error_does_not_populate_cache(self):
        """A synthesis error must not leave an entry in the cache."""
        with patch.object(
            tts_module, "_synthesise",
            side_effect=Exception("connection refused")
        ):
            speak("error text", "en")

        assert len(_cache) == 0

    def test_error_does_not_raise(self):
        """Any exception inside synthesis must be swallowed."""
        with patch.object(
            tts_module, "_synthesise",
            side_effect=RuntimeError("unexpected")
        ):
            try:
                speak("quiet failure", "en")
            except Exception as exc:
                pytest.fail(f"speak() raised unexpectedly: {exc}")


# ---------------------------------------------------------------------------
# 6. Empty text guard
# ---------------------------------------------------------------------------

class TestEmptyTextGuard:
    def test_empty_string_returns_none(self):
        assert speak("", "en") is None

    def test_whitespace_only_returns_none(self):
        assert speak("   ", "en") is None

    def test_empty_text_does_not_call_synthesise(self):
        mock_synth = MagicMock(return_value=FAKE_MP3)
        with patch.object(tts_module, "_synthesise", mock_synth):
            speak("", "en")
        mock_synth.assert_not_called()


# ---------------------------------------------------------------------------
# 7. LRU cache eviction
# ---------------------------------------------------------------------------

class TestLRUCacheEviction:
    def test_lru_eviction_drops_oldest_when_full(self):
        """When the cache is full, the least-recently-used entry is evicted."""
        from config import get_config
        max_size = get_config("TTS_CACHE_MAX_SIZE")

        mock_synth = MagicMock(return_value=FAKE_MP3)
        with patch.object(tts_module, "_synthesise", mock_synth):
            first_text = "lru_text_0"
            speak(first_text, "en")  # this will be the LRU entry

            for i in range(1, max_size):
                speak(f"lru_text_{i}", "en")

        assert len(_cache) == max_size
        first_key = _cache_key(first_text, "en")
        assert first_key in _cache  # still present, not yet evicted

        # Adding one more entry should evict the first (LRU) entry
        mock_synth2 = MagicMock(return_value=FAKE_MP3)
        with patch.object(tts_module, "_synthesise", mock_synth2):
            speak("lru_overflow_entry", "en")

        assert len(_cache) == max_size  # size unchanged
        assert first_key not in _cache  # LRU entry was evicted

    def test_cache_size_does_not_exceed_max(self):
        """The cache must never grow beyond TTS_CACHE_MAX_SIZE entries."""
        from config import get_config
        max_size = get_config("TTS_CACHE_MAX_SIZE")

        mock_synth = MagicMock(return_value=FAKE_MP3)
        with patch.object(tts_module, "_synthesise", mock_synth):
            for i in range(max_size + 10):
                speak(f"overflow_text_{i}", "en")

        assert len(_cache) <= max_size

    def test_access_promotes_to_mru(self):
        """Accessing a cached entry should move it to most-recently-used position."""
        from config import get_config
        max_size = get_config("TTS_CACHE_MAX_SIZE")

        mock_synth = MagicMock(return_value=FAKE_MP3)
        with patch.object(tts_module, "_synthesise", mock_synth):
            promoted_text = "promoted_text"
            speak(promoted_text, "en")  # inserted, becomes LRU

            for i in range(1, max_size):
                speak(f"filler_{i}", "en")

        # Access the first entry — this promotes it to MRU
        promoted_key = _cache_key(promoted_text, "en")
        assert promoted_key in _cache
        tts_module._cache_get(promoted_key)  # promotes it

        # The second entry (filler_1) is now the LRU; overflow evicts it
        mock_synth2 = MagicMock(return_value=FAKE_MP3)
        with patch.object(tts_module, "_synthesise", mock_synth2):
            speak("another_overflow", "en")

        assert promoted_key in _cache  # promoted entry survives
        filler_key = _cache_key("filler_1", "en")
        assert filler_key not in _cache  # actual LRU was evicted
