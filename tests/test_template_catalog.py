import json
from pathlib import Path

import pytest

from src.templates.catalog import CatalogError, load_template_catalog


def test_default_catalog_contains_every_supplied_agreement():
    catalog = load_template_catalog()

    assert [template.template_id for template in catalog] == [
        "autm_chemical",
        "autm_biological",
        "simple_letter_agreement",
        "ubmta_implementing_letter",
    ]
    assert all(template.source_path.is_file() for template in catalog)


def test_new_template_can_be_added_without_selector_code_changes(tmp_path: Path):
    source = tmp_path / "new-template.docx"
    source.write_bytes(b"template")
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(
        json.dumps(
            [
                {
                    "id": "new_template",
                    "display_name": "New Template",
                    "source_file": source.name,
                    "material_categories": ["biological"],
                    "required_context": {"approved_for_new_template": True},
                }
            ]
        ),
        encoding="utf-8",
    )

    catalog = load_template_catalog(catalog_path)

    assert catalog[0].template_id == "new_template"
    assert catalog[0].required_context == {"approved_for_new_template": True}


def test_catalog_rejects_a_missing_required_field(tmp_path: Path):
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(
        json.dumps(
            [
                {
                    "display_name": "Broken",
                    "source_file": "missing.docx",
                    "material_categories": ["biological"],
                    "required_context": {},
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(CatalogError, match="id"):
        load_template_catalog(catalog_path)


def test_catalog_rejects_duplicate_ids(tmp_path: Path):
    source = tmp_path / "template.docx"
    source.write_bytes(b"template")
    definition = {
        "id": "duplicate",
        "display_name": "Duplicate",
        "source_file": source.name,
        "material_categories": ["chemical"],
        "required_context": {},
    }
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps([definition, definition]), encoding="utf-8")

    with pytest.raises(CatalogError, match="Duplicate template id"):
        load_template_catalog(catalog_path)
