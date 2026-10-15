from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from src.agreement_readiness import evaluate_agreement_readiness
from src.eligibility import evaluate_eligibility
from src.template_selector import evaluate_template_selection


DISCLAIMER = (
    "This local proof of concept is not legal approval, does not authorize a "
    "transfer, and is not connected to eRPM."
)


def build_screening_report(request: Mapping[str, Any]) -> dict[str, Any]:
    eligibility = evaluate_eligibility(request)
    return {
        "proof_of_concept": True,
        "disclaimer": DISCLAIMER,
        "eligibility": eligibility,
        "agreement_readiness": evaluate_agreement_readiness(request),
        "template_selection": evaluate_template_selection(request, eligibility),
    }


def serialize_screening_report(report: Mapping[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
