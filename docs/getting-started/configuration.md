# Configuration

## Environment Variables

OmniData Nexus Core uses environment variables for configuration. Copy the template and edit:

```bash
cp .env.example .env
nano .env  # or your preferred editor
```

## Required Variables

### API Keys

```bash
# Required for LIVE mode
FMP_KEY=your_fmp_api_key
POLYGON_KEY=your_polygon_api_key
FRED_KEY=your_fred_api_key
```

!!! warning "Security"
    Never commit API keys to version control. The `.env` file is in `.gitignore`.

### Getting API Keys

| Provider | Free Tier | Link |
|----------|-----------|------|
| FMP | 250 calls/day | [financialmodelingprep.com](https://financialmodelingprep.com/) |
| Polygon | Limited | [polygon.io](https://polygon.io/) |
| FRED | Unlimited | [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html) |

## Optional Variables

```bash
# Cache settings
CACHE_TTL_DAYS=7          # Cache expiration (default: 7)

# Logging
LOG_LEVEL=INFO            # DEBUG, INFO, WARNING, ERROR

# Operating mode
OPERATING_MODE=LIVE       # LIVE or READ_ONLY

# Network
REQUEST_TIMEOUT=30        # API timeout in seconds
```

## Operating Modes

### LIVE Mode (Default)

- Makes API calls when data not cached
- Caches responses automatically
- Requires valid API keys

### READ_ONLY Mode

- Only serves cached data
- No API calls made
- Useful for offline analysis or testing

```python
from data_loader import DataLoader, OperatingMode

loader = DataLoader()
loader.set_operating_mode(OperatingMode.READ_ONLY)
```

## Security Best Practices

```bash
# Secure the .env file (Linux/macOS)
chmod 600 .env

# Verify permissions
ls -la .env
# Should show: -rw-------
```

## Configuration in Code

You can also configure programmatically:

```python
from data_loader import DataLoader

loader = DataLoader()

# Override cache TTL
loader._cache.ttl_days = 14

# Check current mode
print(loader.get_operating_mode())
```
