from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


class AgreementDataError(ValueError):
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
    material_description: str
    shipping_recipient_name: str
    shipping_address: str
    transmittal_fee: str

    @classmethod
    def from_request(cls, request: Mapping[str, Any]) -> "AgreementData":
        raw = request.get("agreement_information", {})
        if not isinstance(raw, Mapping):
            raise AgreementDataError("agreement_information must be an object")

        def required(field_id: str) -> str:
            value = raw.get(field_id)
            if not isinstance(value, str) or not value.strip():
                raise AgreementDataError(f"Missing required agreement field: {field_id}")
            return value.strip()

        fee = raw.get("transmittal_fee", "")
        if not isinstance(fee, str):
            raise AgreementDataError("transmittal_fee must be text")

        return cls(
            provider_organization=PROVIDER_ORGANIZATION,
            provider_address=PROVIDER_ADDRESS,
            provider_scientist_name=required("provider_scientist_name"),
            provider_scientist_title=required("provider_scientist_title"),
            recipient_organization=required("recipient_institution_name"),
            recipient_address=required("recipient_institution_address"),
            recipient_scientist_name=required("recipient_scientist_name"),
            recipient_scientist_title=required("recipient_scientist_title"),
            material_description=required("material_description"),
            shipping_recipient_name=required("shipping_recipient_name"),
            shipping_address=required("shipping_address"),
            transmittal_fee=fee.strip() or "N/A",
        )
