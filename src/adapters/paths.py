from __future__ import annotations

import re


UNSAFE_FILENAME_CHARACTERS = re.compile(r"[^A-Za-z0-9._-]+")


def safe_identifier(value: str) -> str:
    normalized = UNSAFE_FILENAME_CHARACTERS.sub("_", value).strip("._-")
    return normalized or "request"
