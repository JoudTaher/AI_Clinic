from datetime import datetime
from zoneinfo import ZoneInfo

from src.request_identity import submission_identity
from tests.fixtures import request_for, verified_facts_for


def test_submission_identity_keeps_full_hash_and_adds_readable_reference():
    identity = submission_identity(
        request_for("chemical"),
        verified_facts_for("chemical"),
        now=datetime(2026, 11, 18, 9, 30, tzinfo=ZoneInfo("America/Detroit")),
    )

    assert len(identity.submission_id) == len("mta-") + 64
    assert identity.submission_id.startswith("mta-")
    assert identity.tracking_reference == (
        "MTA-2026-" + identity.submission_id.removeprefix("mta-")[:8].upper()
    )


def test_internal_tracking_reference_never_changes_submission_identity():
    request = request_for("chemical")
    original = submission_identity(request, verified_facts_for("chemical"))
    request["tracking_reference"] = "MTA-1999-STALE123"

    repeated = submission_identity(request, verified_facts_for("chemical"))

    assert repeated.submission_id == original.submission_id
