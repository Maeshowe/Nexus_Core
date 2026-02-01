# OmniData Nexus Core Examples

This directory contains example scripts demonstrating various features of the DataLoader.

## Prerequisites

1. API keys configured in `.env`:
   ```bash
   FMP_KEY=your_fmp_key
   POLYGON_KEY=your_polygon_key
   FRED_KEY=your_fred_key
   ```

2. Package installed:
   ```bash
   pip install -e .
   # or
   export PYTHONPATH=src
   ```

## Examples

| File | Description |
|------|-------------|
| `01_quickstart.py` | Basic usage - fetch data from all providers |
| `02_multi_provider_analysis.py` | Comprehensive stock analysis combining FMP + Polygon + FRED |
| `03_caching_demo.py` | Intelligent caching demonstration |
| `04_error_handling.py` | Resilience and error handling patterns |
| `05_readonly_mode.py` | Offline analysis with READ_ONLY mode |
| `06_parallel_fetch.py` | Concurrent data fetching for portfolios |

## Running Examples

```bash
# From project root
cd Nexus_Core

# Run quickstart
python examples/01_quickstart.py

# Run all examples
for f in examples/*.py; do python "$f"; done
```

## Expected Output

Each example prints its results to the console. Data may come from cache if previously fetched.
