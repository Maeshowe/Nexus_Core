# Contributing

Thank you for your interest in contributing to OmniData Nexus Core!

## Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/Nexus_Core.git
cd Nexus_Core
```

### 2. Set Up Development Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
```

### 3. Run Tests

```bash
pytest
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow the coding standards below.

### 3. Run Quality Checks

```bash
# Linting
ruff check src/ tests/

# Type checking
mypy src/

# Tests with coverage
pytest --cov=src
```

### 4. Commit

```bash
git add .
git commit -m "feat: add your feature description"
```

Use conventional commit messages:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `chore:` Maintenance

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub.

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use `ruff` for linting and formatting

```bash
# Format code
ruff format src/ tests/

# Check linting
ruff check src/ tests/
```

### Docstrings

Use Google-style docstrings:

```python
def fetch_data(symbol: str, use_cache: bool = True) -> DataResult:
    """Fetch data for a symbol.

    Args:
        symbol: The stock symbol (e.g., "AAPL").
        use_cache: Whether to use cached data. Defaults to True.

    Returns:
        DataResult containing the fetched data.

    Raises:
        ProviderError: If the API request fails.
        RateLimitError: If rate limited.
    """
```

### Type Hints

```python
from typing import Optional

async def get_data(
    session: aiohttp.ClientSession,
    endpoint: str,
    *,
    symbol: Optional[str] = None,
) -> DataResult:
    ...
```

## Testing Guidelines

### Write Tests First

For new features, write tests before implementation.

### Test Categories

Mark tests appropriately:

```python
@pytest.mark.unit
def test_cache_key_generation():
    ...

@pytest.mark.integration
async def test_api_with_cache():
    ...

@pytest.mark.e2e
async def test_full_workflow():
    ...
```

### Coverage Requirements

- New code must have >90% coverage
- Don't decrease overall coverage

## Documentation

### Update Docs

When adding features, update:

1. Docstrings in code
2. Relevant guide pages in `docs/guide/`
3. API reference in `docs/api/`
4. CHANGELOG.md

### Build Docs Locally

```bash
mkdocs serve
# Open http://127.0.0.1:8000
```

## Adding a New Provider

1. Create provider class in `src/data_loader/providers/`
2. Inherit from `BaseDataProvider`
3. Define `ENDPOINTS` mapping
4. Implement `fetch()` method
5. Add to `DataLoader` class
6. Write tests
7. Document endpoints

Example:

```python
# src/data_loader/providers/new_provider.py
from .base import BaseDataProvider

class NewProvider(BaseDataProvider):
    ENDPOINTS = {
        "endpoint1": "/api/endpoint1",
        "endpoint2": "/api/endpoint2",
    }

    async def fetch(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        **params,
    ) -> dict:
        url = self._build_url(endpoint, params)
        return await self._request(session, url)
```

## Pull Request Checklist

- [ ] Tests pass (`pytest`)
- [ ] Linting passes (`ruff check`)
- [ ] Type checking passes (`mypy`)
- [ ] Coverage maintained (>90%)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commits follow conventional format

## Questions?

Open an issue on GitHub: [Nexus_Core Issues](https://github.com/Maeshowe/Nexus_Core/issues)
