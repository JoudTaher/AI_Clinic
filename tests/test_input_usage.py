import pytest

from src.input_usage import build_input_usage
from src.request_normalization import normalize_request
from tests.fixtures import plasmid_request, request_for


def test_every_submitted_input_has_an_explicit_backend_use():
    request = normalize_request(plasmid_request())
    usage = build_input_usage(request)

    assert set(usage["erpm_intake"]) == set(request["erpm_intake"])
    assert set(usage["agreement_information"]) == set(
        request["agreement_information"]
    )
    assert all(item["uses"] for item in usage["erpm_intake"].values())
    assert all(item["uses"] for item in usage["agreement_information"].values())


@pytest.mark.parametrize(
    "category", ["chemical", "animal_derived", "biological", "device"]
)
def test_every_supported_template_request_has_no_silently_ignored_input(category: str):
    request = normalize_request(request_for(category))
    usage = build_input_usage(request)

    all_items = [*usage["erpm_intake"].values(), *usage["agreement_information"].values()]
    assert all("unmapped_input" not in item["uses"] for item in all_items)


def test_semantic_inputs_are_identified_in_the_audit_map():
    usage = build_input_usage(normalize_request(plasmid_request()))

    assert "semantic_eligibility" in usage["erpm_intake"]["project_title"]["uses"]
    assert "semantic_eligibility" in usage["erpm_intake"][
        "recipient_experimental_plan"
    ]["uses"]
    assert "semantic_eligibility" in usage["agreement_information"][
        "material_description"
    ]["uses"]


def test_unknown_payload_field_is_not_silently_ignored():
    request = plasmid_request()
    request["erpm_intake"]["unexpected_field"] = "value"

    usage = build_input_usage(normalize_request(request))

    assert usage["erpm_intake"]["unexpected_field"] == {
        "uses": ["unmapped_input"],
        "warning": "No backend consumer is registered for this field.",
    }


def test_template_inapplicable_agreement_fields_are_flagged():
    request = normalize_request(plasmid_request())
    request["agreement_information"]["shipping_address"] = "hidden stale value"

    usage = build_input_usage(request)

    assert usage["agreement_information"]["shipping_address"] == {
        "uses": ["not_applicable_to_selected_template"],
        "warning": "This field is not used by the selected agreement template.",
    }
