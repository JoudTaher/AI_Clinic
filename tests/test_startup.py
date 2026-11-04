from pathlib import Path


def test_run_script_checks_semantic_model_dependencies():
    script = (Path(__file__).parents[1] / "run_app.command").read_text()

    assert "import torch, transformers" in script

