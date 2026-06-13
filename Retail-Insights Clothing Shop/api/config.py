from pathlib import Path

ROOT        = Path(__file__).resolve().parent.parent
DATA_DIR    = ROOT / "data" / "clean"
MODEL_DIR   = ROOT / "model_package"

CLEAN_CSV   = DATA_DIR / "clothing_clean.csv"
RECS_CSV    = DATA_DIR / "discount_recommendations.csv"
MODEL_PATH  = MODEL_DIR / "model.joblib"

THRESHOLD   = 0.36
LOW_ST      = 0.20   # dead stock threshold
HIGH_ST     = 0.60   # fast mover threshold
REORDER_QTY = 30     # flag fast movers with fewer than this many units remaining
