"""
Normalizes incoming categorical values to the closest known training vocabulary.

Why this exists:
  The model uses OHE. If "Wine Red" arrives and it wasn't in training, OHE produces
  an all-zero column — the model has no signal. This module maps it to "Burgundy"
  before prediction, making the model robust to collection/color renames.

Two-layer strategy:
  Layer 1 — Alias dict: hand-curated map of known synonyms and renames.
             Used first, highest confidence. Catches semantic similarities
             (Wine Red → Burgundy) that string metrics can't handle.

  Layer 2 — Fuzzy matching: partial_ratio finds substrings
             ("dark burgundy" → "Burgundy", "rainforest collection" → "Rainforest").
             Only applied if Layer 1 misses.

  If both layers miss (score < threshold), value is passed through unchanged.
  The OHE will produce a zero-vector for unknown values — prediction will still
  run but confidence will be low.
"""

from rapidfuzz import process, fuzz

# ── Training vocabulary ────────────────────────────────────────────────────────

VOCAB = {
    "product_category": [
        "Accessories", "Pants", "Polo", "Shirt", "Shoes",
        "Shorts", "Sweatshirt", "Swimwear", "T-Shirt",
    ],
    "collection_family": [
        "Box Logo", "Circular", "Cresta", "Geographic", "Iconic",
        "Morgex", "Patch", "Rainforest", "Slate", "Sun-Lover",
        "Trail", "Tribe", "Wave",
    ],
    "sex": ["Men", "Women"],
    "color": [
        "Beige Sand", "Black Beauty", "Blue Marine", "Bright Red",
        "Bright White", "Burgundy", "Caviar", "Forest Green", "Free Blue",
        "Green Lichen", "Grey Melange", "Khaki", "Navy", "Old Rose",
        "Olive", "Orange Tangerine", "Pale Mint", "Petit Four",
        "Snow White", "Stone Grey", "White Whisper", "Yellow Sunshine",
    ],
    "season": ["FS24", "SS25"],
    "size": [
        "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46",
        "XS", "S", "M", "L", "XL", "XXL", "One Size",
    ],
}

# ── Layer 1: alias dictionaries ────────────────────────────────────────────────
# Key = lowercase incoming value (or prefix), Value = canonical training value
# Add new aliases here as the company renames things each season.

COLOR_ALIASES: dict[str, str] = {
    # Red family → Burgundy
    "wine red"         : "Burgundy",
    "wine"             : "Burgundy",
    "bordeaux"         : "Burgundy",
    "maroon"           : "Burgundy",
    "claret"           : "Burgundy",
    "dark red"         : "Burgundy",
    # Red family → Bright Red
    "crimson"          : "Bright Red",
    "scarlet"          : "Bright Red",
    "deep red"         : "Bright Red",
    "fire red"         : "Bright Red",
    "tomato"           : "Bright Red",
    "red"              : "Bright Red",
    # White family
    "white"            : "Bright White",
    "off white"        : "Snow White",
    "ivory"            : "Snow White",
    "cream"            : "Snow White",
    "ecru"             : "Snow White",
    "pearl"            : "Snow White",
    "chalk"            : "Bright White",
    "optical white"    : "Bright White",
    # Black / dark
    "black"            : "Black Beauty",
    "jet black"        : "Black Beauty",
    "charcoal black"   : "Black Beauty",
    "onyx"             : "Black Beauty",
    # Caviar (dark near-black)
    "dark caviar"      : "Caviar",
    "deep black"       : "Caviar",
    # Navy / blue family
    "dark blue"        : "Navy",
    "deep blue"        : "Navy",
    "midnight blue"    : "Navy",
    "ink blue"         : "Navy",
    "royal blue"       : "Blue Marine",
    "marine blue"      : "Blue Marine",
    "cobalt"           : "Blue Marine",
    "cerulean"         : "Free Blue",
    "sky blue"         : "Free Blue",
    "electric blue"    : "Free Blue",
    "blue"             : "Blue Marine",
    # Green family
    "dark green"       : "Forest Green",
    "bottle green"     : "Forest Green",
    "hunter green"     : "Forest Green",
    "racing green"     : "Forest Green",
    "green"            : "Forest Green",
    "sage"             : "Green Lichen",
    "sage green"       : "Green Lichen",
    "moss green"       : "Green Lichen",
    "army green"       : "Olive",
    "military green"   : "Olive",
    "khaki green"      : "Olive",
    "mint"             : "Pale Mint",
    "mint green"       : "Pale Mint",
    "light green"      : "Pale Mint",
    # Grey family
    "grey"             : "Grey Melange",
    "gray"             : "Grey Melange",
    "light grey"       : "Grey Melange",
    "dark grey"        : "Stone Grey",
    "dark gray"        : "Stone Grey",
    "slate grey"       : "Stone Grey",
    "charcoal"         : "Stone Grey",
    "silver"           : "Grey Melange",
    # Beige / sand
    "sand"             : "Beige Sand",
    "beige"            : "Beige Sand",
    "camel"            : "Beige Sand",
    "tan"              : "Beige Sand",
    "desert"           : "Beige Sand",
    # Orange
    "orange"           : "Orange Tangerine",
    "tangerine"        : "Orange Tangerine",
    "burnt orange"     : "Orange Tangerine",
    # Pink / rose
    "pink"             : "Old Rose",
    "rose"             : "Old Rose",
    "blush"            : "Old Rose",
    "dusty pink"       : "Old Rose",
    "dusty rose"       : "Old Rose",
    "light pink"       : "Pale Mint",
    # Yellow
    "yellow"           : "Yellow Sunshine",
    "mustard"          : "Yellow Sunshine",
    "lemon"            : "Yellow Sunshine",
    "gold"             : "Yellow Sunshine",
    # Lavender / pink tones
    "lavender"         : "Petit Four",
    "lilac"            : "Petit Four",
    "mauve"            : "Petit Four",
    "pastel purple"    : "Petit Four",
}

