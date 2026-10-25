"""Compatibility facade for agreement template selection."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.templates.selector import select_template


def evaluate_template_selection(
    request: Mapping[str, Any], eligibility_result: Mapping[str, Any]
) -> dict[str, Any]:
    return select_template(request, eligibility_result)
