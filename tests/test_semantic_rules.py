from src.semantic_rules import analyze_open_text


def test_explicit_noncommercial_and_no_human_use_are_recognized_with_evidence():
    result = analyze_open_text(
        {
            "recipient_experimental_plan": (
                "Internal, non-commercial laboratory research only. "
                "The material will not be used in humans or for diagnosis."
            ),
            "material_description": "A synthetic research reagent.",
        }
    )

    assert result["facts"]["internal_noncommercial_research_only"] is True
    assert result["facts"]["chemical_not_used_in_humans"] is True
    assert result["facts"]["device_not_used_in_humans"] is True
    assert result["facts"]["device_not_clinical_or_diagnostic"] is True
    assert "recipient_experimental_plan" in result["evidence"][
        "internal_noncommercial_research_only"
    ]["source_fields"]


def test_commercial_clinical_language_fails_relevant_rules():
    result = analyze_open_text(
        {
            "recipient_experimental_plan": (
                "Product development for a commercial clinical diagnostic device "
                "that will be tested in patients."
            )
        }
    )

    assert result["facts"]["internal_noncommercial_research_only"] is False
    assert result["facts"]["device_not_clinical_or_diagnostic"] is False
    assert result["facts"]["device_not_used_in_humans"] is False


def test_negation_is_not_misread_as_human_use():
    result = analyze_open_text(
        {"related_details": "This device is not for use in humans or patients."}
    )

    assert result["facts"]["device_not_used_in_humans"] is True


def test_ambiguous_open_text_stays_unresolved():
    result = analyze_open_text(
        {"recipient_experimental_plan": "The team will study performance."}
    )

    assert result["facts"]["internal_noncommercial_research_only"] is None
    assert result["facts"]["device_not_used_in_humans"] is None
    assert result["nlp_backend"]["library"] == "spacy"
    assert result["nlp_backend"]["pipeline"] == "blank_en_with_sentencizer"


def test_nonliving_animal_derivative_language_is_recognized():
    result = analyze_open_text(
        {
            "material_description": (
                "Fixed, non-living mouse tissue samples; no live animals and no "
                "restricted species or special permits are involved."
            )
        }
    )

    assert result["facts"]["animal_no_live_animals"] is True
    assert result["facts"]["animal_no_restricted_species_or_permits"] is True
    assert result["facts"]["animal_nonliving_derivative_definition_met"] is True


def test_explicit_ip_export_and_ownership_blockers_are_recognized():
    result = analyze_open_text(
        {
            "related_details": (
                "The material is patented and encumbered, is owned by another party "
                "subject to third-party restrictions, and is a DEA Schedule II "
                "controlled substance."
            )
        }
    )

    assert result["facts"]["not_invention_report_patented_or_encumbered"] is False
    assert result["facts"]["um_owned_without_third_party_restrictions"] is False
    assert result["facts"]["not_controlled_beyond_ear99"] is False


def test_explicit_standard_facts_can_be_recognized_without_guessing():
    result = analyze_open_text(
        {
            "recipient_entity": "Example U.S. non-profit research institution",
            "related_details": (
                "The material is owned by U-M with no third-party restrictions. "
                "It is not patented, licensed, encumbered, or the subject of an "
                "invention report. It is EAR99 and no return is required."
            ),
        }
    )

    assert result["facts"]["recipient_is_us_nonprofit"] is True
    assert result["facts"]["um_owned_without_third_party_restrictions"] is True
    assert result["facts"]["not_invention_report_patented_or_encumbered"] is True
    assert result["facts"]["not_controlled_beyond_ear99"] is True
    assert result["facts"]["return_not_required"] is True
