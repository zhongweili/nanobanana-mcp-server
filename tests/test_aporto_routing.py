import os
from unittest.mock import patch

import pytest

from nanobanana_mcp_server.config.settings import ServerConfig
from nanobanana_mcp_server.core.exceptions import ValidationError
from nanobanana_mcp_server.services.aporto_routing_service import (
    NANO_BANANA_2_SKILL_IDS,
    NANO_BANANA_IMAGE_TO_IMAGE_SKILL_ID,
    AportoRoutingService,
)

pytestmark = pytest.mark.unit


def test_nano_banana_2_skill_ids_are_discovered_values():
    assert NANO_BANANA_2_SKILL_IDS == {
        "1k": 96,
        "2k": 95,
        "4k": 94,
    }
    assert NANO_BANANA_IMAGE_TO_IMAGE_SKILL_ID == 249


@pytest.mark.parametrize(
    ("resolution", "quality"),
    [
        ("1k", "1k"),
        ("low", "1k"),
        ("2k", "2k"),
        ("medium", "2k"),
        ("4k", "4k"),
        ("high", "4k"),
        (None, "4k"),
    ],
)
def test_resolve_quality(resolution, quality):
    assert AportoRoutingService.resolve_quality(resolution) == quality


def test_resolve_quality_rejects_unknown_resolution():
    with pytest.raises(ValidationError):
        AportoRoutingService.resolve_quality("8k")


def test_run_nano_banana_2_uses_direct_skill_id_and_extracts_task_id():
    service = AportoRoutingService("test-key")
    response = {
        "status": "running",
        "runId": "run_123",
        "result": {"taskId": "task_456"},
    }

    with patch.object(service, "_post_json", return_value=response) as post_json:
        results = service.run_nano_banana_2(prompt="cat", n=1, resolution="2k")

    post_json.assert_called_once()
    body = post_json.call_args.args[1]
    assert body["skillId"] == 95
    assert body["params"] == {"prompt": "cat"}
    assert body["waitForResult"] is False
    assert results[0]["run_id"] == "run_123"
    assert results[0]["task_id"] == "task_456"


def test_run_nano_banana_image_to_image_uses_direct_skill_id_and_image_urls():
    service = AportoRoutingService("test-key")
    response = {
        "status": "running",
        "runId": "run_789",
        "result": {"task_id": "task_999"},
    }

    with patch.object(service, "_post_json", return_value=response) as post_json:
        results = service.run_nano_banana_image_to_image(
            prompt="make it cinematic",
            image_urls=["https://example.com/image.png"],
            n=1,
        )

    body = post_json.call_args.args[1]
    assert body["skillId"] == 249
    assert body["params"] == {
        "prompt": "make it cinematic",
        "image_urls": ["https://example.com/image.png"],
    }
    assert body["waitForResult"] is False
    assert results[0]["run_id"] == "run_789"
    assert results[0]["task_id"] == "task_999"


def test_server_config_allows_aporto_only_auth():
    with patch("nanobanana_mcp_server.config.settings.load_dotenv"), patch.dict(
        os.environ,
        {"APORTO_API_KEY": "aporto-test-key"},
        clear=True,
    ):
        config = ServerConfig.from_env()

    assert config.gemini_api_key is None
    assert config.aporto_api_key == "aporto-test-key"
    assert config.aporto_nanobanana_enabled is True
