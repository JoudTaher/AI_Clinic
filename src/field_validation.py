from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def email_error(value: Any, label: str) -> str | None:
    """Return a user-facing syntax error for a non-empty email value."""
    if not isinstance(value, str) or not value.strip():
        return None
    if EMAIL_PATTERN.fullmatch(value.strip()) is None:
        return f"Enter a valid {label}."
    return None


def email_errors(
    information: Mapping[str, Any], field_labels: Mapping[str, str]
) -> dict[str, str]:
    errors: dict[str, str] = {}
    for field_id, label in field_labels.items():
        error = email_error(information.get(field_id), label)
        if error is not None:
            errors[field_id] = error
    return errors
