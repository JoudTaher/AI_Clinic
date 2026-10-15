from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_loads_core_intake_sections():
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=10)
    assert not app.exception
    assert app.title[0].value == "Outgoing MTA Screening Proof of Concept"
    headings = [item.value for item in app.subheader]
    assert "Part A General eligibility" in headings
    assert "Part B Material specific eligibility" in headings
    assert "Part C Agreement information" in headings
    assert app.multiselect[0].label == "Material categories"
    assert any(button.label == "Screen request" for button in app.button)
