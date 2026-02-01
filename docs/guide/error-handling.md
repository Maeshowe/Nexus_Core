# Error Handling

OmniData Nexus Core includes a comprehensive resilience layer for handling API errors.

## Exception Hierarchy

```
DataLoaderError (base)
├── ProviderError
│   ├── RateLimitError
│   ├── AuthenticationError
│   └── EndpointNotFoundError
├── CircuitBreakerOpenError
├── ReadOnlyError
└── CacheError
```

## Common Errors

### RateLimitError

Raised when the API returns HTTP 429 (Too Many Requests).

```python
from data_loader.exceptions import RateLimitError

try:
    result = await loader.get_fmp_data(session, "profile", symbol="AAPL")
except RateLimitError as e:
    print(f"Rate limited: {e}")
    print(f"Retry after: {e.retry_after} seconds")
```

The system automatically applies exponential backoff before raising this error.

### CircuitBreakerOpenError

Raised when too many consecutive failures occur.

```python
from data_loader.exceptions import CircuitBreakerOpenError

try:
    result = await loader.get_fmp_data(session, "profile", symbol="AAPL")
except CircuitBreakerOpenError as e:
    print(f"Circuit open for {e.provider}")
    print(f"Recovery in: {e.recovery_time} seconds")
```

### ReadOnlyError

Raised in READ_ONLY mode when data is not cached.

```python
from data_loader.exceptions import ReadOnlyError

loader.set_operating_mode(OperatingMode.READ_ONLY)

try:
    result = await loader.get_fmp_data(session, "profile", symbol="UNKNOWN")
except ReadOnlyError as e:
    print(f"Not cached: {e.provider}:{e.endpoint}")
```

### ProviderError

General provider errors (5xx, network issues).

```python
from data_loader.exceptions import ProviderError

try:
    result = await loader.get_fmp_data(session, "profile", symbol="AAPL")
except ProviderError as e:
    print(f"Provider error: {e}")
    print(f"Status code: {e.status_code}")
```

## Resilience Patterns

### Circuit Breaker

Prevents cascading failures by opening the circuit after consecutive errors.

```
CLOSED → (failures ≥ threshold) → OPEN
OPEN → (timeout expires) → HALF_OPEN
HALF_OPEN → (success) → CLOSED
HALF_OPEN → (failure) → OPEN
```

Configuration:

| Parameter | Default | Description |
|-----------|---------|-------------|
| Failure threshold | 5 | Opens circuit after N failures |
| Recovery timeout | 60s | Time before trying again |
| Success threshold | 2 | Successes to close circuit |

### Exponential Backoff

Automatically retries failed requests with increasing delays.

```
Attempt 1: immediate
Attempt 2: wait 1s + jitter
Attempt 3: wait 2s + jitter
Attempt 4: wait 4s + jitter
(max 3 retries by default)
```

### Rate Limiting

Respects `Retry-After` headers and applies QoS limits:

| Provider | Concurrency |
|----------|-------------|
| FMP | 3 |
| Polygon | 10 |
| FRED | 1 |

## Error Handling Patterns

### Basic Try/Except

```python
from data_loader.exceptions import DataLoaderError

try:
    result = await loader.get_fmp_data(session, "profile", symbol="AAPL")
    process(result.data)
except DataLoaderError as e:
    log.error(f"Failed to fetch data: {e}")
```

### Specific Error Handling

```python
from data_loader.exceptions import (
    RateLimitError,
    CircuitBreakerOpenError,
    ReadOnlyError,
    ProviderError,
)

async def fetch_with_fallback(session, symbol: str):
    try:
        return await loader.get_fmp_data(session, "profile", symbol=symbol)
    except RateLimitError:
        # Wait and retry
        await asyncio.sleep(60)
        return await loader.get_fmp_data(session, "profile", symbol=symbol)
    except CircuitBreakerOpenError:
        # Try alternative provider or return cached
        return get_from_backup(symbol)
    except ReadOnlyError:
        # Data not available offline
        return None
    except ProviderError:
        # Log and continue
        log.warning(f"Could not fetch {symbol}")
        return None
```

### Graceful Degradation

```python
async def fetch_company_data(session, symbol: str) -> dict:
    """Fetch as much data as possible, even if some fails."""
    data = {}

    # Required data
    try:
        profile = await loader.get_fmp_data(session, "profile", symbol=symbol)
        data['profile'] = profile.data
    except DataLoaderError:
        raise  # Can't continue without profile

    # Optional data - continue if fails
    try:
        ratios = await loader.get_fmp_data(session, "ratios", symbol=symbol)
        data['ratios'] = ratios.data
    except DataLoaderError:
        data['ratios'] = None

    try:
        insider = await loader.get_fmp_data(session, "insider_trading", symbol=symbol)
        data['insider'] = insider.data
    except DataLoaderError:
        data['insider'] = None

    return data
```

## Health Monitoring

Check provider status before making requests:

```python
report = loader.get_api_health_report()

for provider, metrics in report['providers'].items():
    if metrics['status'] == 'FAIL':
        print(f"⚠️ {provider} is unhealthy")
        print(f"  Error rate: {metrics['error_rate']:.1%}")
        print(f"  Last error: {metrics['last_error']}")
```

## Debugging

Enable debug logging for detailed error information:

```python
import logging

logging.getLogger('data_loader').setLevel(logging.DEBUG)
```

Or in `.env`:

```bash
LOG_LEVEL=DEBUG
```
