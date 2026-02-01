"""
FMP Charts Endpoints (3.5)

Endpoints for historical price data and intraday charts.
"""

from .registry import Category, Tier, endpoint

# 3.5.01 - Historical Price EOD Light
endpoint(
    name="historical-price-eod-light",
    path="/stable/historical-price-eod/light",
    category=Category.CHARTS,
    tier=Tier.FREE,
    description="Simple EOD chart (close, volume)",
    required_params=["symbol"],
    optional_params=["from", "to"],
)

# 3.5.02 - Historical Price EOD Full (EXISTING as "historical_price")
endpoint(
    name="historical-price-eod-full",
    path="/stable/historical-price-eod/full",
    category=Category.CHARTS,
    tier=Tier.FREE,
    description="Full EOD chart (OHLCV)",
    required_params=["symbol"],
    optional_params=["from", "to"],
)

# Legacy alias
endpoint(
    name="historical_price",
    path="/stable/historical-price-eod/full",
    category=Category.CHARTS,
    tier=Tier.FREE,
    description="Historical prices (legacy alias)",
    required_params=["symbol"],
    optional_params=["from", "to"],
)

# 3.5.03 - Historical Price Non-Split Adjusted
endpoint(
    name="historical-price-eod-non-split-adjusted",
    path="/stable/historical-price-eod/non-split-adjusted",
    category=Category.CHARTS,
    tier=Tier.FREE,
    description="EOD chart without split adjustment",
    required_params=["symbol"],
    optional_params=["from", "to"],
)

# 3.5.04 - Historical Price Dividend Adjusted
endpoint(
    name="historical-price-eod-dividend-adjusted",
    path="/stable/historical-price-eod/dividend-adjusted",
    category=Category.CHARTS,
    tier=Tier.FREE,
    description="EOD chart with dividend adjustment",
    required_params=["symbol"],
    optional_params=["from", "to"],
)

# 3.5.05 - Historical Chart 1 Minute
endpoint(
    name="historical-chart-1min",
    path="/stable/historical-chart/1min",
    category=Category.CHARTS,
    tier=Tier.PREMIUM,
    description="1-minute intraday chart",
    required_params=["symbol"],
    optional_params=["from", "to"],
)

# 3.5.06 - Historical Chart 5 Minutes
endpoint(
    name="historical-chart-5min",
    path="/stable/historical-chart/5min",
    category=Category.CHARTS,
    tier=Tier.PREMIUM,
    description="5-minute intraday chart",
    required_params=["symbol"],
    optional_params=["from", "to"],
)

# 3.5.07 - Historical Chart 15 Minutes
endpoint(
    name="historical-chart-15min",
    path="/stable/historical-chart/15min",
    category=Category.CHARTS,
    tier=Tier.PREMIUM,
    description="15-minute intraday chart",
    required_params=["symbol"],
    optional_params=["from", "to"],
)

# 3.5.08 - Historical Chart 30 Minutes
endpoint(
    name="historical-chart-30min",
    path="/stable/historical-chart/30min",
    category=Category.CHARTS,
    tier=Tier.PREMIUM,
    description="30-minute intraday chart",
    required_params=["symbol"],
    optional_params=["from", "to"],
)

# 3.5.09 - Historical Chart 1 Hour
endpoint(
    name="historical-chart-1hour",
    path="/stable/historical-chart/1hour",
    category=Category.CHARTS,
    tier=Tier.PREMIUM,
    description="1-hour intraday chart",
    required_params=["symbol"],
    optional_params=["from", "to"],
)

# 3.5.10 - Historical Chart 4 Hours
endpoint(
    name="historical-chart-4hour",
    path="/stable/historical-chart/4hour",
    category=Category.CHARTS,
    tier=Tier.PREMIUM,
    description="4-hour intraday chart",
    required_params=["symbol"],
    optional_params=["from", "to"],
)
