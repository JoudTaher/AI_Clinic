from __future__ import annotations

import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from src.adapters.paths import safe_identifier
from src.pipeline.models import RenderedAgreement
from src.templates.catalog import TemplateDefinition


class ReferenceTemplateRenderer:
    """Copies the approved source agreement without modifying its legal text."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def render(
        self,
        request_id: str,
        template: TemplateDefinition,
        request: Mapping[str, Any],
    ) -> RenderedAgreement:
        del request
        self.output_dir.mkdir(parents=True, exist_ok=True)
        suffix = template.source_path.suffix
        filename = (
            f"{safe_identifier(request_id)}-{safe_identifier(template.template_id)}{suffix}"
        )
        destination = self.output_dir / filename
        shutil.copyfile(template.source_path, destination)
        return RenderedAgreement(template_id=template.template_id, path=destination)
