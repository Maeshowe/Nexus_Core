"""
FMP Company Information Endpoints (3.2)

Endpoints for company profiles, executives, and corporate data.
"""

from .registry import Category, Tier, endpoint

# Register all company endpoints

# 3.2.01 - Profile (EXISTING in v1.2.0)
endpoint(
    name="profile",
    path="/stable/profile",
    category=Category.COMPANY,
    tier=Tier.FREE,
    description="Detailed company profile including sector, industry, CEO, description",
    required_params=["symbol"],
)

# 3.2.02 - Profile by CIK
endpoint(
    name="profile-cik",
    path="/stable/profile-cik",
    category=Category.COMPANY,
    tier=Tier.FREE,
    description="Company profile lookup by CIK number",
    required_params=["cik"],
)

# 3.2.03 - Company Notes
endpoint(
    name="company-notes",
    path="/stable/company-notes",
    category=Category.COMPANY,
    tier=Tier.FREE,
    description="Company notes and additional information",
    required_params=["symbol"],
)

# 3.2.04 - Stock Peers
endpoint(
    name="stock-peers",
    path="/stable/stock-peers",
    category=Category.COMPANY,
    tier=Tier.FREE,
    description="List of stock peers/competitors",
    required_params=["symbol"],
)

# 3.2.05 - Delisted Companies
endpoint(
    name="delisted-companies",
    path="/stable/delisted-companies",
    category=Category.COMPANY,
    tier=Tier.FREE,
    description="List of delisted companies",
    optional_params=["limit", "page"],
)

# 3.2.06 - Employee Count
endpoint(
    name="employee-count",
    path="/stable/employee-count",
    category=Category.COMPANY,
    tier=Tier.FREE,
    description="Current number of employees",
    required_params=["symbol"],
)

# 3.2.07 - Historical Employee Count
endpoint(
    name="historical-employee-count",
    path="/stable/historical-employee-count",
    category=Category.COMPANY,
    tier=Tier.FREE,
    description="Historical employee count over time",
    required_params=["symbol"],
)

# 3.2.08 - Market Capitalization
endpoint(
    name="market-capitalization",
    path="/stable/market-capitalization",
    category=Category.COMPANY,
    tier=Tier.FREE,
    description="Current market capitalization",
    required_params=["symbol"],
)

# 3.2.09 - Historical Market Cap
endpoint(
    name="historical-market-cap",
    path="/stable/historical-market-cap",
    category=Category.COMPANY,
    tier=Tier.FREE,
    description="Historical market capitalization",
    required_params=["symbol"],
    optional_params=["limit"],
)

# 3.2.10 - Shares Float
endpoint(
    name="shares-float",
    path="/stable/shares-float",
    category=Category.COMPANY,
    tier=Tier.FREE,
    description="Free float and shares outstanding",
    required_params=["symbol"],
)

# 3.2.11 - Mergers & Acquisitions
endpoint(
    name="mergers-acquisitions",
    path="/stable/mergers-acquisitions",
    category=Category.COMPANY,
    tier=Tier.FREE,
    description="M&A transactions involving the company",
    required_params=["symbol"],
)

# 3.2.12 - Key Executives
endpoint(
    name="key-executives",
    path="/stable/key-executives",
    category=Category.COMPANY,
    tier=Tier.FREE,
    description="Key executives and management team",
    required_params=["symbol"],
)

# 3.2.13 - Executive Compensation
endpoint(
    name="executive-compensation",
    path="/stable/executive-compensation",
    category=Category.COMPANY,
    tier=Tier.FREE,
    description="Executive compensation details",
    required_params=["symbol"],
)
