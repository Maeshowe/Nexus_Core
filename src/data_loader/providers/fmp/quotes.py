"""
FMP Quotes Endpoints (3.3)

Endpoints for real-time and batch quotes.
"""

from .registry import Category, Tier, endpoint

# 3.3.01 - Quote (EXISTING)
endpoint(
    name="quote",
    path="/stable/quote",
    category=Category.QUOTES,
    tier=Tier.FREE,
    description="Full real-time quote with price, volume, and changes",
    required_params=["symbol"],
)

# 3.3.02 - Quote Short
endpoint(
    name="quote-short",
    path="/stable/quote-short",
    category=Category.QUOTES,
    tier=Tier.FREE,
    description="Abbreviated quote (price and volume only)",
    required_params=["symbol"],
)

# 3.3.03 - Aftermarket Trade
endpoint(
    name="aftermarket-trade",
    path="/stable/aftermarket-trade",
    category=Category.QUOTES,
    tier=Tier.FREE,
    description="After-hours trading data",
    required_params=["symbol"],
)

# 3.3.04 - Aftermarket Quote
endpoint(
    name="aftermarket-quote",
    path="/stable/aftermarket-quote",
    category=Category.QUOTES,
    tier=Tier.FREE,
    description="After-hours quote data",
    required_params=["symbol"],
)

# 3.3.05 - Stock Price Change
endpoint(
    name="stock-price-change",
    path="/stable/stock-price-change",
    category=Category.QUOTES,
    tier=Tier.FREE,
    description="Price changes (daily, weekly, monthly, YTD)",
    required_params=["symbol"],
)

# 3.3.06 - Batch Quote
endpoint(
    name="batch-quote",
    path="/stable/batch-quote",
    category=Category.QUOTES,
    tier=Tier.FREE,
    description="Quotes for multiple tickers at once",
    required_params=["symbols"],
)

# 3.3.07 - Batch Exchange Quote
endpoint(
    name="batch-exchange-quote",
    path="/stable/batch-quote-exchange",
    category=Category.QUOTES,
    tier=Tier.FREE,
    description="All quotes for a specific exchange",
    required_params=["exchange"],
)

# 3.3.08 - Batch Mutual Fund Quotes
endpoint(
    name="batch-mutualfund-quotes",
    path="/stable/batch-quote-mutual-fund",
    category=Category.QUOTES,
    tier=Tier.FREE,
    description="Quotes for all mutual funds",
)

# 3.3.09 - Batch ETF Quotes
endpoint(
    name="batch-etf-quotes",
    path="/stable/batch-quote-etf",
    category=Category.QUOTES,
    tier=Tier.FREE,
    description="Quotes for all ETFs",
)

# 3.3.10 - Batch Commodity Quotes
endpoint(
    name="batch-commodity-quotes",
    path="/stable/batch-quote-commodity",
    category=Category.QUOTES,
    tier=Tier.FREE,
    description="Quotes for all commodities",
)

# 3.3.11 - Batch Crypto Quotes
endpoint(
    name="batch-crypto-quotes",
    path="/stable/batch-quote-crypto",
    category=Category.QUOTES,
    tier=Tier.FREE,
    description="Quotes for all cryptocurrencies",
)

# 3.3.12 - Batch Forex Quotes
endpoint(
    name="batch-forex-quotes",
    path="/stable/batch-quote-forex",
    category=Category.QUOTES,
    tier=Tier.FREE,
    description="Quotes for all forex pairs",
)

# 3.3.13 - Batch Index Quotes
endpoint(
    name="batch-index-quotes",
    path="/stable/batch-quote-index",
    category=Category.QUOTES,
    tier=Tier.FREE,
    description="Quotes for all indices",
)
