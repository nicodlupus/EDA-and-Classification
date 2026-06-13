import sys
import numpy as np
import pandas as pd
from functools import lru_cache
from config import CLEAN_CSV, MODEL_DIR, THRESHOLD, LOW_ST, HIGH_ST, REORDER_QTY

sys.path.insert(0, str(MODEL_DIR.parent))
from model_package.predictor import predict as _predict_single


# ── Data loading ──────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def load_enriched() -> pd.DataFrame:
    df = pd.read_csv(CLEAN_CSV)

    # apply model predictions to full dataset
    tiers, discounts, reasons = [], [], []
    for _, row in df.iterrows():
        result = _predict_single(
            product_category  = row["product_category"],
            collection_family = row["collection_family"],
            sex               = row["sex"],
            color             = row["color"],
            season            = row["season"],
            size              = str(row["size"]),
            price             = float(row["price"]),
            discount          = float(row["discount"]),
            sell_through      = float(row["sell_through"]),
        )
        tiers.append(result["predicted_tier"])
        discounts.append(result["recommended_discount"])
        reasons.append(result["reason"])

    df["predicted_tier"]       = tiers
    df["recommended_discount"] = discounts
    df["discount_reason"]      = reasons

    # revenue columns
    df["revenue_eur"]            = df["price"] * df["quantities_sold"]
    df["discounted_revenue_eur"] = df["price"] * (1 - df["discount"] / 100) * df["quantities_sold"]

    return df


# ── Analytics functions ───────────────────────────────────────────────────────

def get_summary() -> dict:
    df = load_enriched()
    return {
        "total_skus"       : len(df),
        "total_revenue_eur": round(df["revenue_eur"].sum(), 2),
        "avg_sell_through" : round(df["sell_through"].mean(), 4),
        "dead_stock_skus"  : int((df["predicted_tier"] == "dead_stock").sum()),
        "fast_mover_skus"  : int((df["predicted_tier"] == "fast_mover").sum()),
        "revenue_at_risk"  : round(df[df["predicted_tier"] == "dead_stock"]["revenue_eur"].sum(), 2),
    }


def get_revenue_at_risk() -> dict:
    df   = load_enriched()
    dead = df[df["predicted_tier"] == "dead_stock"].copy()

    revenue_at_risk = dead["price"].sum() * dead["quantity"].sum() / len(dead) if len(dead) > 0 else 0
    revenue_at_risk = round(dead["price"].mul(dead["quantity"]).sum(), 2)

    # projected recovery = units stuck × price × recommended discount applied
    dead["recovery"] = dead["quantity"] * dead["price"] * (1 - dead["recommended_discount"] / 100)
    projected        = round(dead["recovery"].sum(), 2)
    margin_cost      = round(revenue_at_risk - projected, 2)

    return {
        "total_dead_stock_skus"   : len(dead),
        "total_units_stuck"       : int(dead["quantity"].sum()),
        "revenue_at_risk_eur"     : revenue_at_risk,
        "projected_recovery_eur"  : projected,
        "margin_cost_of_discounts": margin_cost,
    }


def get_revenue_recovery() -> list[dict]:
    df   = load_enriched()
    dead = df[df["predicted_tier"] == "dead_stock"].copy()
    rows = []
    for level in [10, 20, 30, 50]:
        subset = dead[dead["recommended_discount"] == level]
        if subset.empty:
            continue
        projected = round((subset["quantity"] * subset["price"] * (1 - level / 100)).sum(), 2)
        full      = round((subset["quantity"] * subset["price"]).sum(), 2)
        rows.append({
            "discount_level"    : level,
            "sku_count"         : len(subset),
            "units_affected"    : int(subset["quantity"].sum()),
            "projected_revenue_eur": projected,
            "margin_cost_eur"   : round(full - projected, 2),
        })
    return rows


def get_abc_analysis() -> list[dict]:
    df = load_enriched()
    rev = (df.groupby(["name", "product_category", "collection_family", "sex"])
             ["revenue_eur"].sum()
             .reset_index()
             .sort_values("revenue_eur", ascending=False))

    rev["cumulative_pct"] = (rev["revenue_eur"].cumsum() / rev["revenue_eur"].sum() * 100).round(2)
    rev["abc_class"]      = rev["cumulative_pct"].apply(
        lambda x: "A" if x <= 80 else ("B" if x <= 95 else "C")
    )
    return rev.round(2).to_dict(orient="records")


def get_reorder_alerts() -> list[dict]:
    df   = load_enriched()
    fast = df[(df["predicted_tier"] == "fast_mover") & (df["quantity"] <= REORDER_QTY)].copy()
    fast = fast.sort_values("quantity")[
        ["name", "product_category", "collection_family", "sex",
         "color", "size", "price", "quantity", "sell_through"]
    ].rename(columns={"quantity": "quantity_remaining"})
    return fast.to_dict(orient="records")


def get_collection_roi() -> list[dict]:
    df  = load_enriched()
    grp = df.groupby("collection_family").agg(
        total_revenue_eur = ("revenue_eur",      "sum"),
        total_units_sold  = ("quantities_sold",   "sum"),
        avg_sell_through  = ("sell_through",      "mean"),
        dead_stock_skus   = ("predicted_tier",    lambda x: (x == "dead_stock").sum()),
        fast_mover_skus   = ("predicted_tier",    lambda x: (x == "fast_mover").sum()),
        total_skus        = ("name",              "count"),
    ).reset_index()

    grp["roi_score"] = (
        grp["avg_sell_through"] * 0.5 +
        (grp["fast_mover_skus"] / grp["total_skus"]) * 0.3 +
        (1 - grp["dead_stock_skus"] / grp["total_skus"]) * 0.2
    ).round(4)

    return grp.round(2).sort_values("roi_score", ascending=False).to_dict(orient="records")


def get_margin_analysis() -> list[dict]:
    df  = load_enriched()
    grp = df.groupby("product_category").agg(
        revenue_eur         = ("revenue_eur",            "sum"),
        discounted_rev_eur  = ("discounted_revenue_eur", "sum"),
        avg_discount_pct    = ("discount",               "mean"),
        units_sold          = ("quantities_sold",         "sum"),
    ).reset_index().round(2)
    return grp.sort_values("revenue_eur", ascending=False).to_dict(orient="records")


def get_gender_split() -> list[dict]:
    df   = load_enriched()
    rows = []
    total_rev = df["revenue_eur"].sum()
    for sex, grp in df.groupby("sex"):
        top_cat   = grp.groupby("product_category")["revenue_eur"].sum().idxmax()
        top_color = grp.groupby("color")["quantities_sold"].sum().idxmax()
        rows.append({
            "sex"             : sex,
            "revenue_eur"     : round(grp["revenue_eur"].sum(), 2),
            "revenue_pct"     : round(grp["revenue_eur"].sum() / total_rev * 100, 2),
            "units_sold"      : int(grp["quantities_sold"].sum()),
            "avg_sell_through": round(grp["sell_through"].mean(), 4),
            "top_category"    : top_cat,
            "top_color"       : top_color,
        })
    return rows


def get_season_comparison() -> list[dict]:
    df  = load_enriched()
    grp = df.groupby("season").agg(
        revenue_eur      = ("revenue_eur",    "sum"),
        units_sold       = ("quantities_sold", "sum"),
        avg_sell_through = ("sell_through",    "mean"),
        dead_stock_skus  = ("predicted_tier",  lambda x: (x == "dead_stock").sum()),
        fast_mover_skus  = ("predicted_tier",  lambda x: (x == "fast_mover").sum()),
    ).reset_index().round(2)
    return grp.sort_values("season").to_dict(orient="records")
