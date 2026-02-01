"""
FMP Institutional Ownership Endpoints (3.10)

Endpoints for Form 13F institutional holdings.
"""

from .registry import Category, Tier, endpoint

# 3.10.01 - Institutional Ownership Latest (EXISTING as "institutional_ownership")
endpoint(
    name="institutional-ownership-latest",
    path="/stable/institutional-ownership/latest",
    category=Category.INSTITUTIONAL,
    tier=Tier.FREE,
    description="Latest 13F filing holdings",
    required_params=["symbol"],
)

# Legacy alias
endpoint(
    name="institutional_ownership",
    path="/stable/institutional-ownership/latest",
    category=Category.INSTITUTIONAL,
    tier=Tier.FREE,
    description="Institutional ownership (legacy alias)",
    required_params=["symbol"],
)

# 3.10.02 - Institutional Ownership Extract
endpoint(
    name="institutional-ownership-extract",
    path="/stable/institutional-ownership/extract",
    category=Category.INSTITUTIONAL,
    tier=Tier.FREE,
    description="Extract details from a specific 13F filing",
    required_params=["cik", "date"],
)

# 3.10.03 - Institutional Ownership Dates
endpoint(
    name="institutional-ownership-dates",
    path="/stable/institutional-ownership/dates",
    category=Category.INSTITUTIONAL,
    tier=Tier.FREE,
    description="Available 13F filing dates for a holder",
    required_params=["cik"],
)

# 3.10.04 - Holder Performance Summary
endpoint(
    name="institutional-ownership-holder-performance-summary",
    path="/stable/institutional-ownership/holder-performance-summary",
    category=Category.INSTITUTIONAL,
    tier=Tier.FREE,
    description="Performance summary for an institutional holder",
    required_params=["cik"],
)

# 3.10.05 - Holder Industry Breakdown
endpoint(
    name="institutional-ownership-holder-industry-breakdown",
    path="/stable/institutional-ownership/holder-industry-breakdown",
    category=Category.INSTITUTIONAL,
    tier=Tier.FREE,
    description="Industry breakdown of holder's portfolio",
    required_params=["cik"],
)

# 3.10.06 - Symbol Positions Summary
endpoint(
    name="institutional-ownership-symbol-positions-summary",
    path="/stable/institutional-ownership/symbol-positions-summary",
    category=Category.INSTITUTIONAL,
    tier=Tier.FREE,
    description="Summary of institutional positions for a symbol",
    required_params=["symbol"],
)

# 3.10.07 - Industry Summary
endpoint(
    name="institutional-ownership-industry-summary",
    path="/stable/institutional-ownership/industry-summary",
    category=Category.INSTITUTIONAL,
    tier=Tier.FREE,
    description="Institutional ownership by industry",
    optional_params=["date"],
)
