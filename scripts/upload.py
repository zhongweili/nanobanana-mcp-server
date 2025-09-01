#!/usr/bin/env python3
"""
Upload script for Nano Banana MCP Server.

This script uploads the built distribution packages to PyPI using uv and twine.
Supports both TestPyPI (for testing) and production PyPI.
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import Optional


def run_command(cmd: list[str], description: str, capture_output: bool = True) -> Optional[str]:
    """Run a command and handle errors."""
    print(f"🚀 {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=capture_output, text=True)
        if result.stdout and capture_output:
            return result.stdout.strip()
        return None
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return None


def check_dependencies() -> bool:
    """Check if required dependencies are available."""
    print("🔍 Checking upload dependencies...")
    
    # Check uv
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        print("   ✅ uv is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ uv is not available. Please install uv first:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False
    
    # Check twine
    try:
        subprocess.run(["uv", "run", "python", "-c", "import twine"], 
                      check=True, capture_output=True)
        print("   ✅ twine is available")
    except subprocess.CalledProcessError:
        print("   📥 Installing twine...")
        result = subprocess.run(["uv", "add", "--dev", "twine"], capture_output=True)
        if result.returncode != 0:
            print("❌ Failed to install twine")
            return False
        print("   ✅ twine installed successfully")
    
    return True


def check_dist_files(root_dir: Path) -> list[Path]:
    """Check if distribution files exist and list them."""
    dist_dir = root_dir / "dist"
    
    if not dist_dir.exists():
        print("❌ No dist/ directory found. Please run build script first:")
        print("   uv run python scripts/build.py")
        return []
    
    dist_files = list(dist_dir.glob("*.tar.gz")) + list(dist_dir.glob("*.whl"))
    
    if not dist_files:
        print("❌ No distribution files found in dist/. Please run build script first:")
        print("   uv run python scripts/build.py")
        return []
    
    print(f"📁 Found {len(dist_files)} distribution files:")
    for file in dist_files:
        size = file.stat().st_size / 1024
        print(f"   - {file.name} ({size:.1f} KB)")
    
    return dist_files


def check_pypirc() -> tuple[bool, bool]:
    """Check if .pypirc is configured."""
    pypirc_path = Path.home() / ".pypirc"
    
    if not pypirc_path.exists():
        print("⚠️  No ~/.pypirc found. You'll need to enter credentials manually.")
        return False, False
    
    content = pypirc_path.read_text()
    has_testpypi = "[testpypi]" in content
    has_pypi = "[pypi]" in content
    
    print(f"📝 Found ~/.pypirc configuration:")
    print(f"   - TestPyPI configured: {'✅' if has_testpypi else '❌'}")
    print(f"   - PyPI configured: {'✅' if has_pypi else '❌'}")
    
    return has_testpypi, has_pypi


def show_pypirc_help():
    """Show help for configuring .pypirc."""
    print("\n📖 To configure ~/.pypirc with API tokens:")
    print("""
Create ~/.pypirc with this content:

[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-production-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-token-here

Get tokens from:
- TestPyPI: https://test.pypi.org/manage/account/token/
- PyPI: https://pypi.org/manage/account/token/
""")


def get_package_version(root_dir: Path) -> Optional[str]:
    """Extract package version from pyproject.toml."""
    pyproject_path = root_dir / "pyproject.toml"
    
    if not pyproject_path.exists():
        return None
    
    try:
        content = pyproject_path.read_text()
        for line in content.split('\n'):
            if line.strip().startswith('version = '):
                # Extract version from 'version = "0.1.0"'
                version = line.split('=')[1].strip().strip('"\'')
                return version
    except Exception:
        pass
    
    return None


def upload_to_repository(repository: str, dist_files: list[Path]) -> bool:
    """Upload to specified repository."""
    repo_name = "TestPyPI" if repository == "testpypi" else "PyPI"
    
    print(f"\n🚀 Uploading to {repo_name}...")
    print("=" * 40)
    
    # First, check the package
    print("🔍 Checking package integrity...")
    check_result = subprocess.run(
        ["uv", "run", "twine", "check"] + [str(f) for f in dist_files],
        capture_output=True, text=True
    )
    
    if check_result.returncode != 0:
        print("❌ Package check failed:")
        print(check_result.stderr)
        return False
    print("   ✅ Package check passed")
    
    # Prepare twine command
    cmd = ["uv", "run", "twine", "upload"]
    
    if repository == "testpypi":
        cmd.extend(["--repository", "testpypi"])
    
    # Add files
    cmd.extend([str(f) for f in dist_files])
    
    print(f"Running: {' '.join(cmd[2:])}")  # Hide uv run for cleaner output
    
    try:
        result = subprocess.run(cmd, check=True, text=True)
        print(f"✅ Successfully uploaded to {repo_name}!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Upload to {repo_name} failed")
        print(f"Error: {e}")
        return False


def show_next_steps(repository: str, version: str):
    """Show next steps after successful upload."""
    if repository == "testpypi":
        print("\n🎉 Upload to TestPyPI successful!")
        print("\nNext steps:")
        print("1. Test installation from TestPyPI:")
        print(f"   uvx --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ nanobanana-mcp-server")
        print("\n2. Test the installed package:")
        print("   nanobanana-mcp-server --help")
        print("   nanobanana-mcp --help")
        print("\n3. If testing is successful, upload to production PyPI:")
        print("   uv run python scripts/upload.py")
        print("   Choose option 2 for PyPI")
    else:
        print("\n🎉 Upload to PyPI successful!")
        print("\nYour package is now live! Users can install it with:")
        print(f"   uvx nanobanana-mcp-server")
        print(f"   pip install nanobanana-mcp-server")
        print(f"\nPackage URL: https://pypi.org/project/nanobanana-mcp-server/{version}/")
        print("\nDon't forget to:")
        print("1. Create a GitHub release tag")
        print("2. Update documentation with installation instructions")
        print("3. Announce the release!")


def main():
    """Main upload workflow."""
    root_dir = Path(__file__).parent.parent
    print("📤 Nano Banana MCP Server - PyPI Upload")
    print("=" * 50)
    
    # Change to project root
    os.chdir(root_dir)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check distribution files
    dist_files = check_dist_files(root_dir)
    if not dist_files:
        sys.exit(1)
    
    # Get package version
    version = get_package_version(root_dir)
    if version:
        print(f"📦 Package version: {version}")
    
    # Check .pypirc configuration
    has_testpypi, has_pypi = check_pypirc()
    
    # Interactive menu
    print("\n🎯 Upload destination:")
    print("1. TestPyPI (recommended for testing)")
    print("2. PyPI (production)")
    print("3. Show .pypirc configuration help")
    print("4. Exit")
    
    while True:
        try:
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                if upload_to_repository("testpypi", dist_files):
                    show_next_steps("testpypi", version or "latest")
                break
            
            elif choice == "2":
                # Confirm production upload
                print("\n⚠️  You're about to upload to production PyPI!")
                print("This cannot be undone. Make sure you've tested on TestPyPI first.")
                confirm = input("Continue? (yes/no): ").strip().lower()
                
                if confirm in ("yes", "y"):
                    if upload_to_repository("pypi", dist_files):
                        show_next_steps("pypi", version or "latest")
                else:
                    print("Upload cancelled.")
                break
            
            elif choice == "3":
                show_pypirc_help()
                continue
            
            elif choice == "4":
                print("Upload cancelled.")
                break
            
            else:
                print("Invalid choice. Please select 1-4.")
        
        except KeyboardInterrupt:
            print("\n\nUpload cancelled.")
            sys.exit(0)


if __name__ == "__main__":
    main()