from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Criterion:
    field_id: str
    label: str
    section: str

    def as_dict(self) -> dict[str, str]:
        return {
            "field_id": self.field_id,
            "label": self.label,
            "section": self.section,
        }