COLLECTION_ALIASES: dict[str, str] = {
    "patch+box logo"   : "Patch",
    "patch box logo"   : "Patch",
    "boxlogo"          : "Box Logo",
    "box-logo"         : "Box Logo",
    "box logo patch"   : "Box Logo",
    "sun lover"        : "Sun-Lover",
    "sunlover"         : "Sun-Lover",
}

CATEGORY_ALIASES: dict[str, str] = {
    "tshirt"           : "T-Shirt",
    "t shirt"          : "T-Shirt",
    "tee"              : "T-Shirt",
    "tee shirt"        : "T-Shirt",
    "hoodie"           : "Sweatshirt",
    "sweater"          : "Sweatshirt",
    "jumper"           : "Sweatshirt",
    "crewneck"         : "Sweatshirt",
    "trousers"         : "Pants",
    "jeans"            : "Pants",
    "chinos"           : "Pants",
    "sneakers"         : "Shoes",
    "trainers"         : "Shoes",
    "footwear"         : "Shoes",
    "accessory"        : "Accessories",
    "acc"              : "Accessories",
    "hat"              : "Accessories",
    "cap"              : "Accessories",
    "bag"              : "Accessories",
    "swim"             : "Swimwear",
    "swimsuit"         : "Swimwear",
    "boardshorts"      : "Shorts",
}

FIELD_ALIASES = {
    "color"            : COLOR_ALIASES,
    "collection_family": COLLECTION_ALIASES,
    "product_category" : CATEGORY_ALIASES,
}

FUZZY_THRESHOLD = 80   # minimum partial_ratio score to accept a fuzzy match


def normalize_field(field: str, value: str) -> dict:
    candidates = VOCAB.get(field)
    if not candidates:
        return {"matched": value, "original": value, "score": 100.0, "was_mapped": False}

    value_clean = value.strip()

    # exact match (case-insensitive)
    for c in candidates:
        if c.lower() == value_clean.lower():
            return {"matched": c, "original": value, "score": 100.0, "was_mapped": False}

    # layer 1: alias dict
    aliases = FIELD_ALIASES.get(field, {})
    alias_hit = aliases.get(value_clean.lower())
    if alias_hit:
        return {
            "matched"   : alias_hit,
            "original"  : value,
            "score"     : 100.0,
            "was_mapped": True,
        }

    # layer 2: fuzzy partial_ratio (good for substrings, extra words)
    result = process.extractOne(
        value_clean, candidates,
        scorer=fuzz.partial_ratio,
    )
    if result and result[1] >= FUZZY_THRESHOLD:
        matched, score, _ = result
        return {
            "matched"   : matched,
            "original"  : value,
            "score"     : round(float(score), 1),
            "was_mapped": matched.lower() != value_clean.lower(),
        }

    # no match — pass through, model will handle via OHE fallback
    return {"matched": value_clean, "original": value, "score": 0.0, "was_mapped": False}


def normalize_input(
    product_category: str,
    collection_family: str,
    sex: str,
    color: str,
    season: str,
    size: str,
) -> dict:
    fields = {
        "product_category" : product_category,
        "collection_family": collection_family,
        "sex"              : sex,
        "color"            : color,
        "season"           : season,
        "size"             : size,
    }
    normalized = {}
    mappings   = []

    for field, value in fields.items():
        result = normalize_field(field, value)
        normalized[field] = result["matched"]
        if result["was_mapped"]:
            mappings.append({
                "field"   : field,
                "original": result["original"],
                "matched" : result["matched"],
                "score"   : result["score"],
            })

    return {"values": normalized, "mappings": mappings}
