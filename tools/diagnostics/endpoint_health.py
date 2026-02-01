"""
Endpoint Health Analyzer

Log parser and API endpoint health statistics generator.
Analyzes log files to detect rate-limits, errors, and API issues.

FEATURES:
- Parses Python logging format timestamps
- Detects FMP 429 rate-limit events (old and new format)
- Detects generic API errors (4xx, 5xx)
- Generates endpoint health heatmap
- Exports events to CSV for analysis

SUPPORTED LOG PATTERNS:
- "Rate Limit (429). Retrying in Xs... [URL]"
- "FMP 429 (endpoint). Cooling down Xs... [URL]"
- "API Error {status}: {url}"
- Standard Python logging: "YYYY-MM-DD HH:MM:SS,ms - LEVEL - message"

PROVIDERS DETECTED:
- FMP (financialmodelingprep.com)
- POLYGON (polygon.io)
- FRED (stlouisfed.org)
"""

import contextlib
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pandas as pd


@dataclass
class ApiEvent:
    """Represents a single API event extracted from logs."""
    ts: Optional[str]
    provider: str
    endpoint: str
    status: int
    url: str
    level: str
    raw: str


class EndpointHealth:
    """
    Log parser and endpoint health statistics generator.

    Parses log files to extract API events (errors, rate-limits) and
    generates summary statistics including a heatmap of issues by endpoint.
    """

    # Regex patterns for log parsing
    TS_RE = re.compile(
        r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d{3})\s+-\s+([A-Z]+)\s+-\s+(.*)$"
    )

    # Old format: "Rate Limit (429). Retrying in 1.27s... [https://.../stable/profile]"
    RL_OLD_RE = re.compile(r"Rate Limit\s+\(429\).*?\[(https?://[^\]]+)\]")

    # New format: "FMP 429 (insider-trading). Cooling down 9.1s... [https://...]"
    RL_NEW_RE = re.compile(r"FMP\s+429\s+\(([^)]+)\).*?\[(https?://[^\]]+)\]")

    # Generic API Error: "API Error 502: https://..."
    API_ERR_RE = re.compile(r"API Error\s+(\d{3})\s*:\s*(https?://\S+)")

    @staticmethod
    def _provider_from_url(url: str) -> str:
        """Determine API provider from URL."""
        if "financialmodelingprep.com" in url:
            return "FMP"
        if "polygon.io" in url:
            return "POLYGON"
        if "stlouisfed.org" in url or "fred" in url:
            return "FRED"
        return "OTHER"

    @staticmethod
    def _fmp_endpoint_from_url(url: str) -> str:
        """Extract FMP endpoint from URL."""
        if "/stable/" not in url:
            return "unknown"
        seg = url.split("/stable/", 1)[1]
        return seg.split("/", 1)[0].split("?", 1)[0] if seg else "unknown"

    @staticmethod
    def _polygon_endpoint_from_url(url: str) -> str:
        """Extract Polygon endpoint from URL."""
        if "/v2/aggs/" in url:
            return "aggs"
        if "/v3/trades/" in url:
            return "trades"
        if "/v3/snapshot/options/" in url:
            return "options_snapshot"
        if "/v2/snapshot/" in url:
            return "market_snapshot"
        return "unknown"

    @classmethod
    def _endpoint_from_url(cls, provider: str, url: str) -> str:
        """Extract endpoint name based on provider."""
        if provider == "FMP":
            return cls._fmp_endpoint_from_url(url)
        if provider == "POLYGON":
            return cls._polygon_endpoint_from_url(url)
        if provider == "FRED":
            return "fred"
        return "unknown"

    @classmethod
    def parse_lines(cls, lines: Iterable[str]) -> list[ApiEvent]:
        """Parse log lines and extract API events."""
        events: list[ApiEvent] = []

        for line in lines:
            line = line.rstrip("\n")

            ts = None
            level = "UNKNOWN"
            msg = line

            # Try to parse timestamp and level
            m = cls.TS_RE.match(line)
            if m:
                ts, level, msg = m.group(1), m.group(2), m.group(3)

            # Check for rate-limit (old format)
            m_rl_old = cls.RL_OLD_RE.search(msg)
            if m_rl_old:
                url = m_rl_old.group(1)
                provider = cls._provider_from_url(url)
                endpoint = cls._endpoint_from_url(provider, url)
                events.append(ApiEvent(ts, provider, endpoint, 429, url, level, line))
                continue

            # Check for rate-limit (new format)
            m_rl_new = cls.RL_NEW_RE.search(msg)
            if m_rl_new:
                endpoint_hint = m_rl_new.group(1)
                url = m_rl_new.group(2)
                provider = "FMP"
                endpoint = endpoint_hint or cls._endpoint_from_url(provider, url)
                events.append(ApiEvent(ts, provider, endpoint, 429, url, level, line))
                continue

            # Check for generic API errors
            m_err = cls.API_ERR_RE.search(msg)
            if m_err:
                status = int(m_err.group(1))
                url = m_err.group(2)
                provider = cls._provider_from_url(url)
                endpoint = cls._endpoint_from_url(provider, url)
                events.append(ApiEvent(ts, provider, endpoint, status, url, level, line))
                continue

        return events

    @staticmethod
    def load_logs(paths: list[str]) -> list[str]:
        """Load log content from multiple files."""
        all_lines: list[str] = []
        for p in paths:
            fp = Path(p)
            if fp.is_file():
                with contextlib.suppress(Exception):
                    all_lines.extend(fp.read_text(errors="ignore").splitlines())
        return all_lines

    @staticmethod
    def find_recent_logs() -> list[str]:
        """Find recent log files automatically."""
        candidates: list[str] = []

        # Main log files
        for name in ["moneyflows.log", "nexus.log", "data_loader.log"]:
            if Path(name).exists():
                candidates.append(name)

        # Dated log folders
        logs_dir = Path("logs")
        if logs_dir.exists() and logs_dir.is_dir():
            subdirs = [d for d in logs_dir.iterdir() if d.is_dir()]
            if subdirs:
                latest = sorted(subdirs, key=lambda d: d.name)[-1]
                for f in latest.glob("*.log"):
                    candidates.append(str(f))

        return candidates

    @staticmethod
    def to_dataframe(events: list[ApiEvent]) -> pd.DataFrame:
        """Convert ApiEvent list to DataFrame."""
        if not events:
            return pd.DataFrame(
                columns=["ts", "provider", "endpoint", "status", "url", "level", "raw"]
            )
        return pd.DataFrame([{
            "ts": e.ts,
            "provider": e.provider,
            "endpoint": e.endpoint,
            "status": e.status,
            "url": e.url,
            "level": e.level,
            "raw": e.raw,
        } for e in events])

    @staticmethod
    def summarize(df: pd.DataFrame) -> dict[str, Any]:
        """Generate summary statistics from event DataFrame."""
        if df.empty:
            return {
                "total_events": 0,
                "top_endpoints": pd.DataFrame(),
                "heatmap": pd.DataFrame(),
            }

        # Group by provider/endpoint/status
        grp = df.groupby(["provider", "endpoint", "status"]).size().reset_index(
            name="count"
        )

        # Endpoint totals
        endpoint_totals = grp.groupby(["provider", "endpoint"])["count"].sum()
        endpoint_totals = endpoint_totals.reset_index()
        endpoint_totals = endpoint_totals.sort_values("count", ascending=False)

        # Heatmap: endpoint x status
        heat = grp.pivot_table(
            index=["provider", "endpoint"],
            columns="status",
            values="count",
            aggfunc="sum",
            fill_value=0
        )

        return {
            "total_events": int(len(df)),
            "top_endpoints": endpoint_totals,
            "heatmap": heat,
        }

    @staticmethod
    def save_csv(df: pd.DataFrame, out_path: str):
        """Save DataFrame to CSV."""
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)

    @staticmethod
    def print_heatmap(heat: pd.DataFrame, max_rows: int = 20):
        """Print endpoint health heatmap to console."""
        if heat is None or heat.empty:
            print("No API errors/rate-limits found in parsed logs.")
            return

        h = heat.copy().head(max_rows)

        # Order columns by common status codes
        cols = list(h.columns)
        priority_cols = [429, 502, 500, 503, 403, 401, 400, 404]
        ordered = [c for c in priority_cols if c in cols]
        ordered += [c for c in cols if c not in priority_cols]
        h = h[ordered] if ordered else h

        print("\nENDPOINT HEALTH (top offenders)")
        print("-" * 78)

        status_cols = list(h.columns)
        header = ["provider", "endpoint"] + [str(c) for c in status_cols]
        print(" | ".join([f"{x:<18}" for x in header]))
        print("-" * 78)

        h_disp = h.reset_index()
        for _, row in h_disp.iterrows():
            provider = str(row["provider"])
            endpoint = str(row["endpoint"])
            vals = [int(row[c]) for c in status_cols]
            parts = [f"{provider:<18}", f"{endpoint:<18}"]
            parts += [f"{v:<18}" for v in vals]
            print(" | ".join(parts))

        print("-" * 78)

    def run_from_paths(self, paths: list[str]) -> dict[str, Any]:
        """Analyze logs from specific file paths."""
        lines = self.load_logs(paths)
        events = self.parse_lines(lines)
        df = self.to_dataframe(events)
        summary = self.summarize(df)
        return {"df": df, **summary}

    def run_auto(self) -> dict[str, Any]:
        """Automatically find and analyze recent logs."""
        paths = self.find_recent_logs()
        return self.run_from_paths(paths)


if __name__ == "__main__":
    import sys

    analyzer = EndpointHealth()

    if len(sys.argv) > 1:
        # Use provided paths
        result = analyzer.run_from_paths(sys.argv[1:])
    else:
        # Auto-discover logs
        result = analyzer.run_auto()

    print(f"\nTotal API events found: {result['total_events']}")

    if result["total_events"] > 0:
        analyzer.print_heatmap(result["heatmap"])

        # Optional: save to CSV
        csv_path = "logs/endpoint_health_events.csv"
        analyzer.save_csv(result["df"], csv_path)
        print(f"\nEvents exported to: {csv_path}")
    else:
        print("No API errors or rate-limits detected in logs.")
