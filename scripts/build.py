#!/usr/bin/env python3
"""
Build script for Nano Banana MCP Server.

This script builds the distribution packages for PyPI upload using uv.
"""

import subprocess
import sys
import shutil
from pathlib import Path


def run_command(cmd: list[str], description: str, capture_output: bool = True) -> None:
    """Run a command and handle errors."""
    print(f"🔨 {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=capture_output, text=True)
        if result.stdout and capture_output:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        sys.exit(1)


def clean_build_artifacts(root_dir: Path) -> None:
    """Clean previous build artifacts."""
    print("🧹 Cleaning previous build artifacts...")
    
    # Directories to clean
    dirs_to_clean = [
        root_dir / "dist",
        root_dir / "build", 
        root_dir / "*.egg-info"
    ]
    
    for path in dirs_to_clean:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
                print(f"   - Removed directory: {path.name}")
            else:
                path.unlink()
                print(f"   - Removed file: {path.name}")
    
    # Also clean any .egg-info directories with glob
    for egg_info in root_dir.glob("*.egg-info"):
        if egg_info.is_dir():
            shutil.rmtree(egg_info)
            print(f"   - Removed .egg-info: {egg_info.name}")


def check_uv_available() -> bool:
    """Check if uv is available."""
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_build_deps(root_dir: Path) -> None:
    """Install build dependencies if not available."""
    print("📦 Checking build dependencies...")
    
    if not check_uv_available():
        print("❌ uv is not available. Please install uv first:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        sys.exit(1)
    
    # Check if build is available
    try:
        subprocess.run(["uv", "run", "python", "-c", "import build"], 
                      check=True, capture_output=True)
        print("   ✅ build package is available")
    except subprocess.CalledProcessError:
        print("   📥 Installing build package...")
        run_command(["uv", "add", "--dev", "build"], "Installing build dependency")


def verify_package_config(root_dir: Path) -> None:
    """Verify package configuration is ready for build."""
    print("🔍 Verifying package configuration...")
    
    # Check required files
    required_files = [
        ("pyproject.toml", "Project configuration"),
        ("nanobanana_mcp_server/__init__.py", "Package init"),
        ("nanobanana_mcp_server/server.py", "Main server module"),
    ]
    
    for file_path, description in required_files:
        full_path = root_dir / file_path
        if not full_path.exists():
            print(f"❌ Missing {description}: {file_path}")
            sys.exit(1)
        print(f"   ✅ {description}: {file_path}")


def main():
    """Build the package."""
    root_dir = Path(__file__).parent.parent
    print(f"📦 Building Nano Banana MCP Server from {root_dir}")
    print("=" * 60)
    
    # Change to project root
    import os
    os.chdir(root_dir)
    
    # Verify configuration
    verify_package_config(root_dir)
    
    # Install build dependencies
    install_build_deps(root_dir)
    
    # Clean previous builds
    clean_build_artifacts(root_dir)
    
    # Build the package
    print("\n🏗️  Building distribution packages...")
    run_command(["uv", "run", "python", "-m", "build"], "Building source and wheel distributions")
    
    print("\n✅ Build completed successfully!")
    print("📁 Distribution files created in dist/:")
    
    # List created files with details
    dist_dir = root_dir / "dist"
    if dist_dir.exists():
        total_size = 0
        for file in sorted(dist_dir.iterdir()):
            if file.is_file():
                size = file.stat().st_size
                total_size += size
                size_kb = size / 1024
                print(f"   - {file.name} ({size_kb:.1f} KB)")
        
        print(f"\nTotal package size: {total_size / 1024:.1f} KB")
    
    print("\n🚀 Ready for upload to PyPI!")
    print("Next steps:")
    print("   1. Test upload: uv run python scripts/upload.py")
    print("   2. Choose TestPyPI first for testing")
    print("   3. Then upload to production PyPI")


if __name__ == "__main__":
    main()