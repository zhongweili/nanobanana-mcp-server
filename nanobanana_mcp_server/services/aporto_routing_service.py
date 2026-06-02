"""Aporto routing integration for Nano Banana 2 generation."""

import json
import logging
import time
from typing import Any
from urllib import error, request
from urllib.parse import urlparse

from ..core.exceptions import ValidationError

NANO_BANANA_2_SKILL_IDS = {
    "1k": 96,
    "2k": 95,
    "4k": 94,
}

NANO_BANANA_2_SKILL_NAMES = {
    "1k": "Image Generation Nano Banana 2 1K",
    "2k": "Image Generation Nano Banana 2 2K",
    "4k": "Image Generation Nano Banana 2 4K",
}

NANO_BANANA_IMAGE_TO_IMAGE_SKILL_ID = 249
NANO_BANANA_IMAGE_TO_IMAGE_SKILL_NAME = "Image Generation Nano Banana Image-to-Image"


class AportoRoutingService:
    """Minimal client for Aporto's routing API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://app.aporto.tech",
        integration_id: str | None = None,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.integration_id = integration_id.strip() if integration_id else None
        parsed = urlparse(self.base_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("Aporto base URL must be an HTTP(S) URL")
        self.logger = logging.getLogger(__name__)

    def run_nano_banana_2(
        self,
        *,
        prompt: str,
        n: int,
        resolution: str | None,
        wait_for_result: bool = False,
        max_wait_seconds: int = 600,
    ) -> list[dict[str, Any]]:
        """Submit one Aporto task per requested image and return run metadata."""
        quality = self.resolve_quality(resolution)
        skill_id = NANO_BANANA_2_SKILL_IDS[quality]
        skill_name = NANO_BANANA_2_SKILL_NAMES[quality]

        results = []
        for index in range(n):
            session_id = f"nanobanana-nb2-{quality}-{int(time.time() * 1000)}-{index + 1}"
            response = self._post_json(
                "/api/routing/run",
                {
                    "intent": skill_name,
                    "skillId": skill_id,
                    "params": {"prompt": prompt},
                    "waitForResult": wait_for_result,
                    "maxWaitSeconds": max_wait_seconds,
                    "sessionId": session_id,
                },
            )
            results.append(
                {
                    "provider": "aporto",
                    "skill_id": skill_id,
                    "skill_name": skill_name,
                    "quality": quality,
                    "run_id": response.get("runId"),
                    "status": response.get("status"),
                    "task_id": self._find_first_key(response, ("taskId", "task_id", "taskID")),
                    "integration_id": self.integration_id,
                    "artifact_urls": self._extract_urls(response),
                    "raw_response": response,
                }
            )
        return results

    def run_nano_banana_image_to_image(
        self,
        *,
        prompt: str,
        image_urls: list[str],
        n: int,
        wait_for_result: bool = False,
        max_wait_seconds: int = 600,
    ) -> list[dict[str, Any]]:
        """Submit one Aporto image-to-image task per requested image."""
        results = []
        for index in range(n):
            session_id = f"nanobanana-edit-{int(time.time() * 1000)}-{index + 1}"
            response = self._post_json(
                "/api/routing/run",
                {
                    "intent": NANO_BANANA_IMAGE_TO_IMAGE_SKILL_NAME,
                    "skillId": NANO_BANANA_IMAGE_TO_IMAGE_SKILL_ID,
                    "params": {
                        "prompt": prompt,
                        "image_urls": image_urls,
                    },
                    "waitForResult": wait_for_result,
                    "maxWaitSeconds": max_wait_seconds,
                    "sessionId": session_id,
                },
            )
            results.append(
                {
                    "provider": "aporto",
                    "skill_id": NANO_BANANA_IMAGE_TO_IMAGE_SKILL_ID,
                    "skill_name": NANO_BANANA_IMAGE_TO_IMAGE_SKILL_NAME,
                    "quality": "image-to-image",
                    "run_id": response.get("runId"),
                    "status": response.get("status"),
                    "task_id": self._find_first_key(response, ("taskId", "task_id", "taskID")),
                    "integration_id": self.integration_id,
                    "artifact_urls": self._extract_urls(response),
                    "raw_response": response,
                }
            )
        return results

    @staticmethod
    def resolve_quality(resolution: str | None) -> str:
        value = (resolution or "high").strip().lower()
        if value in ("1k", "low"):
            return "1k"
        if value in ("2k", "medium"):
            return "2k"
        if value in ("4k", "high"):
            return "4k"
        raise ValidationError("Resolution must be one of 'high', '4k', '2k', '1k'.")

    def _post_json(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(body).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Agent-Name": "nanobanana-mcp-server",
        }
        if self.integration_id:
            headers["X-Aporto-Integration-Id"] = self.integration_id

        req = request.Request(  # noqa: S310
            f"{self.base_url}{path}",
            data=payload,
            headers=headers,
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=30) as resp:  # noqa: S310
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Aporto routing failed: HTTP {exc.code} {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Aporto routing failed: {exc}") from exc

    @classmethod
    def _find_first_key(cls, value: Any, keys: tuple[str, ...]) -> Any:
        if isinstance(value, dict):
            for key in keys:
                if found := value.get(key):
                    return found
            for nested in value.values():
                found = cls._find_first_key(nested, keys)
                if found:
                    return found
        elif isinstance(value, list):
            for nested in value:
                found = cls._find_first_key(nested, keys)
                if found:
                    return found
        return None

    @classmethod
    def _extract_urls(cls, value: Any) -> list[str]:
        urls = []
        if isinstance(value, dict):
            for key, nested in value.items():
                if key in ("url", "imageUrl", "image_url") and isinstance(nested, str):
                    urls.append(nested)
                else:
                    urls.extend(cls._extract_urls(nested))
        elif isinstance(value, list):
            for nested in value:
                urls.extend(cls._extract_urls(nested))
        return urls
