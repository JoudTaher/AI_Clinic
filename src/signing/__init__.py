from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.signing.factory import build_agreement_sender

__all__ = ["build_agreement_sender"]


def __getattr__(name: str) -> Any:
    if name == "build_agreement_sender":
        from src.signing.factory import build_agreement_sender

        return build_agreement_sender
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
