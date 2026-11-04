from pathlib import Path

from src.adapters.signnow_api_sender import SignNowApiSender
from src.adapters.signnow_package_sender import SignNowPackageSender
from src.signing import build_agreement_sender


def test_local_signing_package_is_the_safe_default(tmp_path: Path):
    sender, mode = build_agreement_sender(tmp_path, {}, {})

    assert isinstance(sender, SignNowPackageSender)
    assert mode == "local_package"


def test_explicit_enabled_setting_builds_signnow_api_sender(tmp_path: Path):
    sender, mode = build_agreement_sender(
        tmp_path,
        {
            "enabled": True,
            "api_key": "secret",
            "account_email": "sender@umich.edu",
        },
        {},
    )

    assert isinstance(sender, SignNowApiSender)
    assert mode == "signnow_development"
