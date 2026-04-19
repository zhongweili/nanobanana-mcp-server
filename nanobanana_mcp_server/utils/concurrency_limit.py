"""Limit concurrent MCP tool executions using ServerConfig.max_concurrent_requests."""

from __future__ import annotations

import functools
import logging
import threading
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

_sem: threading.Semaphore | None = None
_sem_lock = threading.Lock()
_sem_n: int | None = None

F = TypeVar("F", bound=Callable[..., Any])


def _get_tool_semaphore() -> threading.Semaphore:
    global _sem, _sem_n
    from ..services import get_server_config

    cfg = get_server_config()
    n = max(1, int(cfg.max_concurrent_requests))
    with _sem_lock:
        if _sem is None or _sem_n != n:
            _sem = threading.BoundedSemaphore(n)
            _sem_n = n
            logger.debug("Tool concurrency limit set to %s", n)
        return _sem


def limit_tool_concurrency(fn: F) -> F:
    """Block when max concurrent tool calls are in flight (thread-safe)."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        sem = _get_tool_semaphore()
        sem.acquire()
        try:
            return fn(*args, **kwargs)
        finally:
            sem.release()

    return wrapper  # type: ignore[return-value]
