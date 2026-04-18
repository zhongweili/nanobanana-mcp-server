import os

from nanobanana_mcp_server.server import _default_model_summary


def test_default_model_summary_auto(monkeypatch):
    monkeypatch.delenv("NANOBANANA_MODEL", raising=False)
    summary = _default_model_summary()
    assert summary == (
        "auto (smart selection across "
        "gemini-3.1-flash-image-preview, gemini-3-pro-image-preview, "
        "and gemini-2.5-flash-image)"
    )


def test_default_model_summary_nb2(monkeypatch):
    monkeypatch.setenv("NANOBANANA_MODEL", "nb2")
    assert _default_model_summary() == "nb2 (gemini-3.1-flash-image-preview)"


def test_default_model_summary_pro(monkeypatch):
    monkeypatch.setenv("NANOBANANA_MODEL", "pro")
    assert _default_model_summary() == "pro (gemini-3-pro-image-preview)"


def test_default_model_summary_flash(monkeypatch):
    monkeypatch.setenv("NANOBANANA_MODEL", "flash")
    assert _default_model_summary() == "flash (gemini-2.5-flash-image)"
