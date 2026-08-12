"""Offline-by-default test safeguards."""

import socket

import pytest


@pytest.fixture(autouse=True)
def block_network_access(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject network connections from every A1 test."""

    def blocked(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("Network access is disabled in offline tests")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
