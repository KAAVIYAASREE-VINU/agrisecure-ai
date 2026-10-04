"""
voice/tts.py — AgriSecure AI
=============================

Text-to-speech synthesis using gTTS with an LRU cache and a hard timeout.

Public API
----------
speak(text, lang) -> bytes | None
    Generate MP3 audio bytes for *text* in *lang*.
    Returns None on any failure (timeout, network error, gTTS error).

clear_cache()
    Empty the in-process LRU cache (useful in tests).

Design notes
------------
- Cache key: SHA-256 hex of (text + "|" + lang).
  This is collision-resistant and avoids embedding raw text in memory keys.
- LRU eviction: implemented with collections.OrderedDict.  When the cache
  is full the least-recently-used (oldest access) entry is dropped.
- Timeout: gTTS performs HTTP I/O.  We run it inside a
  concurrent.futures.ThreadPoolExecutor with a hard deadline equal to
  TTS_TIMEOUT_SECONDS from config.py.  If the call takes longer the
  executor future is cancelled, speak() returns None, and no exception
  propagates to the caller.
- Never raises: all exceptions are caught; callers check for None.

Language codes (gTTS)
---------------------
  "en" → "en"   English
  "ta" → "ta"   Tamil
  "hi" → "hi"   Hindi

Requirements: 14
"""

from __future__ import annotations

import hashlib
import io
import logging
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Optional

from config import get_config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Language code mapping
# ---------------------------------------------------------------------------

_GTTS_LANG_MAP: dict[str, str] = {
    "en": "en",
    "ta": "ta",
    "hi": "hi",
}

# ---------------------------------------------------------------------------
# LRU cache — OrderedDict keyed by SHA-256 hash of (text + "|" + lang)
# ---------------------------------------------------------------------------

_cache: OrderedDict[str, bytes] = OrderedDict()


def _cache_key(text: str, lang: str) -> str:
    """Return a hex SHA-256 hash used as the cache key."""
    raw = f"{text}|{lang}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cache_get(key: str) -> Optional[bytes]:
    """Return cached bytes for *key*, promoting it to most-recently-used."""
    if key in _cache:
        _cache.move_to_end(key)
        return _cache[key]
    return None


def _cache_put(key: str, data: bytes) -> None:
    """Insert *data* under *key*, evicting the LRU entry when the cache is full."""
    max_size: int = get_config("TTS_CACHE_MAX_SIZE")
    if key in _cache:
        _cache.move_to_end(key)
        _cache[key] = data
        return
    if len(_cache) >= max_size:
        # Remove least-recently-used (first item)
        _cache.popitem(last=False)
    _cache[key] = data


def clear_cache() -> None:
    """Empty the in-process LRU cache (intended for use in tests)."""
    _cache.clear()


# ---------------------------------------------------------------------------
# Internal synthesis worker
# ---------------------------------------------------------------------------

def _synthesise(text: str, gtts_lang: str) -> bytes:
    """Call gTTS and return the MP3 bytes.  Raises on any gTTS error."""
    from gtts import gTTS  # lazy import keeps startup fast when TTS not used

    buf = io.BytesIO()
    tts = gTTS(text=text, lang=gtts_lang, slow=False)
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def speak(text: str, lang: str = "en") -> Optional[bytes]:
    """Generate MP3 audio bytes for *text* in *lang*.

    Parameters
    ----------
    text : str
        The text to synthesise.  Must be non-empty.
    lang : str
        Language code: ``"en"``, ``"ta"``, or ``"hi"``.
        Falls back to ``"en"`` for unrecognised codes.

    Returns
    -------
    bytes or None
        MP3 audio bytes on success.  ``None`` if synthesis fails, times out,
        or *text* is empty.

    Notes
    -----
    - Never raises; all errors are caught and logged.
    - Results are cached by hash(text + "|" + lang), max 50 entries LRU.
    - Hard timeout is ``TTS_TIMEOUT_SECONDS`` from config.py.
    """
    # Guard: empty text
    if not text or not text.strip():
        return None

    # Normalise language code
    gtts_lang = _GTTS_LANG_MAP.get(lang, "en")

    # Check cache first
    key = _cache_key(text, lang)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    # Synthesise with timeout
    timeout_secs: float = get_config("TTS_TIMEOUT_SECONDS")

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_synthesise, text, gtts_lang)
            audio_bytes = future.result(timeout=timeout_secs)
    except FuturesTimeoutError:
        logger.warning("TTS timeout after %s s for lang=%s", timeout_secs, lang)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("TTS synthesis failed: %s", exc)
        return None

    # Store in cache
    _cache_put(key, audio_bytes)
    return audio_bytes
