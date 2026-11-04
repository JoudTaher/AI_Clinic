from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_loads_erpm_aligned_intake_sections():
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=10)
    assert not app.exception
    assert app.title[0].value == "Outgoing MTA Automation Proof of Concept"
    headings = [item.value for item in app.subheader]
    assert headings[:5] == [
        "Introduction",
        "Personnel",
        "Material Details",
        "Material Safety",
        "Outgoing Material Details",
    ]
    assert "Automatic Approval Eligibility Checklist" not in headings
    assert "Agreement and Signing Information" in headings

    labels = {
        element.label
        for group in (app.text_input, app.text_area, app.selectbox, app.multiselect)
        for element in group
    }
    assert "Request ID" not in labels
    assert "Copy data from an existing UFA record?" not in labels
    assert "Project Title *" in labels
    assert "Material Type *" in labels
    assert "Recipient Entity *" in labels
    assert "Recipient Scientist Email *" in labels
    assert "Contact PI phone" not in labels
    assert "Contact PI email" not in labels
    assert "Primary Research Administrator phone" not in labels
    assert "Primary Research Administrator email" not in labels
    assert "Sponsor name (if applicable)" not in labels
    assert "Provider Scientist title" not in labels
    assert "Provider Scientist signing email" not in labels
    assert "Recipient's experimental plan for use of the material *" in labels
    assert "Is the recipient a verified UBMTA signatory?" not in labels
    assert (
        "Material is being sent from UM to a U.S. non-profit institution "
        "(e.g., university, college, non-profit, or research organization)"
        not in labels
    )
    assert (
        "Has the Simple Letter Agreement been authorized for this request?" not in labels
    )
    assert any(button.label == "Process request" for button in app.button)


def test_material_types_match_the_erpm_form():
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=10)
    assert not app.exception
    material_types = next(
        element for element in app.multiselect if element.label == "Material Type *"
    )
    assert material_types.options == [
        "Human derived materials (isolated tissue, samples, specimens, cells, etc.)",
        "Cells (other than those derived from human subjects or patients)",
        "Plasmid/Vector (rDNA or SNA)",
        "Mouse/Rat",
        "Other Model Organism (yeast, drosophila, zebrafish)",
        "Custom Antibody",
        "Protein",
        "Chemical compound",
        "Software/code",
        "Device",
        "Other material",
    ]


def test_human_material_selection_shows_only_source_form_conditionals():
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=10)
    material_types = next(
        element for element in app.multiselect if element.label == "Material Type *"
    )

    material_types.select(
        "Human derived materials (isolated tissue, samples, specimens, cells, etc.)"
    )
    app.run(timeout=10)

    labels = {
        element.label
        for group in (app.text_input, app.text_area, app.selectbox)
        for element in group
    }
    assert "Human derived tissue/samples description *" in labels
    assert "How are these materials classified? *" in labels
    assert "IRB study HUM number *" in labels
    assert (
        "Protocol and informed-consent sections allowing transfer outside U-M *"
        in labels
    )
    assert "Original Material description *" in labels


def test_empty_submission_fails_closed_without_crashing():
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=10)

    next(button for button in app.button if button.label == "Process request").click()
    app.run(timeout=10)

    assert not app.exception
    assert any("questionnaire is incomplete" in item.value.lower() for item in app.warning)
    assert any("Enter the project title." in item.value for item in app.error)
    assert any("Select Yes or No." in item.value for item in app.error)


def test_invalid_email_error_is_shown_next_to_the_email_field():
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=10)
    next(
        item
        for item in app.text_input
        if item.label == "Recipient Scientist Email *"
    ).set_value("not an email")

    next(button for button in app.button if button.label == "Process request").click()
    app.run(timeout=10)

    assert not app.exception
    assert any(
        item.value == "Enter a valid Recipient Scientist Email."
        for item in app.error
    )


def test_ubmta_shows_only_ubmta_template_entries():
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=10)
    material_types = next(
        element for element in app.multiselect if element.label == "Material Type *"
    )
    material_types.select("Plasmid/Vector (rDNA or SNA)")
    app.run(timeout=10)

    labels = {
        element.label
        for group in (app.text_input, app.text_area, app.selectbox)
        for element in group
    }
    assert "Original Material description *" in labels
    assert "Shipping recipient name" not in labels
    assert "Shipping address" not in labels
    assert (
        "Recipient Scientist authorized to certify for Recipient Organization? *"
        in labels
    )


def test_agreement_section_reuses_full_names_and_labels_titles_as_optional():
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=10)
    next(item for item in app.text_input if item.label == "Contact PI *").set_value(
        "Dr. Provider"
    )
    next(
        item for item in app.text_input if item.label == "Recipient Scientist Name *"
    ).set_value("Dr. Recipient")
    next(
        item for item in app.multiselect if item.label == "Material Type *"
    ).select("Plasmid/Vector (rDNA or SNA)")
    app.run(timeout=10)

    labels = {element.label for element in app.text_input}
    assert "Provider Scientist academic/job title (if known)" in labels
    assert "Recipient Scientist academic/job title (if known)" in labels
    assert "Provider Scientist title" not in labels
    assert "Recipient Scientist title" not in labels
    captions = [item.value for item in app.caption]
    assert "Provider Scientist full name: Dr. Provider" in captions
    assert "Recipient Scientist full name: Dr. Recipient" in captions


def test_autm_shows_autm_shipping_and_signatory_entries():
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=10)
    material_types = next(
        element for element in app.multiselect if element.label == "Material Type *"
    )
    material_types.select("Chemical compound")
    app.run(timeout=10)

    labels = {
        element.label
        for group in (app.text_input, app.text_area, app.selectbox)
        for element in group
    }
    assert "Material description *" in labels
    assert "Shipping recipient name *" in labels
    assert "Shipping address *" in labels
    assert "Recipient Authorized Signatory name *" in labels


def test_simple_letter_omits_autm_only_fields():
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=10)
    material_types = next(
        element for element in app.multiselect if element.label == "Material Type *"
    )
    material_types.select("Device")
    app.run(timeout=10)

    labels = {
        element.label
        for group in (app.text_input, app.text_area, app.selectbox)
        for element in group
    }
    assert "Material description *" in labels
    assert "Recipient Scientist academic/job title (if known)" not in labels
    assert "Shipping recipient name" not in labels
    assert "Shipping address" not in labels
    assert "Recipient Authorized Official name *" in labels


def test_mixed_selection_hides_all_template_specific_agreement_inputs():
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=10)
    material_types = next(
        element for element in app.multiselect if element.label == "Material Type *"
    )
    material_types.select("Chemical compound")
    material_types.select("Device")
    app.run(timeout=10)

    labels = {
        element.label
        for group in (app.text_input, app.text_area, app.selectbox)
        for element in group
    }
    assert "Provider Scientist academic/job title (if known)" not in labels
    assert "Material description" not in labels
    assert "Shipping address" not in labels
