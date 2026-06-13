const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface Summary {
  total_skus: number;
  total_revenue_eur: number;
  avg_sell_through: number;
  dead_stock_skus: number;
  fast_mover_skus: number;
  revenue_at_risk: number;
}

export interface RevenueAtRisk {
  total_dead_stock_skus: number;
  total_units_stuck: number;
  revenue_at_risk_eur: number;
  projected_recovery_eur: number;
  margin_cost_of_discounts: number;
}

export interface RevenueRecovery {
  discount_level: number;
  sku_count: number;
  units_affected: number;
  projected_revenue_eur: number;
  margin_cost_eur: number;
}

export interface CollectionROI {
  collection_family: string;
  total_revenue_eur: number;
  total_units_sold: number;
  avg_sell_through: number;
  dead_stock_skus: number;
  fast_mover_skus: number;
  total_skus: number;
  roi_score: number;
}

export interface ABCItem {
  name: string;
  product_category: string;
  collection_family: string;
  sex: string;
  revenue_eur: number;
  cumulative_pct: number;
  abc_class: string;
}

export interface ReorderAlert {
  name: string;
  product_category: string;
  collection_family: string;
  sex: string;
  color: string;
  size: string;
  price: number;
  quantity_remaining: number;
  sell_through: number;
}

export interface SeasonRow {
  season: string;
  revenue_eur: number;
  units_sold: number;
  avg_sell_through: number;
  dead_stock_skus: number;
  fast_mover_skus: number;
}

export interface NormalizationMapping {
  field: string;
  original: string;
  matched: string;
  score: number;
}

export interface PredictionOutput {
  predicted_tier: "dead_stock" | "average" | "fast_mover";
  confidence: number;
  recommended_discount: number;
  reason: string;
  probabilities: Record<string, number>;
  input_normalizations: NormalizationMapping[];
}

export interface ProductInput {
  product_category: string;
  collection_family: string;
  sex: string;
  color: string;
  season: string;
  size: string;
  price: number;
  discount: number;
  sell_through: number;
}

// ── API calls ─────────────────────────────────────────────────────────────────

export const api = {
  summary:        () => get<Summary>("/analytics/summary"),
  revenueAtRisk:  () => get<RevenueAtRisk>("/revenue/at-risk"),
  recovery:       () => get<RevenueRecovery[]>("/revenue/recovery"),
  collections:    () => get<CollectionROI[]>("/analytics/collection-roi"),
  abc:            () => get<ABCItem[]>("/analytics/abc"),
  reorder:        () => get<ReorderAlert[]>("/analytics/reorder"),
  seasons:        () => get<SeasonRow[]>("/analytics/season-comparison"),
  predict:        (body: ProductInput) => post<PredictionOutput>("/predict", body),
};
