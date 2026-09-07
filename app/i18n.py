from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.config import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES

LOCALES_DIR = Path(__file__).parent / "locales"


@lru_cache(maxsize=None)
def _load_locale(lang: str) -> dict:
    path = LOCALES_DIR / f"{lang}.json"
    if not path.exists():
        path = LOCALES_DIR / f"{DEFAULT_LANGUAGE}.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_language(lang: str | None) -> str:
    if lang and lang.lower() in SUPPORTED_LANGUAGES:
        return lang.lower()
    return DEFAULT_LANGUAGE


def get_dictionary(lang: str) -> dict:
    return _load_locale(normalize_language(lang))


def translate(lang: str, key: str, **kwargs) -> str:
    dictionary = get_dictionary(lang)
    template = dictionary.get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError):
            return template
    return template


def get_direction(lang: str) -> str:
    return SUPPORTED_LANGUAGES.get(normalize_language(lang), {}).get("dir", "ltr")
