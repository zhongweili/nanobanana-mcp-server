"""Tests for model ID environment overrides and config-driven metadata."""

from unittest.mock import MagicMock

import pytest

from nanobanana_mcp_server.config.settings import (
    FlashImageConfig,
    GeminiConfig,
    ModelSelectionConfig,
    ModelTier,
    NanoBanana2Config,
    ProImageConfig,
    ServerConfig,
    describe_default_model,
)
from nanobanana_mcp_server.services.gemini_client import GeminiClient
from nanobanana_mcp_server.services.model_selector import ModelSelector
from nanobanana_mcp_server.services.pro_image_service import ProImageService


def _disable_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "nanobanana_mcp_server.config.settings.load_dotenv",
        lambda *args, **kwargs: False,
    )


@pytest.mark.unit
def test_model_configs_default_when_env_unset_or_whitespace(monkeypatch: pytest.MonkeyPatch) -> None:
    _disable_dotenv(monkeypatch)
    for var in ("NANOBANANA_FLASH_MODEL", "NANOBANANA_PRO_MODEL", "NANOBANANA_NB2_MODEL"):
        monkeypatch.delenv(var, raising=False)

    assert FlashImageConfig.from_env().model_name == "gemini-2.5-flash-image"
    assert GeminiConfig.from_env().model_name == "gemini-2.5-flash-image"
    assert ProImageConfig.from_env().model_name == "gemini-3-pro-image-preview"
    assert NanoBanana2Config.from_env().model_name == "gemini-3.1-flash-image-preview"

    monkeypatch.setenv("NANOBANANA_FLASH_MODEL", "   ")
    monkeypatch.setenv("NANOBANANA_PRO_MODEL", "\t\n")
    monkeypatch.setenv("NANOBANANA_NB2_MODEL", "")

    assert FlashImageConfig.from_env().model_name == "gemini-2.5-flash-image"
    assert GeminiConfig.from_env().model_name == "gemini-2.5-flash-image"
    assert ProImageConfig.from_env().model_name == "gemini-3-pro-image-preview"
    assert NanoBanana2Config.from_env().model_name == "gemini-3.1-flash-image-preview"


@pytest.mark.unit
def test_model_configs_override_and_trim_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    _disable_dotenv(monkeypatch)
    monkeypatch.setenv("NANOBANANA_FLASH_MODEL", "  gemini-2.5-flash-custom  ")
    monkeypatch.setenv("NANOBANANA_PRO_MODEL", "  gemini-3-pro-image  ")
    monkeypatch.delenv("NANOBANANA_NB2_MODEL", raising=False)

    assert FlashImageConfig.from_env().model_name == "gemini-2.5-flash-custom"
    assert GeminiConfig.from_env().model_name == "gemini-2.5-flash-custom"
    assert ProImageConfig.from_env().model_name == "gemini-3-pro-image"
    # NanoBanana2Config subclasses ProImageConfig but must NOT inherit NANOBANANA_PRO_MODEL.
    assert NanoBanana2Config.from_env().model_name == "gemini-3.1-flash-image-preview"

    monkeypatch.setenv("NANOBANANA_NB2_MODEL", "  gemini-3.1-flash-image  ")
    assert NanoBanana2Config.from_env().model_name == "gemini-3.1-flash-image"


@pytest.mark.unit
def test_describe_default_model_reflects_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    _disable_dotenv(monkeypatch)
    monkeypatch.setenv("NANOBANANA_FLASH_MODEL", "gemini-2.5-flash-custom")
    monkeypatch.setenv("NANOBANANA_PRO_MODEL", "gemini-3-pro-image")
    monkeypatch.setenv("NANOBANANA_NB2_MODEL", "gemini-3.1-flash-image")

    assert describe_default_model(ModelTier.FLASH) == "flash (gemini-2.5-flash-custom)"
    assert describe_default_model(ModelTier.PRO) == "pro (gemini-3-pro-image)"
    assert describe_default_model(ModelTier.NB2) == "nb2 (gemini-3.1-flash-image)"
    auto_desc = describe_default_model(ModelTier.AUTO)
    assert "gemini-3.1-flash-image" in auto_desc
    assert "Pro" in auto_desc


@pytest.mark.unit
def test_pro_image_service_tier_label_uses_config_type() -> None:
    server_config = ServerConfig(gemini_api_key="test-key")

    nb2_cfg = NanoBanana2Config(model_name="gemini-3.1-flash-image")
    nb2_service = ProImageService(GeminiClient(server_config, nb2_cfg), nb2_cfg)
    assert nb2_service._tier_label == "nb2"

    pro_cfg = ProImageConfig(model_name="gemini-3-pro-image")
    pro_service = ProImageService(GeminiClient(server_config, pro_cfg), pro_cfg)
    assert pro_service._tier_label == "pro"


@pytest.mark.unit
def test_model_selector_get_model_info_reads_service_configs() -> None:
    server_config = ServerConfig(gemini_api_key="test-key")
    flash_cfg = GeminiConfig(model_name="gemini-2.5-flash-custom")
    pro_cfg = ProImageConfig(model_name="gemini-3-pro-image")
    nb2_cfg = NanoBanana2Config(model_name="gemini-3.1-flash-image")

    flash_service = MagicMock()
    flash_service.gemini_config = flash_cfg
    pro_service = ProImageService(GeminiClient(server_config, pro_cfg), pro_cfg)
    nb2_service = ProImageService(GeminiClient(server_config, nb2_cfg), nb2_cfg)

    selector = ModelSelector(
        flash_service=flash_service,
        pro_service=pro_service,
        nb2_service=nb2_service,
        selection_config=ModelSelectionConfig(),
    )

    assert selector.get_model_info(ModelTier.FLASH)["model_id"] == "gemini-2.5-flash-custom"
    assert selector.get_model_info(ModelTier.PRO)["model_id"] == "gemini-3-pro-image"
    assert selector.get_model_info(ModelTier.NB2)["model_id"] == "gemini-3.1-flash-image"


@pytest.mark.unit
def test_model_selector_get_model_info_falls_back_on_mocks() -> None:
    selector = ModelSelector(
        flash_service=MagicMock(),
        pro_service=MagicMock(),
        nb2_service=MagicMock(),
        selection_config=ModelSelectionConfig(),
    )

    assert selector.get_model_info(ModelTier.FLASH)["model_id"] == FlashImageConfig.model_name
    assert selector.get_model_info(ModelTier.PRO)["model_id"] == ProImageConfig.model_name
    assert selector.get_model_info(ModelTier.NB2)["model_id"] == NanoBanana2Config.model_name
