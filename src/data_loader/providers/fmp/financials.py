"""
FMP Financial Statements Endpoints (3.4)

Endpoints for income statements, balance sheets, cash flow, and financial metrics.
"""

from .registry import Category, Tier, endpoint

# 3.4.01 - Income Statement (EXISTING)
endpoint(
    name="income-statement",
    path="/stable/income-statement",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Income statement (annual or quarterly)",
    required_params=["symbol"],
    optional_params=["period", "limit"],
)

# 3.4.02 - Balance Sheet Statement (EXISTING)
endpoint(
    name="balance-sheet-statement",
    path="/stable/balance-sheet-statement",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Balance sheet statement (annual or quarterly)",
    required_params=["symbol"],
    optional_params=["period", "limit"],
)

# Legacy alias
endpoint(
    name="balance_sheet",
    path="/stable/balance-sheet-statement",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Balance sheet (legacy alias)",
    required_params=["symbol"],
    optional_params=["period", "limit"],
)

# 3.4.03 - Cash Flow Statement (EXISTING)
endpoint(
    name="cash-flow-statement",
    path="/stable/cash-flow-statement",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Cash flow statement (annual or quarterly)",
    required_params=["symbol"],
    optional_params=["period", "limit"],
)

# Legacy alias
endpoint(
    name="cash_flow",
    path="/stable/cash-flow-statement",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Cash flow (legacy alias)",
    required_params=["symbol"],
    optional_params=["period", "limit"],
)

# 3.4.04 - Income Statement TTM
endpoint(
    name="income-statement-ttm",
    path="/stable/income-statement-ttm",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Trailing twelve months income statement",
    required_params=["symbol"],
)

# 3.4.05 - Balance Sheet Statement TTM
endpoint(
    name="balance-sheet-statement-ttm",
    path="/stable/balance-sheet-statement-ttm",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Trailing twelve months balance sheet",
    required_params=["symbol"],
)

# 3.4.06 - Cash Flow Statement TTM
endpoint(
    name="cash-flow-statement-ttm",
    path="/stable/cash-flow-statement-ttm",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Trailing twelve months cash flow",
    required_params=["symbol"],
)

# 3.4.07 - Key Metrics (EXISTING)
endpoint(
    name="key-metrics",
    path="/stable/key-metrics",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Key financial metrics (P/E, EV/EBITDA, etc.)",
    required_params=["symbol"],
    optional_params=["period", "limit"],
)

# 3.4.08 - Ratios (EXISTING)
endpoint(
    name="ratios",
    path="/stable/ratios",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="150+ financial ratios",
    required_params=["symbol"],
    optional_params=["period", "limit"],
)

# 3.4.09 - Key Metrics TTM
endpoint(
    name="key-metrics-ttm",
    path="/stable/key-metrics-ttm",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Trailing twelve months key metrics",
    required_params=["symbol"],
)

# 3.4.10 - Ratios TTM
endpoint(
    name="ratios-ttm",
    path="/stable/ratios-ttm",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Trailing twelve months ratios",
    required_params=["symbol"],
)

# 3.4.11 - Financial Scores
endpoint(
    name="financial-scores",
    path="/stable/financial-scores",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Financial scores (Altman Z-score, Piotroski F-score)",
    required_params=["symbol"],
)

# 3.4.12 - Owner Earnings
endpoint(
    name="owner-earnings",
    path="/stable/owner-earnings",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Owner earnings calculation",
    required_params=["symbol"],
)

# 3.4.13 - Enterprise Values
endpoint(
    name="enterprise-values",
    path="/stable/enterprise-values",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Enterprise value calculation",
    required_params=["symbol"],
    optional_params=["period", "limit"],
)

# 3.4.14 - Income Statement Growth (EXISTING as "growth")
endpoint(
    name="income-statement-growth",
    path="/stable/income-statement-growth",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Income statement growth metrics",
    required_params=["symbol"],
    optional_params=["period", "limit"],
)

# Legacy alias
endpoint(
    name="growth",
    path="/stable/financial-growth",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Financial growth (legacy alias)",
    required_params=["symbol"],
    optional_params=["period", "limit"],
)

# 3.4.15 - Balance Sheet Statement Growth
endpoint(
    name="balance-sheet-statement-growth",
    path="/stable/balance-sheet-statement-growth",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Balance sheet growth metrics",
    required_params=["symbol"],
    optional_params=["period", "limit"],
)

# 3.4.16 - Cash Flow Statement Growth
endpoint(
    name="cash-flow-statement-growth",
    path="/stable/cash-flow-statement-growth",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Cash flow growth metrics",
    required_params=["symbol"],
    optional_params=["period", "limit"],
)

# 3.4.17 - Revenue Product Segmentation
endpoint(
    name="revenue-product-segmentation",
    path="/stable/revenue-product-segmentation",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Revenue breakdown by product/segment",
    required_params=["symbol"],
    optional_params=["period"],
)

# 3.4.18 - Revenue Geographic Segmentation
endpoint(
    name="revenue-geographic-segmentation",
    path="/stable/revenue-geographic-segmentation",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Revenue breakdown by geography",
    required_params=["symbol"],
    optional_params=["period"],
)

# 3.4.19 - Income Statement As Reported
endpoint(
    name="income-statement-as-reported",
    path="/stable/income-statement-as-reported",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Income statement in SEC XBRL format",
    required_params=["symbol"],
    optional_params=["period", "limit"],
)

# 3.4.20 - Balance Sheet Statement As Reported
endpoint(
    name="balance-sheet-statement-as-reported",
    path="/stable/balance-sheet-statement-as-reported",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Balance sheet in SEC XBRL format",
    required_params=["symbol"],
    optional_params=["period", "limit"],
)

# 3.4.21 - Cash Flow Statement As Reported
endpoint(
    name="cash-flow-statement-as-reported",
    path="/stable/cash-flow-statement-as-reported",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Cash flow in SEC XBRL format",
    required_params=["symbol"],
    optional_params=["period", "limit"],
)

# 3.4.22 - Financial Statement Full As Reported
endpoint(
    name="financial-statement-full-as-reported",
    path="/stable/financial-statement-full-as-reported",
    category=Category.FINANCIALS,
    tier=Tier.FREE,
    description="Complete financial statements in SEC XBRL format",
    required_params=["symbol"],
    optional_params=["period", "limit"],
)
