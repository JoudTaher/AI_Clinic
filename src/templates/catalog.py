from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TEMPLATE_ID_PATTERN = re.compile(r"^[a-z0-9_]+$")


class CatalogError(ValueError):
    """Raised when template catalog data is incomplete or unsafe."""


@dataclass(frozen=True)
class TemplateDefinition:
    template_id: str
    display_name: str
    source_path: Path
    material_categories: tuple[str, ...]
    required_context: dict[str, bool]
    automation_enabled: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "display_name": self.display_name,
            "source_file": self.source_path.name,
            "material_categories": list(self.material_categories),
            "required_context": dict(self.required_context),
            "automation_enabled": self.automation_enabled,
        }


def _required_string(raw: Mapping[str, Any], field: str, index: int) -> str:
    value = raw.get(field)
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"Template at index {index} requires a non-empty {field}")
    return value.strip()


def _source_path(source_file: str, project_root: Path, index: int) -> Path:
    relative_path = Path(source_file)
    if relative_path.is_absolute():
        raise CatalogError(f"Template at index {index} source_file must be relative")

    root = project_root.resolve()
    resolved = (root / relative_path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise CatalogError(
            f"Template at index {index} source_file leaves the project root"
        ) from error
    if not resolved.is_file():
        raise CatalogError(
            f"Template at index {index} source_file does not exist: {source_file}"
        )
    return resolved


def _definition(raw: Any, index: int, project_root: Path) -> TemplateDefinition:
    if not isinstance(raw, Mapping):
        raise CatalogError(f"Template at index {index} must be an object")

    template_id = _required_string(raw, "id", index)
    if not TEMPLATE_ID_PATTERN.fullmatch(template_id):
        raise CatalogError(
            f"Template at index {index} id may contain lowercase letters, numbers, and underscores only"
        )
    display_name = _required_string(raw, "display_name", index)
    source_file = _required_string(raw, "source_file", index)

    raw_categories = raw.get("material_categories")
    if (
        not isinstance(raw_categories, list)
        or not raw_categories
        or not all(isinstance(value, str) and value.strip() for value in raw_categories)
    ):
        raise CatalogError(
            f"Template at index {index} requires non-empty material_categories"
        )

    raw_context = raw.get("required_context")
    if not isinstance(raw_context, Mapping) or not all(
        isinstance(key, str) and key and isinstance(value, bool)
        for key, value in raw_context.items()
    ):
        raise CatalogError(
            f"Template at index {index} required_context must map names to booleans"
        )

    automation_enabled = raw.get("automation_enabled")
    if not isinstance(automation_enabled, bool):
        raise CatalogError(
            f"Template at index {index} automation_enabled must be a boolean"
        )

    return TemplateDefinition(
        template_id=template_id,
        display_name=display_name,
        source_path=_source_path(source_file, project_root, index),
        material_categories=tuple(dict.fromkeys(raw_categories)),
        required_context=dict(raw_context),
        automation_enabled=automation_enabled,
    )


def load_template_catalog(path: Path | None = None) -> tuple[TemplateDefinition, ...]:
    catalog_path = path or Path(__file__).with_name("catalog.json")
    project_root = (
        Path(__file__).resolve().parents[2] if path is None else catalog_path.resolve().parent
    )

    try:
        raw_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CatalogError(f"Unable to read template catalog: {error}") from error
    if not isinstance(raw_catalog, list) or not raw_catalog:
        raise CatalogError("Template catalog must be a non-empty list")

    definitions = tuple(
        _definition(raw, index, project_root)
        for index, raw in enumerate(raw_catalog)
    )
    seen: set[str] = set()
    for definition in definitions:
        if definition.template_id in seen:
            raise CatalogError(f"Duplicate template id: {definition.template_id}")
        seen.add(definition.template_id)
    return definitions
