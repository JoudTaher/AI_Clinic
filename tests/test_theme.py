from pathlib import Path
import tomllib


def test_streamlit_theme_uses_michigan_brand_palette():
    config_path = Path(__file__).parents[1] / ".streamlit" / "config.toml"
    with config_path.open("rb") as config_file:
        theme = tomllib.load(config_file)["theme"]

    assert theme["base"] == "light"
    assert theme["backgroundColor"] == "#FFFFFF"
    assert theme["secondaryBackgroundColor"] == "#F5F5F5"
    assert theme["primaryColor"] == "#00274C"
    assert theme["textColor"] == "#00274C"
    assert theme["linkColor"] == "#00274C"
    assert theme["yellowColor"] == "#FFCB05"
    assert theme["redColor"] == "#9A3324"
    assert theme["orangeColor"] == "#D86018"
    assert theme["greenColor"] == "#75988D"
    assert theme["blueColor"] == "#2F65A7"
    assert theme["chartCategoricalColors"][:2] == ["#00274C", "#FFCB05"]
    assert theme["dataframeHeaderBackgroundColor"] == "#FFCB05"
    assert theme["dataframeHeaderTextColor"] == "#00274C"
