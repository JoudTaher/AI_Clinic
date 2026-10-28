from src.templates.selector import select_template
from tests.fixtures import request_for


def test_ineligible_request_has_no_template_selection():
    result = select_template(request_for("biological"), {"status": "ineligible"})
    assert result["status"] == "not_applicable"
    assert result["selected_template"] is None
    assert result["candidate_templates"] == []


def test_eligible_chemical_request_selects_autm_chemical():
    result = select_template(request_for("chemical"), {"status": "eligible"})
    assert result["status"] == "template_selected"
    assert result["selected_template"] == "autm_chemical"
    assert result["recommended_template"] is None
    assert result["candidate_templates"] == ["autm_chemical"]
    assert "source_path" not in result["candidate_details"][0]
    assert result["candidate_details"][0]["source_file"] == (
        "Template_AUTM_MTA_for_Chemical_Materials.docx"
    )


def test_eligible_biological_request_selects_ubmta():
    result = select_template(request_for("biological"), {"status": "eligible"})
    assert result["status"] == "template_selected"
    assert result["selected_template"] == "ubmta_implementing_letter"
    assert result["candidate_templates"] == ["ubmta_implementing_letter"]


def test_eligible_animal_request_selects_autm_biological():
    result = select_template(
        request_for("animal_derived"), {"status": "eligible"}
    )

    assert result["status"] == "template_selected"
    assert result["selected_template"] == "autm_biological"
    assert result["candidate_templates"] == ["autm_biological"]


def test_eligible_device_request_selects_simple_letter():
    result = select_template(request_for("device"), {"status": "eligible"})
    assert result["status"] == "template_selected"
    assert result["selected_template"] == "simple_letter_agreement"
    assert result["candidate_templates"] == ["simple_letter_agreement"]
    assert result["recommended_template"] is None


def test_mixed_request_never_selects_candidate():
    result = select_template(
        request_for("chemical", "biological"), {"status": "eligible"}
    )
    assert result["status"] == "route_to_erpm"
    assert result["selected_template"] is None
    assert result["candidate_templates"] == ["autm_chemical", "ubmta_implementing_letter"]


def test_malformed_material_categories_fail_closed_instead_of_crashing():
    request = request_for("chemical")
    request["erpm_intake"]["material_types"] = [{"invalid": True}]

    result = select_template(request, {"status": "eligible"})

    assert result["status"] == "route_to_erpm"
    assert result["recommended_template"] is None
    assert result["candidate_templates"] == []
    assert any("approved questionnaire values" in reason for reason in result["review_reasons"])
