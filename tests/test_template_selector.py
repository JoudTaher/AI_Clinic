from src.templates.selector import select_template
from tests.fixtures import request_for


def test_ineligible_request_has_no_template_selection():
    result = select_template(request_for("biological"), {"status": "ineligible"})
    assert result["status"] == "manual_special_case_review"
    assert result["selected_template"] is None
    assert result["candidate_templates"] == []


def test_eligible_chemical_request_selects_chemical_material_agreement():
    result = select_template(request_for("chemical"), {"status": "eligible"})
    assert result["status"] == "template_selected"
    assert result["selected_template"] == "chemical_material_agreement"
    assert result["recommended_template"] is None
    assert result["candidate_templates"] == ["chemical_material_agreement"]
    assert "source_path" not in result["candidate_details"][0]
    assert result["candidate_details"][0]["source_file"] == (
        "Template_Chemical_Materials.docx"
    )


def test_eligible_biological_request_selects_biological_material_agreement():
    result = select_template(request_for("biological"), {"status": "eligible"})
    assert result["status"] == "template_selected"
    assert result["selected_template"] == "biological_material_agreement"
    assert result["candidate_templates"] == ["biological_material_agreement"]


def test_eligible_animal_request_selects_animal_material_agreement():
    result = select_template(
        request_for("animal_derived"), {"status": "eligible"}
    )

    assert result["status"] == "template_selected"
    assert result["selected_template"] == "animal_material_agreement"
    assert result["candidate_templates"] == ["animal_material_agreement"]


def test_eligible_device_request_selects_device_material_agreement():
    result = select_template(request_for("device"), {"status": "eligible"})
    assert result["status"] == "template_selected"
    assert result["selected_template"] == "device_material_agreement"
    assert result["candidate_templates"] == ["device_material_agreement"]
    assert result["recommended_template"] is None


def test_mixed_request_never_selects_candidate():
    result = select_template(
        request_for("chemical", "biological"), {"status": "eligible"}
    )
    assert result["status"] == "manual_special_case_review"
    assert result["selected_template"] is None
    assert result["candidate_templates"] == [
        "chemical_material_agreement",
        "biological_material_agreement",
    ]


def test_malformed_material_categories_fail_closed_instead_of_crashing():
    request = request_for("chemical")
    request["erpm_intake"]["material_types"] = [{"invalid": True}]

    result = select_template(request, {"status": "eligible"})

    assert result["status"] == "manual_special_case_review"
    assert result["recommended_template"] is None
    assert result["candidate_templates"] == []
    assert any("approved questionnaire values" in reason for reason in result["review_reasons"])
