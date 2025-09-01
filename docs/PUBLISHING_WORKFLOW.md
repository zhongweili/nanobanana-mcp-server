# PyPI Publishing Workflow - Reusable Guide

This is a streamlined, reusable workflow for publishing Python packages to PyPI using modern tooling (uv, automated scripts).

## 🚀 Quick Publishing Workflow

### One-Command Publishing
```bash
# Build and upload in one go (recommended)
uv run python scripts/build.py && uv run python scripts/upload.py
```

### Step-by-Step Workflow
```bash
# 1. Build the package
uv run python scripts/build.py

# 2. Upload to PyPI
uv run python scripts/upload.py
# Choose 1 for TestPyPI (testing)
# Choose 2 for PyPI (production)
```

## 📋 Prerequisites Checklist

### One-Time Setup
- [ ] PyPI account created: https://pypi.org/account/register/
- [ ] TestPyPI account created: https://test.pypi.org/account/register/
- [ ] API tokens generated for both accounts
- [ ] `~/.pypirc` file configured (see configuration below)

### Before Each Release
- [ ] Version updated in `pyproject.toml`
- [ ] Version updated in `nanobanana_mcp_server/__init__.py`
- [ ] CHANGELOG updated (if you maintain one)
- [ ] All tests pass: `uv run pytest`
- [ ] Code formatted: `uv run ruff format .`
- [ ] Linting passes: `uv run ruff check .`

## ⚙️ Configuration

### ~/.pypirc Configuration
Create `~/.pypirc` in your home directory:

```ini
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
```

### Getting API Tokens
1. **TestPyPI Token**: https://test.pypi.org/manage/account/token/
   - Create token with scope "Entire account"
   - Copy token (starts with `pypi-`)

2. **PyPI Token**: https://pypi.org/manage/account/token/  
   - Create token with scope "Entire account"
   - Copy token (starts with `pypi-`)

## 🏗️ Build Script Features

The automated build script (`scripts/build.py`) includes:

- ✅ **Dependency Check**: Ensures uv and build tools are available
- ✅ **Package Verification**: Validates pyproject.toml and required files
- ✅ **Clean Build**: Removes old artifacts before building
- ✅ **Size Reporting**: Shows package sizes after build
- ✅ **Error Handling**: Clear error messages and troubleshooting hints

### Build Script Usage
```bash
# Standard build
uv run python scripts/build.py

# The script will:
# 1. Check that uv is available
# 2. Install build dependencies if needed
# 3. Verify package configuration
# 4. Clean previous builds
# 5. Create new distribution files
# 6. Report file sizes and next steps
```

## 📤 Upload Script Features

The automated upload script (`scripts/upload.py`) includes:

- ✅ **Interactive Menu**: Choose TestPyPI or PyPI
- ✅ **Dependency Check**: Ensures twine is available
- ✅ **File Validation**: Checks distribution files exist and are valid
- ✅ **Package Integrity**: Runs `twine check` before upload
- ✅ **Configuration Check**: Verifies ~/.pypirc setup
- ✅ **Safety Confirmation**: Requires confirmation for production uploads
- ✅ **Next Steps Guidance**: Shows installation commands after upload

### Upload Script Usage
```bash
# Interactive upload
uv run python scripts/upload.py

# The script provides a menu:
# 1. TestPyPI (recommended for testing)
# 2. PyPI (production)  
# 3. Show .pypirc configuration help
# 4. Exit
```

## 🧪 Testing Workflow

### 1. Test on TestPyPI First
```bash
# Build and upload to TestPyPI
uv run python scripts/build.py
uv run python scripts/upload.py
# Choose option 1 (TestPyPI)
```

### 2. Test Installation from TestPyPI
```bash
# Test with uvx (recommended)
uvx --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ nanobanana-mcp-server

# Test the commands work
nanobanana-mcp-server --help
nanobanana-mcp --help
```

### 3. If Testing Passes, Upload to Production
```bash
uv run python scripts/upload.py
# Choose option 2 (PyPI)
# Confirm with 'yes'
```

## 🔄 Version Management

### Updating Version for New Release
```bash
# 1. Update version in pyproject.toml
# From: version = "0.1.0"  
# To:   version = "0.1.1"

# 2. Update version in package __init__.py
# From: __version__ = "0.1.0"
# To:   __version__ = "0.1.1"

# 3. Build and upload
uv run python scripts/build.py
uv run python scripts/upload.py
```

### Semantic Versioning Guidelines
- **Patch** (0.1.0 → 0.1.1): Bug fixes, minor improvements
- **Minor** (0.1.0 → 0.2.0): New features, backward compatible
- **Major** (0.1.0 → 1.0.0): Breaking changes

## 📁 Generated Files Structure

After building, you'll have:
```
dist/
├── nanobanana-mcp-server-0.1.0.tar.gz    # Source distribution
└── nanobanana_mcp_server-0.1.0-py3-none-any.whl  # Wheel distribution
```

Both files are uploaded to PyPI for maximum compatibility.

## 🚨 Troubleshooting

### Common Issues and Solutions

**Issue**: `uv not found`
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Issue**: `No distribution files found`
```bash
# Run build script first
uv run python scripts/build.py
```

**Issue**: `Authentication failed`
```bash
# Check ~/.pypirc configuration
uv run python scripts/upload.py
# Choose option 3 for configuration help
```

**Issue**: `Package already exists`
- You cannot re-upload the same version
- Update version in pyproject.toml and __init__.py
- Rebuild and upload

**Issue**: `twine check failed`
- Check package metadata in pyproject.toml
- Ensure README.md exists and is properly formatted
- Verify all required fields are present

## ✅ Post-Publication Checklist

After successful PyPI upload:

- [ ] Test installation: `uvx nanobanana-mcp-server`
- [ ] Create GitHub release tag: `git tag v0.1.0 && git push --tags`
- [ ] Update project README with installation instructions
- [ ] Announce the release (social media, forums, etc.)
- [ ] Monitor for issues and user feedback

## 🔄 Automating with GitHub Actions (Optional)

For fully automated publishing on git tags, add `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Install uv
      uses: astral-sh/setup-uv@v1
      
    - name: Set up Python
      run: uv python install 3.11
      
    - name: Build package
      run: uv run python scripts/build.py
      
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: uv run twine upload dist/*
```

Add your PyPI API token as `PYPI_API_TOKEN` in GitHub repository secrets.

## 📝 Summary

This workflow provides:
- **Automated scripts** for building and uploading
- **Safety checks** and validation at each step  
- **Interactive guidance** for first-time users
- **Reusable process** for all future releases
- **Modern tooling** with uv for speed and reliability

The entire process from build to production can be completed in under 5 minutes with this streamlined workflow!