"""
Nano Banana MCP Server - AI-powered image generation and editing via Gemini 2.5 Flash Image.

A production-ready Model Context Protocol server built with FastMCP.
"""

__version__ = "0.1.5"
__author__ = "Nano Banana Team"
__email__ = "team@nanobanana.dev"
__description__ = "A production-ready MCP server for AI-powered image generation using Gemini 2.5 Flash Image"

from .server import create_app, create_wrapper_app, main

__all__ = ["create_app", "create_wrapper_app", "main"]