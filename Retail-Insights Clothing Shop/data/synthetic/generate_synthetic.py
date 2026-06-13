"""
Generates synthetic SKU data to stress-test the classification model.

Produces four controlled test sets:
  A. Obvious dead stock   — low sell-through, high quantity, no discount
  B. Obvious fast movers  — high sell-through, low quantity, no discount
  C. Boundary cases       — sell-through near 0.20 and 0.60 thresholds
  D. Random noise         — fully random, tests model robustness

Output: data/synthetic/synthetic_test.csv  (2,000 rows)
        data/synthetic/synthetic_labelled.csv  (A/B/C with expected tier)

Usage:
    python data/synthetic/generate_synthetic.py
"""

import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
rng  = np.random.default_rng(SEED)
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# ── Domain values (from real data) ────────────────────────────────────────────

CATEGORIES  = ["T-Shirt", "Sweatshirt", "Pants", "Shirt", "Shoes", "Shorts",
                "Polo", "Accessories", "Swimwear"]
COLLECTIONS = ["Box Logo", "Morgex", "Trail", "Rainforest", "Geographic",
                "Slate", "Patch", "Circular", "Tribe"]
SEXES       = ["Men", "Women"]
COLORS      = ["Bright White", "Caviar", "Navy", "Forest Green", "Burgundy",
                "Grey Melange", "Stone Grey", "Bright Red", "Pale Mint",
                "Yellow Sunshine", "Khaki", "Snow White", "White Whisper"]
SEASONS     = ["FS24", "SS25"]
ALPHA_SIZES = ["XS", "S", "M", "L", "XL", "XXL", "One Size"]
NUM_SIZES   = ["36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46"]

PRICE_RANGES = {
    "T-Shirt"     : (29.99, 49.99),
    "Sweatshirt"  : (79.99, 129.99),
    "Pants"       : (79.99, 149.99),
    "Shirt"       : (79.99, 129.99),
    "Shoes"       : (99.99, 179.99),
    "Shorts"      : (49.99, 89.99),
    "Polo"        : (59.99, 89.99),
    "Accessories" : (19.99, 69.99),
    "Swimwear"    : (39.99, 79.99),
}


def random_size(category: str) -> str:
    if category == "Shoes":
        return rng.choice(NUM_SIZES)
    return rng.choice(ALPHA_SIZES)


