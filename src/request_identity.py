from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from src.request_normalization import normalize_request


DETROIT = ZoneInfo("America/Detroit")
UNSAFE_DOCUMENT_NAME = re.compile(r"[\\/:*?\"<>|\x00-\x1f]+")


@dataclass(frozen=True)
class SubmissionIdentity:
    submission_id: str
    tracking_reference: str


def tracking_reference_for_submission(
    submission_id: str, *, year: int | None = None
) -> str:
    raw_hash = submission_id.removeprefix("mta-")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", raw_hash):
        raw_hash = hashlib.sha256(submission_id.encode("utf-8")).hexdigest()
    resolved_year = year or datetime.now(DETROIT).year
    return f"MTA-{resolved_year}-{raw_hash[:8].upper()}"


def submission_identity(
    request: Mapping[str, Any],
    verified_facts: Mapping[str, Any] | None = None,
    *,
    now: datetime | None = None,
) -> SubmissionIdentity:
    normalized = normalize_request(request)
    normalized.pop("tracking_reference", None)
    trusted_facts = {
        key: value
        for key, value in (verified_facts or {}).items()
        if isinstance(key, str) and isinstance(value, bool)
    }
    serialized = json.dumps(
        {"request": normalized, "verified_facts": trusted_facts},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    fingerprint = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    submission_id = f"mta-{fingerprint}"
    local_now = now.astimezone(DETROIT) if now is not None else datetime.now(DETROIT)
    return SubmissionIdentity(
        submission_id=submission_id,
        tracking_reference=tracking_reference_for_submission(
            submission_id, year=local_now.year
        ),
    )


def request_tracking_reference(
    request: Mapping[str, Any], submission_id: str, *, year: int | None = None
) -> str:
    value = request.get("tracking_reference")
    if isinstance(value, str) and re.fullmatch(r"MTA-\d{4}-[0-9A-F]{8}", value):
        return value
    return tracking_reference_for_submission(submission_id, year=year)


def searchable_document_name(
    tracking_reference: str, project_title: Any
) -> str:
    title = project_title.strip() if isinstance(project_title, str) else ""
    title = UNSAFE_DOCUMENT_NAME.sub(" ", title)
    title = " ".join(title.split())[:120].strip()
    return (
        f"{tracking_reference} — {title}"
        if title
        else tracking_reference
    )
