import logging
import sys
from typing import Optional
import json
from datetime import datetime


def setup_logging(level: str = "INFO", format_type: str = "standard") -> None:
    """
    Set up logging configuration for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type ("standard", "json", "detailed")
    """

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Choose format based on type
    if format_type == "json":
        formatter = JSONFormatter()
    elif format_type == "detailed":
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s"
        )
    else:  # standard
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler - use stderr for MCP STDIO compatibility
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set specific loggers to appropriate levels
    logging.getLogger("google").setLevel(logging.WARNING)  # Reduce Google SDK noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)  # Reduce HTTP noise

    logging.info(f"Logging configured with level: {level}, format: {format_type}")


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""

        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
            ):
                log_entry[key] = value

        return json.dumps(log_entry)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


def log_function_call(
    logger: logging.Logger, func_name: str, args: Optional[dict] = None, level: str = "DEBUG"
) -> None:
    """Log a function call with arguments."""
    numeric_level = getattr(logging, level.upper(), logging.DEBUG)

    if args:
        # Sanitize sensitive information
        safe_args = sanitize_log_data(args)
        logger.log(numeric_level, f"Calling {func_name} with args: {safe_args}")
    else:
        logger.log(numeric_level, f"Calling {func_name}")


def log_function_result(
    logger: logging.Logger, func_name: str, result: Optional[dict] = None, level: str = "DEBUG"
) -> None:
    """Log a function result."""
    numeric_level = getattr(logging, level.upper(), logging.DEBUG)

    if result:
        # Sanitize sensitive information
        safe_result = sanitize_log_data(result)
        logger.log(numeric_level, f"{func_name} returned: {safe_result}")
    else:
        logger.log(numeric_level, f"{func_name} completed")


def sanitize_log_data(data: dict) -> dict:
    """Remove or mask sensitive information from log data."""
    sensitive_keys = {
        "api_key",
        "password",
        "token",
        "secret",
        "auth",
        "authorization",
        "credential",
        "key",
    }

    sanitized = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "***MASKED***"
        elif isinstance(value, str) and len(value) > 100:
            sanitized[key] = f"{value[:50]}...{value[-10:]}"  # Truncate long strings
        elif isinstance(value, dict):
            sanitized[key] = sanitize_log_data(value)
        else:
            sanitized[key] = value

    return sanitized


def log_performance_metric(
    logger: logging.Logger, operation: str, duration_ms: float, metadata: Optional[dict] = None
) -> None:
    """Log performance metrics."""
    perf_data = {
        "operation": operation,
        "duration_ms": round(duration_ms, 2),
        "type": "performance_metric",
    }

    if metadata:
        perf_data.update(sanitize_log_data(metadata))

    logger.info("Performance metric", extra=perf_data)


def log_api_call(
    logger: logging.Logger,
    api: str,
    method: str,
    url: str,
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
) -> None:
    """Log API calls."""
    api_data = {"api": api, "method": method, "url": url, "type": "api_call"}

    if status_code:
        api_data["status_code"] = status_code
    if duration_ms:
        api_data["duration_ms"] = round(duration_ms, 2)

    logger.info("API call", extra=api_data)


def log_error_with_context(
    logger: logging.Logger, error: Exception, context: Optional[dict] = None
) -> None:
    """Log error with additional context."""
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "type": "error_context",
    }

    if context:
        error_data["context"] = sanitize_log_data(context)

    logger.error("Error occurred", extra=error_data, exc_info=True)
