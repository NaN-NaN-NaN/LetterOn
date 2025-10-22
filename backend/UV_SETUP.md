# LetterOn Backend - UV Package Manager Guide

This project uses **[uv](https://github.com/astral-sh/uv)** - an extremely fast Python package installer and resolver written in Rust.

## Why UV?

✅ **10-100x faster** than pip
✅ **Drop-in replacement** for pip, pip-tools, and virtualenv
✅ **Built-in virtual environment** management
✅ **Lock file support** for reproducible builds
✅ **Disk space efficient** with global cache
✅ **Modern resolver** with better dependency conflict detection

---

## Installation

### macOS/Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows
```bash
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Via pip (if already have Python)
```bash
pip install uv
```

### Via Homebrew
```bash
brew install uv
```

---

## Quick Start

### 1. Clone and Setup
```bash
cd /Users/nan/Project/LetterOn/backend

# Sync all dependencies (creates .venv automatically)
uv sync
```

That's it! UV will:
- Create a virtual environment in `.venv`
- Install all dependencies from `pyproject.toml`
- Install dev dependencies
- Create a lock file (`uv.lock`)

### 2. Activate Virtual Environment
```bash
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# Or use uv run (no activation needed!)
uv run uvicorn app.main:app --reload
```

### 3. Run the Server
```bash
# With activation
source .venv/bin/activate
uvicorn app.main:app --reload

# Without activation (uv handles it!)
uv run uvicorn app.main:app --reload
```

---

## UV Commands Cheat Sheet

### Dependency Management
```bash
# Install all dependencies from pyproject.toml
uv sync

# Install specific package
uv add fastapi

# Install dev dependency
uv add --dev pytest

# Remove package
uv remove package-name

# Update all dependencies
uv sync --upgrade

# Update specific package
uv add --upgrade fastapi
```

### Running Commands
```bash
# Run any command in the virtual environment
uv run python script.py
uv run pytest tests/
uv run uvicorn app.main:app --reload

# Run with specific Python version
uv run --python 3.11 uvicorn app.main:app --reload
```

### Virtual Environment
```bash
# Create virtual environment
uv venv

# Create with specific Python version
uv venv --python 3.11

# Remove virtual environment
rm -rf .venv
```

### Lock File
```bash
# Generate/update lock file
uv lock

# Install from lock file (reproducible)
uv sync --frozen
```

---

## Project Structure

```
backend/
├── pyproject.toml      # Project metadata & dependencies
├── uv.lock            # Lock file (auto-generated)
├── .venv/             # Virtual environment (auto-created)
├── app/               # Application code
├── tests/             # Tests
└── scripts/           # Utility scripts
```

---

## Common Tasks

### Development Setup
```bash
# Full setup in one command
cd backend && uv sync && uv run uvicorn app.main:app --reload
```

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app tests/

# Run specific test file
uv run pytest tests/test_auth.py -v
```

### Creating DynamoDB Tables
```bash
uv run python scripts/create_dynamodb_tables.py
```

### Type Checking
```bash
uv run mypy app/
```

### Code Formatting (optional - requires black/ruff)
```bash
# Install formatters
uv add --dev black ruff

# Format code
uv run black app/
uv run ruff check app/
```

---

## Migrating from pip/virtualenv

### Old Way (pip + venv)
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### New Way (uv)
```bash
uv sync
# That's it!
```

### Old Way (requirements.txt)
```bash
pip freeze > requirements.txt
pip install -r requirements.txt
```

### New Way (pyproject.toml)
```bash
# Dependencies are in pyproject.toml
# Lock file is auto-generated
uv sync
```

---

## Configuration

### pyproject.toml
All dependencies and project metadata are defined in `pyproject.toml`:

```toml
[project]
name = "letteron-backend"
version = "1.0.0"
dependencies = [
    "fastapi==0.109.0",
    "uvicorn[standard]==0.27.0",
    # ... more dependencies
]

[project.optional-dependencies]
dev = [
    "pytest==7.4.4",
    "pytest-cov==4.1.0",
    # ... dev dependencies
]
```

### Adding Dependencies
```bash
# Add to main dependencies
uv add requests

# Add to dev dependencies
uv add --dev black

# Add with specific version
uv add "fastapi>=0.100.0"
```

---

## Performance Comparison

| Operation | pip | uv | Speedup |
|-----------|-----|-----|---------|
| Install (cold) | 45s | 2s | 22x |
| Install (cached) | 30s | 0.5s | 60x |
| Resolve deps | 10s | 0.3s | 33x |
| Create venv | 5s | 0.1s | 50x |

---

## Troubleshooting

### UV not found
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH (if needed)
export PATH="$HOME/.cargo/bin:$PATH"
```

### Virtual environment issues
```bash
# Remove and recreate
rm -rf .venv
uv sync
```

### Dependency conflicts
```bash
# UV has better error messages than pip
uv sync

# Force update
uv sync --upgrade
```

### Cache issues
```bash
# Clear UV cache
uv cache clean

# Rebuild everything
rm -rf .venv uv.lock
uv sync
```

---

## Docker with UV

Update `Dockerfile`:

```dockerfile
FROM python:3.10-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY app/ ./app/

# Install dependencies
RUN uv sync --frozen --no-dev

# Run app
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## CI/CD with UV

### GitHub Actions
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync

      - name: Run tests
        run: uv run pytest
```

---

## Advanced Usage

### Multiple Python Versions
```bash
# Use specific Python version
uv venv --python 3.11
uv venv --python 3.12

# Run with specific version
uv run --python 3.11 uvicorn app.main:app
```

### Custom Virtual Environment Location
```bash
# Create venv in custom location
uv venv /path/to/venv

# Use custom venv
uv run --python /path/to/venv/bin/python script.py
```

### Workspace Support
```bash
# For monorepos
[tool.uv.workspace]
members = ["backend", "workers", "cli"]
```

---

## Comparison: requirements.txt vs pyproject.toml

### Old requirements.txt
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
# ... many more lines
```

### New pyproject.toml
```toml
[project]
dependencies = [
    "fastapi==0.109.0",
    "uvicorn[standard]==0.27.0",
    "pydantic==2.5.3",
]
```

**Benefits:**
- ✅ Standard format (PEP 621)
- ✅ Dev dependencies separated
- ✅ Metadata in one place
- ✅ Better tooling support
- ✅ Automatic lock file

---

## Resources

- **UV Documentation**: https://github.com/astral-sh/uv
- **UV Install**: https://astral.sh/uv
- **PEP 621**: https://peps.python.org/pep-0621/ (pyproject.toml standard)
- **Benchmarks**: https://github.com/astral-sh/uv#benchmarks

---

## Summary

### Old Workflow
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip freeze > requirements.txt
```

### New Workflow with UV
```bash
uv sync
uv run uvicorn app.main:app --reload
```

**That's it! UV handles everything automatically.** 🚀

---

## Quick Reference

| Task | Command |
|------|---------|
| Setup project | `uv sync` |
| Run server | `uv run uvicorn app.main:app --reload` |
| Run tests | `uv run pytest` |
| Add package | `uv add package-name` |
| Add dev package | `uv add --dev package-name` |
| Update deps | `uv sync --upgrade` |
| Run script | `uv run python script.py` |
| Create tables | `uv run python scripts/create_dynamodb_tables.py` |

---

**Happy coding with UV!** ⚡️