def random_row(category=None, sell_through_range=(0.0, 1.0),
               quantity_range=(1, 800), discount_range=(0, 30)) -> dict:
    if category is None:
        category = rng.choice(CATEGORIES)
    p_lo, p_hi = PRICE_RANGES[category]
    price    = round(float(rng.uniform(p_lo, p_hi)), 2)
    st       = round(float(rng.uniform(*sell_through_range)), 3)
    qty      = int(rng.integers(*quantity_range))
    discount = float(rng.choice([0, 10, 20, 25, 30][: discount_range[1] // 10 + 1]))
    sold     = round(qty * st / (1 - st)) if st < 1 else qty * 10
    season   = rng.choice(SEASONS)
    size     = random_size(category)
    return {
        "product_category" : category,
        "collection_family": rng.choice(COLLECTIONS),
        "sex"              : rng.choice(SEXES),
        "color"            : rng.choice(COLORS),
        "season"           : season,
        "size"             : size,
        "price"            : price,
        "discount"         : discount,
        "sell_through"     : st,
        "quantity"         : qty,
        "quantities_sold"  : max(0, sold),
    }


# NOTE: The model is season-dominated by design.
# In the real data: FS24 = 100% fast movers (mature season), SS25 = 100% dead stock (new season).
# Synthetic sets must respect this — mixing seasons invalidates the expected_tier labels.
# Set A/B/C use season-aligned splits. Set D uses random seasons to test robustness only.

# ── Set A: obvious dead stock ──────────────────────────────────────────────────
# SS25 season, low sell-through, large quantities — model should flag as dead_stock

set_a = []
for _ in range(500):
    row = random_row(sell_through_range=(0.01, 0.18),
                     quantity_range=(200, 800), discount_range=(0, 0))
    row["season"]        = "SS25"   # dead stock season
    row["expected_tier"] = "dead_stock"
    row["test_set"]      = "A_obvious_dead_stock"
    set_a.append(row)


# ── Set B: obvious fast movers ─────────────────────────────────────────────────
# FS24 season, high sell-through, low remaining quantity

set_b = []
for _ in range(500):
    row = random_row(sell_through_range=(0.80, 0.99),
                     quantity_range=(1, 50), discount_range=(0, 0))
    row["season"]        = "FS24"   # fast mover season
    row["expected_tier"] = "fast_mover"
    row["test_set"]      = "B_obvious_fast_mover"
    set_b.append(row)


# ── Set C: boundary cases ──────────────────────────────────────────────────────
# Season-aligned boundaries — model uncertainty is highest here

set_c = []
# Around dead_stock boundary (0.20) — SS25 season
for _ in range(250):
    row = random_row(sell_through_range=(0.17, 0.23), quantity_range=(50, 400))
    row["season"]        = "SS25"
    row["expected_tier"] = "dead_stock" if row["sell_through"] < 0.20 else "average"
    row["test_set"]      = "C_boundary_020"
    set_c.append(row)
# Around fast_mover boundary (0.60) — FS24 season
for _ in range(250):
    row = random_row(sell_through_range=(0.57, 0.63), quantity_range=(20, 300))
    row["season"]        = "FS24"
    row["expected_tier"] = "fast_mover" if row["sell_through"] >= 0.60 else "average"
    row["test_set"]      = "C_boundary_060"
    set_c.append(row)


# ── Set D: random noise ────────────────────────────────────────────────────────
# Random seasons intentionally — tests model doesn't crash, no expected label

set_d = []
for _ in range(500):
    row = random_row(sell_through_range=(0.0, 1.0), quantity_range=(1, 1000),
                     discount_range=(0, 50))
    row["expected_tier"] = None
    row["test_set"]      = "D_random_noise"
    set_d.append(row)


# ── Combine and save labelled (A+B+C) ─────────────────────────────────────────

OUT = Path(__file__).parent

labelled = pd.DataFrame(set_a + set_b + set_c)
labelled.to_csv(OUT / "synthetic_labelled.csv", index=False)
print(f"synthetic_labelled.csv  ({len(labelled)} rows — sets A, B, C)")

all_rows = pd.DataFrame(set_a + set_b + set_c + set_d)
all_rows.to_csv(OUT / "synthetic_test.csv", index=False)
print(f"synthetic_test.csv      ({len(all_rows)} rows — all sets)")


# ── Run model predictions on labelled set ─────────────────────────────────────

print("\nRunning model predictions on labelled set...")
from model_package.predictor import predict as _predict

results = []
for _, row in labelled.iterrows():
    r = _predict(
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
    results.append({
        "test_set"        : row["test_set"],
        "expected_tier"   : row["expected_tier"],
        "predicted_tier"  : r["predicted_tier"],
        "confidence"      : r["confidence"],
        "correct"         : r["predicted_tier"] == row["expected_tier"],
        "sell_through"    : row["sell_through"],
        "price"           : row["price"],
        "discount"        : row["discount"],
    })

results_df = pd.DataFrame(results)
results_df.to_csv(OUT / "synthetic_results.csv", index=False)

print("\n── Accuracy by test set ──────────────────────────────────────")
for name, grp in results_df.groupby("test_set"):
    acc = grp["correct"].mean()
    print(f"  {name:<30}  {acc:.1%}  ({len(grp)} rows)")

print(f"\n  Overall accuracy on controlled sets: {results_df['correct'].mean():.1%}")
print(f"\nsynthetic_results.csv saved.")
