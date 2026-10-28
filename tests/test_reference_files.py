import hashlib
import json
from pathlib import Path


EXPECTED_FILES = {
    "Outgoing MTA Eligibility Checklist for UMSI.docx",
    "Template_AUTM_MTA_for_Biological_Materials.doc",
    "Template_AUTM_MTA_for_Biological_Materials.docx",
    "Template_AUTM_MTA_for_Chemical_Materials.docx",
    "Template_Simple Letter Agreement.docx",
    "Template_UBMTA.docx",
}


def test_reference_manifest_matches_copied_files():
    reference_dir = Path(__file__).parents[1] / "reference_files"
    manifest = json.loads((reference_dir / "manifest.json").read_text())
    assert set(manifest) == EXPECTED_FILES
    for filename, expected_digest in manifest.items():
        contents = (reference_dir / filename).read_bytes()
        assert hashlib.sha256(contents).hexdigest() == expected_digest
