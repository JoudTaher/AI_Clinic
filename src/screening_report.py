from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from src.agreement_readiness import evaluate_agreement_readiness
from src.eligibility import evaluate_eligibility
from src.template_selector import evaluate_template_selection


DISCLAIMER = (
    "This proof of concept automatically processes only documented standard "
    "requests. It creates a local signing package and performs no live submission."
)

DELIVERY_POLICY = {
    "internal_approval_required": False,
    "delivery_mode": "signnow_package",
    "live_delivery_enabled": False,
    "nonstandard_route": "eRPM",
}


def build_screening_report(request: Mapping[str, Any]) -> dict[str, Any]:
    eligibility = evaluate_eligibility(request)
    raw_intake = request.get("erpm_intake", {})
    erpm_intake = dict(raw_intake) if isinstance(raw_intake, Mapping) else {}
    return {
        "proof_of_concept": True,
        "disclaimer": DISCLAIMER,
        "delivery_policy": dict(DELIVERY_POLICY),
        "erpm_intake": erpm_intake,
        "eligibility": eligibility,
        "agreement_readiness": evaluate_agreement_readiness(request),
        "template_selection": evaluate_template_selection(request, eligibility),
    }


def serialize_screening_report(report: Mapping[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
