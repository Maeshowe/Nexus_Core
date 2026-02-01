"""
FMP Analyst Endpoints (3.11)

Endpoints for analyst estimates, ratings, and price targets.
"""

from .registry import Category, Tier, endpoint

# 3.11.01 - Analyst Estimates (EXISTING)
endpoint(
    name="analyst-estimates",
    path="/stable/analyst-estimates",
    category=Category.ANALYST,
    tier=Tier.FREE,
    description="Analyst EPS and revenue estimates",
    required_params=["symbol"],
    optional_params=["period", "limit"],
)

# 3.11.02 - Ratings Snapshot
endpoint(
    name="ratings-snapshot",
    path="/stable/ratings-snapshot",
    category=Category.ANALYST,
    tier=Tier.FREE,
    description="Current analyst rating summary",
    required_params=["symbol"],
)

# 3.11.03 - Ratings Historical
endpoint(
    name="ratings-historical",
    path="/stable/ratings-historical",
    category=Category.ANALYST,
    tier=Tier.FREE,
    description="Historical analyst ratings over time",
    required_params=["symbol"],
    optional_params=["limit"],
)

# 3.11.04 - Price Target Summary
endpoint(
    name="price-target-summary",
    path="/stable/price-target-summary",
    category=Category.ANALYST,
    tier=Tier.FREE,
    description="Summary of analyst price targets",
    required_params=["symbol"],
)

# 3.11.05 - Price Target Consensus (EXISTING)
endpoint(
    name="price-target-consensus",
    path="/stable/price-target-consensus",
    category=Category.ANALYST,
    tier=Tier.FREE,
    description="Consensus price target",
    required_params=["symbol"],
)

# 3.11.06 - Grades
endpoint(
    name="grades",
    path="/stable/grades",
    category=Category.ANALYST,
    tier=Tier.FREE,
    description="Analyst grades (buy/hold/sell)",
    required_params=["symbol"],
    optional_params=["limit"],
)

# 3.11.07 - Grades Historical
endpoint(
    name="grades-historical",
    path="/stable/grades-historical",
    category=Category.ANALYST,
    tier=Tier.FREE,
    description="Historical analyst grades",
    required_params=["symbol"],
    optional_params=["limit"],
)

# 3.11.08 - Grades Consensus
endpoint(
    name="grades-consensus",
    path="/stable/grades-consensus",
    category=Category.ANALYST,
    tier=Tier.FREE,
    description="Consensus analyst grade",
    required_params=["symbol"],
)
