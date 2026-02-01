# Installation

## Requirements

- Python 3.9 or higher
- pip package manager

## From Source

```bash
# Clone repository
git clone https://github.com/Maeshowe/Nexus_Core.git
cd Nexus_Core

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt
```

## Development Installation

For development (tests, linting, documentation):

```bash
pip install -r requirements-dev.txt
```

This includes:

- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **ruff** - Linting and formatting
- **mypy** - Type checking
- **mkdocs** - Documentation generation

## Verify Installation

```python
# Test import
python -c "from data_loader import DataLoader; print('OK')"
```

## Troubleshooting

### ModuleNotFoundError: No module named 'data_loader'

**Cause:** Package not installed or PYTHONPATH not set.

**Solution:**

```bash
# Option 1: Install in development mode
pip install -e .

# Option 2: Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Permission denied

**Cause:** Virtual environment not activated or wrong Python version.

**Solution:**

```bash
# Ensure virtual environment is active
source venv/bin/activate

# Check Python version
python --version  # Should be 3.9+
```
