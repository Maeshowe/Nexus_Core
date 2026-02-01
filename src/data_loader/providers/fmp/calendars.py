"""
FMP Calendars & Events Endpoints (3.7)

Endpoints for earnings, dividends, IPOs, and splits calendars.
"""

from .registry import Category, Tier, endpoint

# 3.7.01 - Dividends (EXISTING)
endpoint(
    name="dividends",
    path="/stable/dividends",
    category=Category.CALENDARS,
    tier=Tier.FREE,
    description="Dividend history for a ticker",
    required_params=["symbol"],
)

# 3.7.02 - Dividends Calendar
endpoint(
    name="dividends-calendar",
    path="/stable/dividends-calendar",
    category=Category.CALENDARS,
    tier=Tier.FREE,
    description="Upcoming dividend announcements",
    optional_params=["from", "to"],
)

# 3.7.03 - Earnings (EXISTING as "earnings_calendar")
endpoint(
    name="earnings",
    path="/stable/earnings",
    category=Category.CALENDARS,
    tier=Tier.FREE,
    description="Earnings history for a ticker",
    required_params=["symbol"],
)

# Legacy alias
endpoint(
    name="earnings_calendar",
    path="/stable/earnings-calendar",
    category=Category.CALENDARS,
    tier=Tier.FREE,
    description="Earnings calendar (legacy alias)",
    optional_params=["symbol", "from", "to"],
)

# 3.7.04 - Earnings Calendar
endpoint(
    name="earnings-calendar",
    path="/stable/earnings-calendar",
    category=Category.CALENDARS,
    tier=Tier.FREE,
    description="Upcoming earnings announcements",
    optional_params=["from", "to"],
)

# 3.7.05 - IPOs Calendar
endpoint(
    name="ipos-calendar",
    path="/stable/ipos-calendar",
    category=Category.CALENDARS,
    tier=Tier.FREE,
    description="Upcoming IPO calendar",
    optional_params=["from", "to"],
)

# 3.7.06 - IPOs Disclosure
endpoint(
    name="ipos-disclosure",
    path="/stable/ipos-disclosure",
    category=Category.CALENDARS,
    tier=Tier.FREE,
    description="IPO disclosure filings",
    optional_params=["from", "to"],
)

# 3.7.07 - IPOs Prospectus
endpoint(
    name="ipos-prospectus",
    path="/stable/ipos-prospectus",
    category=Category.CALENDARS,
    tier=Tier.FREE,
    description="IPO prospectus documents",
    optional_params=["from", "to"],
)

# 3.7.08 - Splits (EXISTING)
endpoint(
    name="splits",
    path="/stable/splits",
    category=Category.CALENDARS,
    tier=Tier.FREE,
    description="Stock split history for a ticker",
    required_params=["symbol"],
)

# 3.7.09 - Splits Calendar
endpoint(
    name="splits-calendar",
    path="/stable/splits-calendar",
    category=Category.CALENDARS,
    tier=Tier.FREE,
    description="Upcoming stock splits",
    optional_params=["from", "to"],
)
