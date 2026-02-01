# Cache API Reference

::: data_loader.cache.CacheManager
    options:
      show_root_heading: true
      show_source: true

## CacheEntry

::: data_loader.cache.CacheEntry
    options:
      show_root_heading: true

## Usage Examples

### Getting Cache Stats

```python
from data_loader import DataLoader

loader = DataLoader()
cache = loader._cache

stats = cache.get_stats()
print(f"Total entries: {stats['total_entries']}")
print(f"Total size: {stats['total_size_mb']:.2f} MB")
```

### Cache Configuration

```python
# Set TTL
cache.ttl_days = 14

# Get cache directory
print(cache.cache_dir)
```

## Cache File Structure

Each cache entry is stored as a JSON file:

```json
{
  "data": { ... },
  "timestamp": 1706698200.0,
  "provider": "fmp",
  "key": "profile_AAPL",
  "ttl_days": 7
}
```
