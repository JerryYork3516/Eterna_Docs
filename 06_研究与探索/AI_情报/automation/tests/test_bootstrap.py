"""Stage 1.12 A1 bootstrap checks."""

import importlib
import socket
import sys

import pytest


SECRET_ENVIRONMENT_NAMES = (
    "OPENAI_API_KEY",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GMAIL_CREDENTIALS",
    "GITHUB_TOKEN",
)


def test_python_version_is_3_13() -> None:
    assert sys.version_info[:2] == (3, 13)


def test_packages_import_without_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in SECRET_ENVIRONMENT_NAMES:
        monkeypatch.delenv(name, raising=False)

    collectors = importlib.import_module("collectors")
    delivery = importlib.import_module("delivery")
    pipeline = importlib.import_module("pipeline")
    rendering = importlib.import_module("rendering")

    assert collectors.__doc__
    assert delivery.__doc__
    assert pipeline.__version__ == "0.1.0"
    assert rendering.__doc__


def test_network_is_blocked_by_default() -> None:
    with pytest.raises(RuntimeError, match="Network access is disabled"):
        socket.create_connection(("example.invalid", 443))
