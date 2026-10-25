from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class SigningConfigurationError(ValueError):
    """Raised when deployment-owned signing configuration is incomplete."""


def validate_email(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not EMAIL_PATTERN.fullmatch(normalized):
        raise SigningConfigurationError(f"{field_name} must be a valid email address")
    return normalized


@dataclass(frozen=True)
class SigningConfiguration:
    um_signer_name: str
    um_signer_title: str
    um_signer_email: str

    def __post_init__(self) -> None:
        for field_name in ("um_signer_name", "um_signer_title"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise SigningConfigurationError(f"{field_name} must not be empty")
            object.__setattr__(self, field_name, value.strip())
        if not isinstance(self.um_signer_email, str):
            raise SigningConfigurationError(
                "um_signer_email must be a valid email address"
            )
        object.__setattr__(
            self,
            "um_signer_email",
            validate_email(self.um_signer_email, "um_signer_email"),
        )

    @classmethod
    def from_environment(
        cls, environment: Mapping[str, str] | None = None
    ) -> "SigningConfiguration":
        source = os.environ if environment is None else environment
        fields = {
            "um_signer_name": "MTA_UM_SIGNER_NAME",
            "um_signer_title": "MTA_UM_SIGNER_TITLE",
            "um_signer_email": "MTA_UM_SIGNER_EMAIL",
        }
        missing = [
            variable
            for variable in fields.values()
            if not isinstance(source.get(variable), str) or not source[variable].strip()
        ]
        if missing:
            raise SigningConfigurationError(
                "Missing signing configuration: " + ", ".join(missing)
            )
        return cls(**{field: source[variable] for field, variable in fields.items()})
