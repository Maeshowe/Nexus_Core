#!/usr/bin/env python3
"""
Performance Benchmark Tool - OmniData Nexus Core

Measures and reports performance metrics:
- API latency per provider
- Cache hit/miss performance
- Concurrent request throughput
- Memory usage

Usage:
    python tools/benchmarks/benchmark.py [--full]

Options:
    --full    Run comprehensive benchmarks (takes longer)
"""

import asyncio
import argparse
import gc
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import aiohttp
from data_loader import DataLoader


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    name: str
    iterations: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    std_dev_ms: float
    throughput_per_sec: float
    cache_hit_rate: float = 0.0
    errors: int = 0
    details: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return (
            f"{self.name}:\n"
            f"  Iterations: {self.iterations}\n"
            f"  Total time: {self.total_time_ms:.1f}ms\n"
            f"  Avg: {self.avg_time_ms:.2f}ms | Min: {self.min_time_ms:.2f}ms | Max: {self.max_time_ms:.2f}ms\n"
            f"  Std Dev: {self.std_dev_ms:.2f}ms\n"
            f"  Throughput: {self.throughput_per_sec:.1f} req/sec\n"
            f"  Cache hit rate: {self.cache_hit_rate:.1%}\n"
            f"  Errors: {self.errors}"
        )


class Benchmark:
    """Performance benchmark suite."""

    def __init__(self):
        self.results: list[BenchmarkResult] = []

    async def run_latency_benchmark(
        self,
        provider: str,
        endpoint: str,
        params: dict,
        iterations: int = 10
    ) -> BenchmarkResult:
        """Benchmark API/cache latency for a specific endpoint."""
        loader = DataLoader()
        times_ms = []
        cache_hits = 0
        errors = 0

        async with aiohttp.ClientSession() as session:
            for i in range(iterations):
                gc.collect()  # Minimize GC interference

                start = time.perf_counter()
                try:
                    if provider == "fmp":
                        response = await loader.get_fmp_data(session, endpoint, **params)
                    elif provider == "polygon":
                        response = await loader.get_polygon_data(session, endpoint, **params)
                    elif provider == "fred":
                        response = await loader.get_fred_data(session, endpoint, **params)
                    else:
                        raise ValueError(f"Unknown provider: {provider}")

                    elapsed_ms = (time.perf_counter() - start) * 1000
                    times_ms.append(elapsed_ms)

                    if response.from_cache:
                        cache_hits += 1

                except Exception as e:
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    times_ms.append(elapsed_ms)
                    errors += 1
                    print(f"  Error in iteration {i+1}: {e}")

        total_time = sum(times_ms)
        avg_time = statistics.mean(times_ms) if times_ms else 0
        min_time = min(times_ms) if times_ms else 0
        max_time = max(times_ms) if times_ms else 0
        std_dev = statistics.stdev(times_ms) if len(times_ms) > 1 else 0
        throughput = (iterations / total_time * 1000) if total_time > 0 else 0
        cache_rate = cache_hits / iterations if iterations > 0 else 0

        result = BenchmarkResult(
            name=f"{provider}:{endpoint}",
            iterations=iterations,
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            std_dev_ms=std_dev,
            throughput_per_sec=throughput,
            cache_hit_rate=cache_rate,
            errors=errors,
        )
        self.results.append(result)
        return result

    async def run_cache_benchmark(self, iterations: int = 50) -> BenchmarkResult:
        """Benchmark cache read performance."""
        loader = DataLoader()
        times_ms = []

        async with aiohttp.ClientSession() as session:
            # First, ensure data is cached
            await loader.get_fmp_data(session, "profile", symbol="AAPL")

            # Now benchmark cache reads
            for _ in range(iterations):
                gc.collect()
                start = time.perf_counter()
                await loader.get_fmp_data(session, "profile", symbol="AAPL")
                elapsed_ms = (time.perf_counter() - start) * 1000
                times_ms.append(elapsed_ms)

        total_time = sum(times_ms)
        result = BenchmarkResult(
            name="Cache Read (FMP profile)",
            iterations=iterations,
            total_time_ms=total_time,
            avg_time_ms=statistics.mean(times_ms),
            min_time_ms=min(times_ms),
            max_time_ms=max(times_ms),
            std_dev_ms=statistics.stdev(times_ms) if len(times_ms) > 1 else 0,
            throughput_per_sec=(iterations / total_time * 1000) if total_time > 0 else 0,
            cache_hit_rate=1.0,  # All should be cache hits
            errors=0,
        )
        self.results.append(result)
        return result

    async def run_concurrent_benchmark(
        self,
        concurrent_requests: int = 5,
        symbols: Optional[list] = None
    ) -> BenchmarkResult:
        """Benchmark concurrent request handling."""
        loader = DataLoader()
        symbols = symbols or ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
        symbols = symbols[:concurrent_requests]

        async with aiohttp.ClientSession() as session:
            gc.collect()
            start = time.perf_counter()

            # Create concurrent tasks
            tasks = [
                loader.get_fmp_data(session, "profile", symbol=symbol)
                for symbol in symbols
            ]

            # Execute concurrently
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            total_time_ms = (time.perf_counter() - start) * 1000

        # Analyze results
        successful = sum(1 for r in responses if not isinstance(r, Exception) and r.success)
        errors = len(responses) - successful
        cache_hits = sum(
            1 for r in responses
            if not isinstance(r, Exception) and r.from_cache
        )

        result = BenchmarkResult(
            name=f"Concurrent Requests ({concurrent_requests} parallel)",
            iterations=concurrent_requests,
            total_time_ms=total_time_ms,
            avg_time_ms=total_time_ms / concurrent_requests,
            min_time_ms=total_time_ms / concurrent_requests,  # Approximate
            max_time_ms=total_time_ms,
            std_dev_ms=0,
            throughput_per_sec=(concurrent_requests / total_time_ms * 1000),
            cache_hit_rate=cache_hits / concurrent_requests if concurrent_requests > 0 else 0,
            errors=errors,
            details={"symbols": symbols, "successful": successful},
        )
        self.results.append(result)
        return result

    async def run_throughput_benchmark(
        self,
        duration_seconds: float = 5.0
    ) -> BenchmarkResult:
        """Benchmark maximum throughput over a time period."""
        loader = DataLoader()
        requests_completed = 0
        errors = 0
        cache_hits = 0

        async with aiohttp.ClientSession() as session:
            # Pre-warm cache
            await loader.get_fmp_data(session, "profile", symbol="AAPL")

            start = time.perf_counter()
            end_time = start + duration_seconds

            while time.perf_counter() < end_time:
                try:
                    response = await loader.get_fmp_data(
                        session, "profile", symbol="AAPL"
                    )
                    requests_completed += 1
                    if response.from_cache:
                        cache_hits += 1
                except Exception:
                    errors += 1
                    requests_completed += 1

            actual_duration = time.perf_counter() - start

        throughput = requests_completed / actual_duration if actual_duration > 0 else 0

        result = BenchmarkResult(
            name=f"Throughput Test ({duration_seconds}s)",
            iterations=requests_completed,
            total_time_ms=actual_duration * 1000,
            avg_time_ms=(actual_duration * 1000) / requests_completed if requests_completed > 0 else 0,
            min_time_ms=0,
            max_time_ms=0,
            std_dev_ms=0,
            throughput_per_sec=throughput,
            cache_hit_rate=cache_hits / requests_completed if requests_completed > 0 else 0,
            errors=errors,
        )
        self.results.append(result)
        return result

    def print_summary(self):
        """Print summary of all benchmark results."""
        print("\n" + "=" * 70)
        print("  BENCHMARK SUMMARY")
        print("=" * 70)

        for result in self.results:
            print(f"\n{result}")

        print("\n" + "=" * 70)


