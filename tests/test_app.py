from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.market_engine import build_market_snapshot

client = TestClient(app)


# ---------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------

class TestDashboardPage:
    def test_root_returns_200(self):
        res = client.get("/")
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]

    @pytest.mark.parametrize("lang,expected_dir", [
        ("ar", "rtl"),
        ("en", "ltr"),
        ("id", "ltr"),
    ])
    def test_language_switch_sets_direction(self, lang, expected_dir):
        res = client.get(f"/?lang={lang}")
        assert res.status_code == 200
        assert f'dir="{expected_dir}"' in res.text
        assert f'lang="{lang}"' in res.text

    def test_unsupported_language_falls_back_to_default(self):
        res = client.get("/?lang=fr")
        assert res.status_code == 200
        # default language is Arabic (rtl)
        assert 'dir="rtl"' in res.text

    def test_page_contains_expected_sections(self):
        res = client.get("/?lang=en")
        assert "Run analysis" in res.text
        assert "Market overview" in res.text or "overview" in res.text.lower()
        assert "trend-chart" in res.text

    def test_static_js_is_served(self):
        res = client.get("/static/js/app.js")
        assert res.status_code == 200
        assert "runAnalysis" in res.text


# ---------------------------------------------------------------------
# Health & meta endpoints
# ---------------------------------------------------------------------

class TestUtilityEndpoints:
    def test_health(self):
        res = client.get("/health")
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "ok"

    def test_meta_returns_cities_and_dictionary(self):
        res = client.get("/api/meta?lang=en")
        assert res.status_code == 200
        body = res.json()
        assert "jakarta" in body["cities"]
        assert body["direction"] == "ltr"
        assert "app_name" in body["dictionary"]


# ---------------------------------------------------------------------
# Analyze API
# ---------------------------------------------------------------------

class TestAnalyzeAPI:
    def test_valid_request_returns_full_snapshot(self):
        res = client.post("/api/analyze", json={
            "city": "makassar", "product": "Kopi Kemasan", "language": "en",
        })
        assert res.status_code == 200
        body = res.json()

        for key in [
            "city_label", "product", "avg_price", "min_price", "max_price",
            "median_price", "demand_index", "market_saturation",
            "competitor_count", "opportunity_score", "trend", "competitors",
            "insight_key", "insight_params",
        ]:
            assert key in body

        assert body["city_label"] == "Makassar"
        assert body["min_price"] <= body["avg_price"] <= body["max_price"]
        assert 0 <= body["demand_index"] <= 100
        assert 0 <= body["market_saturation"] <= 100
        assert 0 <= body["opportunity_score"] <= 100
        assert len(body["trend"]) == 14
        assert len(body["competitors"]) >= 3

    def test_insight_text_is_populated_and_translated(self):
        res_en = client.post("/api/analyze", json={
            "city": "jakarta", "product": "Skincare Serum", "language": "en",
        })
        res_id = client.post("/api/analyze", json={
            "city": "jakarta", "product": "Skincare Serum", "language": "id",
        })
        assert res_en.status_code == res_id.status_code == 200
        text_en = res_en.json()["insight_text"]
        text_id = res_id.json()["insight_text"]
        assert text_en and text_id
        assert text_en != text_id  # different languages must render different text

    def test_unknown_city_is_still_handled_gracefully(self):
        res = client.post("/api/analyze", json={
            "city": "Kota Baru", "product": "Elektronik", "language": "en",
        })
        assert res.status_code == 200
        assert res.json()["city_label"]

    @pytest.mark.parametrize("payload", [
        {"city": "", "product": "Kopi", "language": "en"},
        {"city": "jakarta", "product": "", "language": "en"},
        {"city": "jakarta", "product": "   ", "language": "en"},
    ])
    def test_blank_fields_are_rejected(self, payload):
        res = client.post("/api/analyze", json=payload)
        assert res.status_code == 422

    def test_missing_fields_are_rejected(self):
        res = client.post("/api/analyze", json={"city": "jakarta"})
        assert res.status_code == 422

    def test_competitors_are_sorted_by_sales_descending(self):
        res = client.post("/api/analyze", json={
            "city": "surabaya", "product": "Furnitur Minimalis", "language": "en",
        })
        sales = [c["sales_last_30d"] for c in res.json()["competitors"]]
        assert sales == sorted(sales, reverse=True)


# ---------------------------------------------------------------------
# Market engine (unit level)
# ---------------------------------------------------------------------

class TestMarketEngine:
    def test_snapshot_shape(self):
        snap = build_market_snapshot("jakarta", "Kopi Kemasan")
        assert snap["min_price"] <= snap["avg_price"] <= snap["max_price"]
        assert len(snap["trend"]) == 14
        assert snap["trend"][-1]["price"] == snap["avg_price"]
        assert snap["trend"][-1]["demand"] == snap["demand_index"]

    def test_same_inputs_are_stable_within_the_same_live_window(self):
        snap_a = build_market_snapshot("jakarta", "Kopi Kemasan")
        snap_b = build_market_snapshot("jakarta", "Kopi Kemasan")
        # Same city/product called back-to-back should match (same live bucket).
        assert snap_a["avg_price"] == snap_b["avg_price"]
        assert snap_a["competitors"] == snap_b["competitors"]

    def test_different_products_yield_different_price_bands(self):
        coffee = build_market_snapshot("jakarta", "Kopi Kemasan")
        electronics = build_market_snapshot("jakarta", "Elektronik Rumah Tangga")
        assert coffee["avg_price"] != electronics["avg_price"]
        # Electronics category should generally command a higher price band.
        assert electronics["avg_price"] > coffee["avg_price"]

    def test_city_weight_influences_competitor_count(self):
        # Jakarta has a materially higher weight than Yogyakarta in config,
        # so it should not systematically produce fewer competitors across
        # a handful of product samples.
        products = ["Kopi Kemasan", "Skincare Serum", "Fashion Muslim"]
        jakarta_counts = [build_market_snapshot("jakarta", p)["competitor_count"] for p in products]
        jogja_counts = [build_market_snapshot("yogyakarta", p)["competitor_count"] for p in products]
        assert sum(jakarta_counts) >= sum(jogja_counts)

    def test_insight_key_is_one_of_known_scenarios(self):
        snap = build_market_snapshot("medan", "Makanan Ringan Lokal")
        assert snap["insight_key"] in {
            "insight_high_demand_low_saturation",
            "insight_high_demand_high_saturation",
            "insight_low_demand_low_saturation",
            "insight_low_demand_high_saturation",
            "insight_balanced_market",
        }
