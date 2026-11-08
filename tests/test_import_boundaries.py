from __future__ import annotations

import subprocess
import sys


def test_agreement_readiness_imports_cleanly_in_fresh_interpreter():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from src.agreement_readiness import evaluate_agreement_readiness",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