async def run_quick_benchmark():
    """Run a quick benchmark suite."""
    bench = Benchmark()

    print("\n" + "=" * 70)
    print("  OmniData Nexus Core - Performance Benchmark (Quick)")
    print("=" * 70)

    # API Latency benchmarks
    print("\n[1/4] API Latency Benchmarks...")

    print("  - FMP profile...")
    await bench.run_latency_benchmark("fmp", "profile", {"symbol": "AAPL"}, iterations=5)

    print("  - FRED series...")
    await bench.run_latency_benchmark("fred", "series", {"series_id": "UNRATE"}, iterations=5)

    # Cache benchmark
    print("\n[2/4] Cache Performance...")
    await bench.run_cache_benchmark(iterations=20)

    # Concurrent benchmark
    print("\n[3/4] Concurrent Requests...")
    await bench.run_concurrent_benchmark(concurrent_requests=5)

    # Throughput benchmark
    print("\n[4/4] Throughput Test...")
    await bench.run_throughput_benchmark(duration_seconds=2.0)

    bench.print_summary()


async def run_full_benchmark():
    """Run comprehensive benchmark suite."""
    bench = Benchmark()

    print("\n" + "=" * 70)
    print("  OmniData Nexus Core - Performance Benchmark (Full)")
    print("=" * 70)

    # API Latency benchmarks - all providers
    print("\n[1/5] API Latency Benchmarks...")

    print("  - FMP profile...")
    await bench.run_latency_benchmark("fmp", "profile", {"symbol": "AAPL"}, iterations=10)

    print("  - FMP quote...")
    await bench.run_latency_benchmark("fmp", "quote", {"symbol": "MSFT"}, iterations=10)

    print("  - FMP ratios...")
    await bench.run_latency_benchmark("fmp", "ratios", {"symbol": "GOOGL"}, iterations=10)

    print("  - Polygon aggs_daily...")
    await bench.run_latency_benchmark(
        "polygon", "aggs_daily",
        {"symbol": "SPY", "start": "2025-01-01", "end": "2025-01-31"},
        iterations=5
    )

    print("  - FRED UNRATE...")
    await bench.run_latency_benchmark("fred", "series", {"series_id": "UNRATE"}, iterations=10)

    print("  - FRED CPIAUCSL...")
    await bench.run_latency_benchmark("fred", "series", {"series_id": "CPIAUCSL"}, iterations=10)

    # Cache benchmark
    print("\n[2/5] Cache Performance...")
    await bench.run_cache_benchmark(iterations=100)

    # Concurrent benchmarks
    print("\n[3/5] Concurrent Requests...")
    await bench.run_concurrent_benchmark(concurrent_requests=3)
    await bench.run_concurrent_benchmark(concurrent_requests=5)
    await bench.run_concurrent_benchmark(concurrent_requests=10)

    # Throughput benchmark
    print("\n[4/5] Throughput Test...")
    await bench.run_throughput_benchmark(duration_seconds=5.0)

    # Cold start benchmark
    print("\n[5/5] Cold Start (API call, no cache)...")
    # Use a unique symbol to avoid cache
    await bench.run_latency_benchmark(
        "fmp", "profile",
        {"symbol": "IBM"},
        iterations=3
    )

    bench.print_summary()


def main():
    parser = argparse.ArgumentParser(description="OmniData Nexus Core Benchmark")
    parser.add_argument("--full", action="store_true", help="Run full benchmark suite")
    args = parser.parse_args()

    if args.full:
        asyncio.run(run_full_benchmark())
    else:
        asyncio.run(run_quick_benchmark())


if __name__ == "__main__":
    main()
