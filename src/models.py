from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticLabels:
    satisfied: str
    violated: str
    unknown: str
    satisfied_threshold: float = 0.60
    violated_threshold: float = 0.85
    minimum_margin: float = 0.15


@dataclass(frozen=True)
class Criterion:
    field_id: str
    label: str
    section: str
    semantic_sources: tuple[str, ...] = ()
    semantic_labels: SemanticLabels | None = None
    validate_semantics: bool = False

    def as_dict(self) -> dict[str, str]:
        return {
            "field_id": self.field_id,
            "label": self.label,
            "section": self.section,
        }
