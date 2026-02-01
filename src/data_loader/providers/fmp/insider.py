"""
FMP Insider Trading Endpoints (3.16)

Endpoints for insider trading and institutional ownership.
"""

from .registry import Category, Tier, endpoint

# 3.16.01 - Insider Trading Latest (EXISTING as "insider_trading")
endpoint(
    name="insider-trading-latest",
    path="/stable/insider-trading/latest",
    category=Category.INSIDER,
    tier=Tier.FREE,
    description="Latest insider trading transactions",
    optional_params=["limit", "page"],
)

# Legacy alias
endpoint(
    name="insider_trading",
    path="/stable/insider-trading/search",
    category=Category.INSIDER,
    tier=Tier.FREE,
    description="Insider trading (legacy alias)",
    required_params=["symbol"],
    optional_params=["page", "limit"],
)

# 3.16.02 - Insider Trading Search
endpoint(
    name="insider-trading-search",
    path="/stable/insider-trading/search",
    category=Category.INSIDER,
    tier=Tier.FREE,
    description="Search insider trading by symbol",
    required_params=["symbol"],
    optional_params=["page", "limit"],
)

# 3.16.03 - Insider Trading by Reporting Name
endpoint(
    name="insider-trading-reporting-name",
    path="/stable/insider-trading/reporting-name",
    category=Category.INSIDER,
    tier=Tier.FREE,
    description="Search insider trading by insider name",
    required_params=["name"],
    optional_params=["page", "limit"],
)

# 3.16.04 - Insider Trading Transaction Types
endpoint(
    name="insider-trading-transaction-type",
    path="/stable/insider-trading-transaction-type",
    category=Category.INSIDER,
    tier=Tier.FREE,
    description="List of transaction type codes",
)

# 3.16.05 - Insider Trading Statistics
endpoint(
    name="insider-trading-statistics",
    path="/stable/insider-trading/statistics",
    category=Category.INSIDER,
    tier=Tier.FREE,
    description="Insider trading statistics for a symbol",
    required_params=["symbol"],
)

# 3.16.06 - Acquisition of Beneficial Ownership
endpoint(
    name="acquisition-of-beneficial-ownership",
    path="/stable/acquisition-of-beneficial-ownership",
    category=Category.INSIDER,
    tier=Tier.FREE,
    description="Beneficial ownership acquisitions (Form 3/4/5)",
    required_params=["symbol"],
    optional_params=["page", "limit"],
)
