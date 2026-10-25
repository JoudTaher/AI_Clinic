from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_loads_erpm_aligned_intake_sections():
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=10)
    assert not app.exception
    assert app.title[0].value == "Outgoing MTA Screening Proof of Concept"
    headings = [item.value for item in app.subheader]
    assert headings[:5] == [
        "Introduction",
        "Personnel",
        "Material Details",
        "Material Safety",
        "Outgoing Material Details",
    ]
    assert "Streamlined Eligibility Review" in headings

    labels = {
        element.label
        for group in (app.text_input, app.text_area, app.selectbox, app.multiselect)
        for element in group
    }
    assert "Project title" in labels
    assert "Material types" in labels
    assert "Plasmid/Vector/DNA/RNA description" in labels
    assert "Recipient entity" in labels
    assert "Recipient scientist email" in labels
    assert "Recipient's experimental plan for use of the material" in labels
    assert "Is the recipient a verified UBMTA signatory?" in labels
    assert (
        "Has the Simple Letter Agreement been authorized for this request?" in labels
    )
    assert any(button.label == "Screen request" for button in app.button)


def test_material_types_match_the_erpm_form():
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=10)
    assert not app.exception
    material_types = next(
        element for element in app.multiselect if element.label == "Material types"
    )
    assert material_types.options == [
        "Human derived materials (isolated tissue, samples, specimens, cells, etc.)",
        "Cells (other than those derived from human subjects or patients)",
        "Plasmid/vector (DNA or RNA)",
        "Mouse/Rat",
        "Other model organism (yeast, drosophila, zebrafish)",
        "Custom antibody",
        "Protein",
        "Chemical compound",
        "Software/code",
        "Device",
        "Other material",
    ]
