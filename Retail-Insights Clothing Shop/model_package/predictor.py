import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from .normalizer import normalize_input

_bundle    = joblib.load(Path(__file__).parent / "model.joblib")
_pipeline  = _bundle["pipeline"]
_threshold = _bundle["threshold"]
_ds_idx    = _bundle["ds_class_index"]
_classes   = _bundle["classes"]
_features  = _bundle["features_all"]

def _derive_size_type(size: str) -> str:
    return "numeric" if str(size).strip().isdigit() else "alpha"

def _recommend_discount(tier: str, sell_through: float) -> dict:
    if tier == "fast_mover":
        return {"discount": 0,  "reason": "Restock — no discount needed"}
    elif tier == "average":
        if sell_through >= 0.40:
            return {"discount": 10, "reason": "Light stimulus — 10% discount"}
        else:
            return {"discount": 20, "reason": "Moderate push — 20% discount"}
    else:
        if sell_through >= 0.15:
            return {"discount": 30, "reason": "Clear before season end — 30% discount"}
        else:
            return {"discount": 50, "reason": "Urgent clearance — 50% discount"}

def predict(
    product_category: str,
    collection_family: str,
    sex: str,
    color: str,
    season: str,
    size: str,
    price: float,
    discount: float,
    sell_through: float = 0.0,
) -> dict:
    norm      = normalize_input(product_category, collection_family, sex, color, season, size)
    v         = norm["values"]
    size_type = _derive_size_type(v["size"])

    row = pd.DataFrame([{
        "price"            : price,
        "discount"         : discount,
        "product_category" : v["product_category"],
        "collection_family": v["collection_family"],
        "sex"              : v["sex"],
        "color"            : v["color"],
        "season"           : v["season"],
        "size"             : v["size"],
        "size_type"        : size_type,
    }])
    proba = _pipeline.predict_proba(row)[0]
    if proba[_ds_idx] >= _threshold:
        tier = "dead_stock"
    else:
        tier = _classes[np.argmax(proba)]
    confidence = round(float(max(proba)), 4)
    rec        = _recommend_discount(tier, sell_through)
    return {
        "predicted_tier"      : tier,
        "confidence"          : confidence,
        "recommended_discount": rec["discount"],
        "reason"              : rec["reason"],
        "probabilities"       : {c: round(float(p), 4) for c, p in zip(_classes, proba)},
        "input_normalizations": norm["mappings"],   # empty list if nothing was remapped
    }
