from unittest.mock import Mock

import pytest
from google.genai import types as gx

from nanobanana_mcp_server.config.settings import NanoBanana2Config, ProImageConfig, ServerConfig
from nanobanana_mcp_server.services.gemini_client import GeminiClient


def _build_client(model_config):
    client = GeminiClient(ServerConfig(gemini_api_key="test-key"), model_config)
    client._client = Mock()
    client._client.models = Mock()
    client._client.models.generate_content = Mock(return_value=Mock())
    return client


@pytest.mark.unit
def test_nb2_thinking_level_becomes_thinking_config():
    client = _build_client(NanoBanana2Config())

    client.generate_content(contents=["test prompt"], config={"thinking_level": "high"})

    sent_config = client._client.models.generate_content.call_args.kwargs["config"]
    assert sent_config.thinking_config is not None
    assert sent_config.thinking_config.thinking_level == gx.ThinkingLevel.HIGH


@pytest.mark.unit
def test_pro_thinking_level_is_still_ignored():
    client = _build_client(ProImageConfig())

    client.generate_content(contents=["test prompt"], config={"thinking_level": "high"})

    sent_config = client._client.models.generate_content.call_args.kwargs["config"]
    assert sent_config.thinking_config is None
