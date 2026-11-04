from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from src.adapters.signnow_api_sender import SignNowApiSender, SignNowSettings
from src.adapters.signnow_package_sender import SignNowPackageSender
from src.pipeline.ports import AgreementSender


def build_agreement_sender(
    project_root: Path,
    secrets: Mapping[str, Any] | None = None,
    environment: Mapping[str, str] | None = None,
) -> tuple[AgreementSender, str]:
    settings = SignNowSettings.from_sources(secrets, environment)
    if settings.enabled:
        return SignNowApiSender(settings), "signnow_development"
    return (
        SignNowPackageSender(project_root / "outputs" / "signing"),
        "local_package",
    )
