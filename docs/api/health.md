# Health Monitoring API Reference

::: data_loader.health.HealthMonitor
    options:
      show_root_heading: true
      show_source: true

## ProviderStatus

::: data_loader.health.ProviderStatus
    options:
      show_root_heading: true

## Health Report Structure

```python
report = loader.get_api_health_report()
```

Returns:

```python
{
    "operating_mode": "LIVE",
    "overall_status": "OK",  # or "DEGRADED" or "FAIL"
    "providers": {
        "fmp": {
            "status": "OK",
            "total_requests": 150,
            "successful_requests": 148,
            "failed_requests": 2,
            "error_rate": 0.013,
            "last_success": "2025-01-31T10:30:00Z",
            "last_error": "2025-01-31T09:15:00Z"
        },
        ...
    },
    "circuit_breakers": {
        "fmp": {
            "state": "CLOSED",
            "failure_count": 0
        },
        ...
    }
}
```

## Status Levels

| Status | Meaning |
|--------|---------|
| `OK` | Provider functioning normally |
| `DEGRADED` | Some errors but still operational |
| `FAIL` | Provider unavailable |

## Usage Examples

### Check Before Requests

```python
report = loader.get_api_health_report()

if report['providers']['fmp']['status'] == 'FAIL':
    print("FMP is down, using cached data only")
    loader.set_operating_mode(OperatingMode.READ_ONLY)
```

### Monitor Error Rates

```python
for provider, metrics in report['providers'].items():
    if metrics['error_rate'] > 0.1:  # More than 10% errors
        print(f"⚠️ {provider} has high error rate: {metrics['error_rate']:.1%}")
```
