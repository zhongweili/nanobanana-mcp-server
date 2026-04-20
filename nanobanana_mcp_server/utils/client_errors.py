"""Helpers for returning client-safe error messages (no internal detail leakage)."""


def should_mask_errors() -> bool:
    """True when FASTMCP_MASK_ERRORS / ServerConfig requests generic client errors."""
    try:
        from ..services import get_server_config

        return bool(get_server_config().mask_error_details)
    except RuntimeError:
        return False


def client_safe_message(
    detail: str,
    *,
    mask: bool | None = None,
    generic: str = "Request failed. See server logs for details.",
) -> str:
    """Return a generic message when masking is enabled, else the original detail."""
    if mask is None:
        mask = should_mask_errors()
    return generic if mask else detail
