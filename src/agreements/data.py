from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from src.pipeline.ports import AgreementRenderError


class AgreementDataError(AgreementRenderError):
    """Raised when required agreement population data is missing."""


PROVIDER_ORGANIZATION = "The Regents of the University of Michigan"
PROVIDER_ADDRESS = "1600 Huron Parkway, 2nd Floor\nAnn Arbor, Michigan 48109-2590"


@dataclass(frozen=True)
class AgreementData:
    provider_organization: str
    provider_address: str
    provider_scientist_name: str
    provider_scientist_title: str
    recipient_organization: str
    recipient_address: str
    recipient_scientist_name: str
    recipient_scientist_title: str
    recipient_authorized_official_name: str
    recipient_authorized_official_title: str
    recipient_scientist_can_certify_organization: bool
    material_description: str
    shipping_recipient_name: str
    shipping_address: str
    transmittal_fee: str

    @classmethod
    def from_request(
        cls, request: Mapping[str, Any], template_id: str
    ) -> "AgreementData":
        raw = request.get("agreement_information", {})
        if not isinstance(raw, Mapping):
            raise AgreementDataError("agreement_information must be an object")

        def required(field_id: str) -> str:
            value = raw.get(field_id)
            if not isinstance(value, str) or not value.strip():
                raise AgreementDataError(f"Missing required agreement field: {field_id}")
            return value.strip()

        def optional(field_id: str) -> str:
            value = raw.get(field_id, "")
            if not isinstance(value, str):
                raise AgreementDataError(f"Agreement field must be text: {field_id}")
            return value.strip()

        def required_for(field_id: str, template_ids: set[str]) -> str:
            return required(field_id) if template_id in template_ids else optional(field_id)

        fee = raw.get("transmittal_fee", "")
        if not isinstance(fee, str):
            raise AgreementDataError("transmittal_fee must be text")

        can_certify = raw.get("recipient_scientist_can_certify_organization")
        if not isinstance(can_certify, bool):
            can_certify = False
        requires_recipient_official = template_id in {
            "autm_chemical",
            "autm_biological",
            "simple_letter_agreement",
        } or (template_id == "ubmta_implementing_letter" and not can_certify)

        recipient_official_name = (
            required("recipient_authorized_official_name")
            if requires_recipient_official
            else optional("recipient_authorized_official_name")
        )
        recipient_official_title = (
            required("recipient_authorized_official_title")
            if requires_recipient_official
            else optional("recipient_authorized_official_title")
        )

        return cls(
            provider_organization=PROVIDER_ORGANIZATION,
            provider_address=PROVIDER_ADDRESS,
            provider_scientist_name=required("provider_scientist_name"),
            provider_scientist_title=optional("provider_scientist_title"),
            recipient_organization=required("recipient_institution_name"),
            recipient_address=required("recipient_institution_address"),
            recipient_scientist_name=required("recipient_scientist_name"),
            recipient_scientist_title=optional("recipient_scientist_title"),
            recipient_authorized_official_name=recipient_official_name,
            recipient_authorized_official_title=recipient_official_title,
            recipient_scientist_can_certify_organization=can_certify,
            material_description=required("material_description"),
            shipping_recipient_name=required_for(
                "shipping_recipient_name", {"autm_chemical", "autm_biological"}
            ),
            shipping_address=required_for(
                "shipping_address", {"autm_chemical", "autm_biological"}
            ),
            transmittal_fee=fee.strip() or "N/A",
        )
