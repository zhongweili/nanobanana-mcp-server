#!/usr/bin/env python3
"""
Nano Banana MCP Server - Main Entry Point

A production-ready FastMCP server that provides AI-powered image generation and editing
capabilities through Google's Gemini 2.5 Flash Image model.
"""

import sys
import os
from .config.settings import ServerConfig, GeminiConfig
from .core.server import NanoBananaMCP
from .core.exceptions import ConfigurationError
from .utils.logging_utils import setup_logging
from . import services
import logging


def create_app():
    """
    Application factory function for FastMCP CLI.

    This function is used by FastMCP CLI as the server entrypoint.
    It can be called via: fastmcp dev server.py:create_app
    """
    # Set up logging if not already configured
    if not logging.getLogger().hasHandlers():
        log_level = os.getenv("LOG_LEVEL", "INFO")
        log_format = os.getenv("LOG_FORMAT", "standard")
        setup_logging(level=log_level, format_type=log_format)

    logger = logging.getLogger(__name__)
    logger.info("Initializing Nano Banana MCP Server...")

    try:
        # Load configuration
        server_config = ServerConfig.from_env()
        gemini_config = GeminiConfig()

        logger.info(f"Server transport: {server_config.transport}")
        logger.info(f"Gemini model: {gemini_config.model_name}")

        # Initialize services first
        services.initialize_services(server_config, gemini_config)

        # Get services from the global registry (don't create new instances)
        image_service = services.get_image_service()

        # Create and configure server
        app = NanoBananaMCP(server_config)

        # Inject dependencies from the global registry
        app.image_service = image_service

        logger.info("Server initialized successfully")

        # Return the inner FastMCP server instance for FastMCP CLI
        return app.server

    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        raise


def create_wrapper_app() -> NanoBananaMCP:
    """Create the complete application wrapper (for direct execution)."""
    # Set up logging if not already configured
    if not logging.getLogger().hasHandlers():
        log_level = os.getenv("LOG_LEVEL", "INFO")
        log_format = os.getenv("LOG_FORMAT", "standard")
        setup_logging(level=log_level, format_type=log_format)

    logger = logging.getLogger(__name__)
    logger.info("Initializing Nano Banana MCP Server...")

    try:
        # Load configuration
        server_config = ServerConfig.from_env()
        gemini_config = GeminiConfig()

        logger.info(f"Server transport: {server_config.transport}")
        logger.info(f"Gemini model: {gemini_config.model_name}")

        # Initialize services first
        services.initialize_services(server_config, gemini_config)

        # Get services from the global registry (don't create new instances)
        image_service = services.get_image_service()

        # Create and configure server
        app = NanoBananaMCP(server_config)

        # Inject dependencies from the global registry
        app.image_service = image_service

        logger.info("Server initialized successfully")
        return app

    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        raise


def main():
    """Main entry point for the server."""
    # Set up logging first
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_format = os.getenv("LOG_FORMAT", "standard")  # standard, json, detailed
    setup_logging(level=log_level, format_type=log_format)

    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting Nano Banana MCP Server...")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")

        # Create and run application wrapper
        app = create_wrapper_app()
        logger.info("Application initialized successfully")

        # Start the server
        logger.info("Starting FastMCP server...")
        app.run()

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
