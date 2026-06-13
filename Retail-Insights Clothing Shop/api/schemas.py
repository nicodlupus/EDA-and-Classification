from pydantic import BaseModel, Field
from typing import Optional


# ── Prediction ────────────────────────────────────────────────────────────────

class ProductInput(BaseModel):
    product_category  : str
    collection_family : str
    sex               : str
    color             : str
    season            : str
    size              : str
    price             : float = Field(..., gt=0)
    discount          : float = Field(0, ge=0, le=100)
    sell_through      : float = Field(0.0, ge=0, le=1)

class BatchInput(BaseModel):
    products: list[ProductInput]

class NormalizationMapping(BaseModel):
    field    : str
    original : str
    matched  : str
    score    : float

class PredictionOutput(BaseModel):
    predicted_tier        : str
    confidence            : float
    recommended_discount  : int
    reason                : str
    probabilities         : dict[str, float]
    input_normalizations  : list[NormalizationMapping] = []

class BatchOutput(BaseModel):
    results: list[PredictionOutput]


# ── Revenue ───────────────────────────────────────────────────────────────────

class RevenueAtRisk(BaseModel):
    total_dead_stock_skus     : int
    total_units_stuck         : int
    revenue_at_risk_eur       : float
    projected_recovery_eur    : float
    margin_cost_of_discounts  : float

class RevenueRecovery(BaseModel):
    discount_level            : int
    sku_count                 : int
    units_affected            : int
    projected_revenue_eur     : float
    margin_cost_eur           : float


# ── Analytics ─────────────────────────────────────────────────────────────────

class ABCItem(BaseModel):
    name              : str
    product_category  : str
    collection_family : str
    sex               : str
    revenue_eur       : float
    cumulative_pct    : float
    abc_class         : str

class ReorderAlert(BaseModel):
    name              : str
    product_category  : str
    collection_family : str
    sex               : str
    color             : str
    size              : str
    price             : float
    quantity_remaining: int
    sell_through      : float

class CollectionROI(BaseModel):
    collection_family : str
    total_revenue_eur : float
    total_units_sold  : int
    avg_sell_through  : float
    dead_stock_skus   : int
    fast_mover_skus   : int
    roi_score         : float

class MarginRow(BaseModel):
    product_category  : str
    revenue_eur       : float
    discounted_rev_eur: float
    avg_discount_pct  : float
    units_sold        : int

class GenderSplit(BaseModel):
    sex               : str
    revenue_eur       : float
    revenue_pct       : float
    units_sold        : int
    avg_sell_through  : float
    top_category      : str
    top_color         : str

class SeasonRow(BaseModel):
    season            : str
    revenue_eur       : float
    units_sold        : int
    avg_sell_through  : float
    dead_stock_skus   : int
    fast_mover_skus   : int

class SummaryResponse(BaseModel):
    total_skus        : int
    total_revenue_eur : float
    avg_sell_through  : float
    dead_stock_skus   : int
    fast_mover_skus   : int
    revenue_at_risk   : float
