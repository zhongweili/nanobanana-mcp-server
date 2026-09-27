"""Startup description of the configured default model."""

import pytest

from nanobanana_mcp_server.config.settings import (
    ModelSelectionConfig,
    ModelTier,
    describe_default_model,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("tier", "model_name"),
    [
        (ModelTier.FLASH, "gemini-2.5-flash-image"),
        (ModelTier.NB2, "gemini-3.1-flash-image-preview"),
        (ModelTier.PRO, "gemini-3-pro-image-preview"),
    ],
)
def test_explicit_tier_names_its_model(tier: ModelTier, model_name: str):
    summary = describe_default_model(tier)

    assert summary.startswith(f"{tier.value} (")
    assert model_name in summary


@pytest.mark.unit
def test_auto_defaults_to_nb2_and_mentions_pro():
    summary = describe_default_model(ModelTier.AUTO)

    assert summary.startswith("auto (")
    assert "gemini-3.1-flash-image-preview" in summary
    assert "Pro" in summary
    assert "gemini-2.5-flash-image" not in summary


@pytest.mark.unit
def test_from_env_reads_nanobanana_model(monkeypatch):
    monkeypatch.setattr(
        "nanobanana_mcp_server.config.settings.load_dotenv",
        lambda *args, **kwargs: False,
    )

    monkeypatch.delenv("NANOBANANA_MODEL", raising=False)
    assert ModelSelectionConfig.from_env().default_tier == ModelTier.AUTO

    monkeypatch.setenv("NANOBANANA_MODEL", "NB2")
    assert ModelSelectionConfig.from_env().default_tier == ModelTier.NB2

    monkeypatch.setenv("NANOBANANA_MODEL", "not-a-tier")
    assert ModelSelectionConfig.from_env().default_tier == ModelTier.AUTO
