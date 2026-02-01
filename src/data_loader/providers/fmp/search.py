"""
FMP Search & Directory Endpoints (3.1)

Endpoints for searching tickers, companies, and listing available data.
"""

from .registry import Category, Tier, endpoint

# 3.1.01 - Search by Symbol
endpoint(
    name="search-symbol",
    path="/stable/search-symbol",
    category=Category.SEARCH,
    tier=Tier.FREE,
    description="Search for tickers by symbol",
    required_params=["query"],
    optional_params=["limit", "exchange"],
)

# 3.1.02 - Search by Name
endpoint(
    name="search-name",
    path="/stable/search-name",
    category=Category.SEARCH,
    tier=Tier.FREE,
    description="Search for companies by name",
    required_params=["query"],
    optional_params=["limit", "exchange"],
)

# 3.1.03 - Search by CIK
endpoint(
    name="search-cik",
    path="/stable/search-cik",
    category=Category.SEARCH,
    tier=Tier.FREE,
    description="Search for companies by CIK number",
    required_params=["query"],
)

# 3.1.04 - Search by CUSIP
endpoint(
    name="search-cusip",
    path="/stable/search-cusip",
    category=Category.SEARCH,
    tier=Tier.FREE,
    description="Search for securities by CUSIP",
    required_params=["query"],
)

# 3.1.05 - Search by ISIN
endpoint(
    name="search-isin",
    path="/stable/search-isin",
    category=Category.SEARCH,
    tier=Tier.FREE,
    description="Search for securities by ISIN",
    required_params=["query"],
)

# 3.1.06 - Company Screener (EXISTING as "screener")
endpoint(
    name="company-screener",
    path="/stable/company-screener",
    category=Category.SEARCH,
    tier=Tier.FREE,
    description="Stock screener with multiple filters",
    optional_params=[
        "marketCapMoreThan",
        "marketCapLowerThan",
        "priceMoreThan",
        "priceLowerThan",
        "betaMoreThan",
        "betaLowerThan",
        "volumeMoreThan",
        "volumeLowerThan",
        "dividendMoreThan",
        "dividendLowerThan",
        "isEtf",
        "isActivelyTrading",
        "sector",
        "industry",
        "country",
        "exchange",
        "limit",
    ],
)

# Legacy alias for backward compatibility
endpoint(
    name="screener",
    path="/stable/company-screener",
    category=Category.SEARCH,
    tier=Tier.FREE,
    description="Stock screener (legacy alias for company-screener)",
    optional_params=[
        "marketCapMoreThan",
        "marketCapLowerThan",
        "priceMoreThan",
        "priceLowerThan",
        "betaMoreThan",
        "betaLowerThan",
        "volumeMoreThan",
        "volumeLowerThan",
        "dividendMoreThan",
        "dividendLowerThan",
        "isEtf",
        "isActivelyTrading",
        "sector",
        "industry",
        "country",
        "exchange",
        "limit",
    ],
)

# 3.1.07 - Stock List
endpoint(
    name="stock-list",
    path="/stable/stock-list",
    category=Category.SEARCH,
    tier=Tier.FREE,
    description="List of all available stock tickers",
)

# 3.1.08 - ETF List
endpoint(
    name="etf-list",
    path="/stable/etf-list",
    category=Category.SEARCH,
    tier=Tier.FREE,
    description="List of all available ETFs",
)

# 3.1.09 - Available Exchanges
endpoint(
    name="available-exchanges",
    path="/stable/available-exchanges",
    category=Category.SEARCH,
    tier=Tier.FREE,
    description="List of available stock exchanges",
)

# 3.1.10 - Available Sectors
endpoint(
    name="available-sectors",
    path="/stable/available-sectors",
    category=Category.SEARCH,
    tier=Tier.FREE,
    description="List of available sectors",
)

# 3.1.11 - Available Industries
endpoint(
    name="available-industries",
    path="/stable/available-industries",
    category=Category.SEARCH,
    tier=Tier.FREE,
    description="List of available industries",
)

# 3.1.12 - Available Countries
endpoint(
    name="available-countries",
    path="/stable/available-countries",
    category=Category.SEARCH,
    tier=Tier.FREE,
    description="List of available countries",
)
