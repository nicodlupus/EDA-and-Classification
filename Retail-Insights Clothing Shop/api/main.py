import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from schemas import (
    ProductInput, BatchInput, PredictionOutput, BatchOutput,
    RevenueAtRisk, RevenueRecovery, ABCItem, ReorderAlert,
    CollectionROI, MarginRow, GenderSplit, SeasonRow, SummaryResponse,
)
from analytics import (
    get_summary, get_revenue_at_risk, get_revenue_recovery,
    get_abc_analysis, get_reorder_alerts, get_collection_roi,
    get_margin_analysis, get_gender_split, get_season_comparison,
)
from model_package.predictor import predict as _predict

app = FastAPI(
    title       = "Retail Insights API",
    description = "ML-powered inventory intelligence for clothing retail",
    version     = "1.0.0",
)

@app.on_event("startup")
def warmup():
    # Run load_enriched() in a background thread so the API is responsive
    # immediately while the 1,936-row prediction cache builds in the background.
    from analytics import load_enriched
    def _warm():
        try:
            load_enriched()
            print("Cache warmed — all endpoints ready.")
        except Exception as e:
            print(f"Warmup error: {e}")
    threading.Thread(target=_warm, daemon=True).start()

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],   # restrict to Next.js domain in production
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


# ── Prediction ────────────────────────────────────────────────────────────────

@app.post("/predict", response_model=PredictionOutput)
def predict(product: ProductInput):
    try:
        result = _predict(
            product_category  = product.product_category,
            collection_family = product.collection_family,
            sex               = product.sex,
            color             = product.color,
            season            = product.season,
            size              = product.size,
            price             = product.price,
            discount          = product.discount,
            sell_through      = product.sell_through,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/batch", response_model=BatchOutput)
def predict_batch(batch: BatchInput):
    try:
        results = []
        for product in batch.products:
            result = _predict(
                product_category  = product.product_category,
                collection_family = product.collection_family,
                sex               = product.sex,
                color             = product.color,
                season            = product.season,
                size              = product.size,
                price             = product.price,
                discount          = product.discount,
                sell_through      = product.sell_through,
            )
            results.append(result)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Revenue ───────────────────────────────────────────────────────────────────

@app.get("/revenue/at-risk", response_model=RevenueAtRisk)
def revenue_at_risk():
    return get_revenue_at_risk()


@app.get("/revenue/recovery", response_model=list[RevenueRecovery])
def revenue_recovery():
    return get_revenue_recovery()


# ── Analytics ─────────────────────────────────────────────────────────────────

@app.get("/analytics/summary", response_model=SummaryResponse)
def summary():
    return get_summary()


@app.get("/analytics/abc", response_model=list[ABCItem])
def abc():
    return get_abc_analysis()


@app.get("/analytics/reorder", response_model=list[ReorderAlert])
def reorder():
    return get_reorder_alerts()


@app.get("/analytics/collection-roi", response_model=list[CollectionROI])
def collection_roi():
    return get_collection_roi()


@app.get("/analytics/margin", response_model=list[MarginRow])
def margin():
    return get_margin_analysis()


@app.get("/analytics/gender-split", response_model=list[GenderSplit])
def gender_split():
    return get_gender_split()


@app.get("/analytics/season-comparison", response_model=list[SeasonRow])
def season_comparison():
    return get_season_comparison()
