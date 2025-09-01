#!/usr/bin/env python3
"""
Structure validation script for Nano Banana MCP Server.
Validates the project structure without requiring external dependencies.
"""

import os
import sys


def check_file_exists(file_path: str, description: str) -> bool:
    """Check if a file exists and report status."""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (MISSING)")
        return False


def check_directory_exists(dir_path: str, description: str) -> bool:
    """Check if a directory exists and report status."""
    if os.path.isdir(dir_path):
        print(f"✅ {description}: {dir_path}/")
        return True
    else:
        print(f"❌ {description}: {dir_path}/ (MISSING)")
        return False


def check_python_syntax(file_path: str) -> bool:
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, "r") as f:
            compile(f.read(), file_path, "exec")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return False


def main():
    """Main validation function."""
    print("🔍 Nano Banana MCP Server - Structure Validation")
    print("=" * 50)

    all_checks_passed = True

    # Core files
    print("\n📋 Core Files:")
    core_files = [
        ("server.py", "Main server entry point"),
        (".env.example", "Environment template"),
        ("README.md", "Documentation"),
        ("pyproject.toml", "Project configuration"),
    ]

    for file_path, description in core_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False

    # Directory structure
    print("\n📁 Directory Structure:")
    directories = [
        ("config", "Configuration management"),
        ("core", "Core functionality"),
        ("services", "Business logic services"),
        ("tools", "MCP tools"),
        ("resources", "MCP resources"),
        ("prompts", "Prompt templates"),
        ("utils", "Utility functions"),
        ("tests", "Test suite"),
    ]

    for dir_path, description in directories:
        if not check_directory_exists(dir_path, description):
            all_checks_passed = False

    # Module files
    print("\n🐍 Python Modules:")
    python_files = [
        "config/settings.py",
        "config/constants.py",
        "core/server.py",
        "core/exceptions.py",
        "core/validation.py",
        "services/gemini_client.py",
        "services/image_service.py",
        "services/file_service.py",
        "tools/generate_image.py",
        "tools/edit_image.py",
        "tools/upload_file.py",
        "resources/file_metadata.py",
        "resources/template_catalog.py",
        "prompts/photography.py",
        "prompts/design.py",
        "prompts/editing.py",
        "utils/image_utils.py",
        "utils/logging_utils.py",
        "utils/validation_utils.py",
    ]

    for file_path in python_files:
        if check_file_exists(file_path, f"Module {file_path}"):
            if not check_python_syntax(file_path):
                all_checks_passed = False
        else:
            all_checks_passed = False

    # __init__.py files
    print("\n📦 Package Init Files:")
    init_files = [
        "config/__init__.py",
        "core/__init__.py",
        "services/__init__.py",
        "tools/__init__.py",
        "resources/__init__.py",
        "prompts/__init__.py",
        "utils/__init__.py",
        "tests/__init__.py",
    ]

    for init_file in init_files:
        if not check_file_exists(init_file, f"Package init {init_file}"):
            all_checks_passed = False

    # Summary
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 All structure validation checks PASSED!")
        print("✅ Server is ready for dependency installation and testing.")
        print("\nNext steps:")
        print("1. Install dependencies: uv sync")
        print("2. Set up environment: cp .env.example .env")
        print("3. Add your GEMINI_API_KEY to .env")
        print("4. Run server: uv run python -m nanobanana_mcp_server.server")
        return 0
    else:
        print("❌ Some validation checks FAILED!")
        print("Please fix the missing files/directories before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
