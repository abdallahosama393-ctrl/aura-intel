"""
Aura Intel — Market Simulation Engine.

Generates a believable, internally-consistent market snapshot for a
given (city, product) pair. The simulation is *seeded* so that the
same city/product combination returns a stable "market identity"
(price band, competitor roster, base demand) that only drifts slowly
over time — plus a small live jitter on every call so the dashboard
feels like it is watching a real, moving market rather than a static
fixture.

No external data source is used: this is a self-contained estimator
built for demonstration and exploration purposes, not a live feed of
real prices. That distinction is also surfaced in the UI copy.
"""

from __future__ import annotations

import hashlib
import random
import time
from datetime import datetime, timezone

from app.config import (
    CATEGORY_PRICE_BANDS,
    CITIES,
    DEFAULT_CITY,
    STORE_NAME_CORES,
    STORE_NAME_PREFIXES,
    STORE_NAME_SUFFIXES,
)


def _stable_seed(*parts: str) -> int:
    """A deterministic integer seed derived from the given strings."""
    digest = hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def _live_bucket(width_seconds: int = 300) -> int:
    """Changes every `width_seconds` so results feel 'live' without
    reshuffling on every single request (default: every 5 minutes)."""
    return int(time.time() // width_seconds)


def _detect_price_band(product: str) -> tuple[int, int]:
    normalized = product.strip().lower()
    for keyword, band in CATEGORY_PRICE_BANDS.items():
        if keyword == "default":
            continue
        if keyword in normalized:
            return band
    return CATEGORY_PRICE_BANDS["default"]


def _round_to_nice(value: float) -> int:
    """Round a price to a natural-looking denomination (nearest 500)."""
    return max(500, int(round(value / 500.0) * 500))


def _generate_store_name(rng: random.Random) -> str:
    prefix = rng.choice(STORE_NAME_PREFIXES)
    core = rng.choice(STORE_NAME_CORES)
    suffix = rng.choice(STORE_NAME_SUFFIXES)
    name = f"{prefix} {core}"
    if suffix:
        name = f"{name} {suffix}"
    return name


def _resolve_city(city_key: str) -> tuple[str, dict]:
    key = city_key.strip().lower().replace(" ", "")
    if key in CITIES:
        return key, CITIES[key]
    # Unknown city typed freely by the user: still produce a result,
    # using a neutral weight, and echo back their own label.
    return city_key, {"label": city_key.strip().title(), "weight": 1.0, "region": "N/A"}


def build_market_snapshot(city: str, product: str) -> dict:
    """Return a full, internally-consistent market snapshot.

    The output is a plain dict shaped to populate `AnalyzeResponse`
    (kept as a dict here so callers can freely enrich it, e.g. with
    localized insight text, before validating/serializing).
    """
    city_key, city_meta = _resolve_city(city)
    product_clean = product.strip()

    base_seed = _stable_seed(city_key, product_clean.lower())
    live_seed = _stable_seed(city_key, product_clean.lower(), str(_live_bucket()))

    base_rng = random.Random(base_seed)   # slow-moving "market identity"
    live_rng = random.Random(live_seed)   # fast "right now" jitter

    weight = city_meta.get("weight", 1.0)

    # --- Price band -------------------------------------------------
    low, high = _detect_price_band(product_clean)
    band_span = high - low
    # A stable anchor within the band for this city/product...
    anchor_ratio = base_rng.uniform(0.30, 0.70)
    anchor_price = low + band_span * anchor_ratio * weight
    # ...plus a small live jitter (±4%) so it "breathes" between calls.
    jitter = live_rng.uniform(-0.04, 0.04)
    avg_price = _round_to_nice(anchor_price * (1 + jitter))

    price_spread = base_rng.uniform(0.18, 0.35)
    min_price = _round_to_nice(avg_price * (1 - price_spread))
    max_price = _round_to_nice(avg_price * (1 + price_spread * 1.4))
    median_price = _round_to_nice((avg_price + base_rng.uniform(-0.05, 0.05) * avg_price))
    median_price = max(min_price, min(median_price, max_price))

    # --- Demand & saturation -----------------------------------------
    base_demand = base_rng.uniform(35, 90) * (0.85 + 0.3 * min(weight, 1.4))
    demand_index = int(max(5, min(99, base_demand + live_rng.uniform(-6, 6))))

    competitor_count = int(max(3, min(240, base_rng.uniform(8, 60) * weight)))
    saturation_raw = (competitor_count / 240 * 60) + base_rng.uniform(0, 30)
    market_saturation = int(max(4, min(97, saturation_raw)))

    # Opportunity score rewards high demand + low saturation.
    opportunity_score = int(max(1, min(99, (demand_index * 0.65) - (market_saturation * 0.45) + 45)))

    # --- Trend (last 14 "days") --------------------------------------
    trend = []
    day_labels_en = ["D-13", "D-12", "D-11", "D-10", "D-9", "D-8", "D-7",
                      "D-6", "D-5", "D-4", "D-3", "D-2", "D-1", "Today"]
    walk_price = avg_price * (1 - base_rng.uniform(0.03, 0.08))
    walk_demand = max(10, demand_index - base_rng.uniform(5, 15))
    trend_rng = random.Random(base_seed ^ live_seed)
    for i, label in enumerate(day_labels_en):
        is_last = i == len(day_labels_en) - 1
        if is_last:
            walk_price, walk_demand = avg_price, demand_index
        else:
            walk_price += walk_price * trend_rng.uniform(-0.02, 0.025)
            walk_demand += trend_rng.uniform(-4, 4)
            walk_demand = max(5, min(99, walk_demand))
        trend.append({
            "label": label,
            "price": _round_to_nice(walk_price),
            "demand": int(walk_demand),
        })

    # --- Competitors ---------------------------------------------------
    competitors = []
    seen_names = set()
    comp_rng = random.Random(base_seed + 7)
    n_listed = min(6, max(3, competitor_count // 6 + 3))
    for _ in range(n_listed):
        name = _generate_store_name(comp_rng)
        attempts = 0
        while name in seen_names and attempts < 5:
            name = _generate_store_name(comp_rng)
            attempts += 1
        seen_names.add(name)
        comp_price = _round_to_nice(avg_price * comp_rng.uniform(0.82, 1.22))
        rating = round(comp_rng.uniform(3.6, 5.0), 1)
        sales = int(comp_rng.uniform(15, 60) * weight * (demand_index / 50))
        competitors.append({
            "name": name,
            "price": comp_price,
            "rating": rating,
            "sales_last_30d": sales,
        })
    competitors.sort(key=lambda c: c["sales_last_30d"], reverse=True)

    # --- Insight selection (translated later via locale files) -------
    insight_key, insight_params = _select_insight(
        demand_index=demand_index,
        saturation=market_saturation,
        opportunity=opportunity_score,
        avg_price=avg_price,
        competitor_count=competitor_count,
    )

    return {
        "city_label": city_meta.get("label", city_key.title()),
        "product": product_clean,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "currency": "IDR",
        "avg_price": avg_price,
        "min_price": min_price,
        "max_price": max_price,
        "median_price": median_price,
        "demand_index": demand_index,
        "market_saturation": market_saturation,
        "competitor_count": competitor_count,
        "opportunity_score": opportunity_score,
        "trend": trend,
        "competitors": competitors,
        "insight_key": insight_key,
        "insight_params": insight_params,
    }


def _select_insight(*, demand_index: int, saturation: int, opportunity: int,
                     avg_price: int, competitor_count: int) -> tuple[str, dict]:
    """Pick a scenario key (resolved to text via locale files) plus the
    numeric parameters needed to fill in its placeholders."""
    params = {
        "demand": demand_index,
        "saturation": saturation,
        "opportunity": opportunity,
        "price": f"{avg_price:,}".replace(",", "."),
        "competitors": competitor_count,
    }
    if demand_index >= 65 and saturation <= 40:
        return "insight_high_demand_low_saturation", params
    if demand_index >= 65 and saturation > 40:
        return "insight_high_demand_high_saturation", params
    if demand_index < 40 and saturation <= 40:
        return "insight_low_demand_low_saturation", params
    if demand_index < 40 and saturation > 60:
        return "insight_low_demand_high_saturation", params
    return "insight_balanced_market", params
