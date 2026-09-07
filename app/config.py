"""
Aura Intel — Static configuration and reference data.

This module holds no business logic. It only defines the reference
data pools (cities, languages, store-name components, category
multipliers) that the market simulation engine draws from.
"""

from __future__ import annotations

APP_NAME = "Aura Intel"
APP_TAGLINE_KEY = "app_tagline"

SUPPORTED_LANGUAGES = {
    "ar": {"label": "العربية", "dir": "rtl", "flag": "🇸🇦"},
    "en": {"label": "English", "dir": "ltr", "flag": "🇬🇧"},
    "id": {"label": "Bahasa Indonesia", "dir": "ltr", "flag": "🇮🇩"},
}
DEFAULT_LANGUAGE = "ar"

# Indonesian cities with a relative economic-activity weight.
# The weight nudges price levels and competitor density — larger
# metro markets tend to show more competitors and tighter margins.
CITIES: dict[str, dict] = {
    "jakarta": {"label": "Jakarta", "weight": 1.35, "region": "Jawa"},
    "surabaya": {"label": "Surabaya", "weight": 1.18, "region": "Jawa"},
    "makassar": {"label": "Makassar", "weight": 1.05, "region": "Sulawesi"},
    "bandung": {"label": "Bandung", "weight": 1.12, "region": "Jawa"},
    "medan": {"label": "Medan", "weight": 1.08, "region": "Sumatra"},
    "semarang": {"label": "Semarang", "weight": 0.98, "region": "Jawa"},
    "denpasar": {"label": "Denpasar", "weight": 1.15, "region": "Bali"},
    "yogyakarta": {"label": "Yogyakarta", "weight": 0.95, "region": "Jawa"},
    "palembang": {"label": "Palembang", "weight": 0.92, "region": "Sumatra"},
    "balikpapan": {"label": "Balikpapan", "weight": 1.02, "region": "Kalimantan"},
}
DEFAULT_CITY = "jakarta"

# A few illustrative product categories shown as quick-select chips.
# The engine accepts any free-text product name beyond this list.
SAMPLE_PRODUCTS = [
    "Kopi Kemasan",
    "Skincare Serum",
    "Fashion Muslim",
    "Elektronik Rumah Tangga",
    "Furnitur Minimalis",
    "Makanan Ringan Lokal",
]
DEFAULT_PRODUCT = "Kopi Kemasan"

# Category → (base_price_low, base_price_high) in IDR, used to seed a
# believable price band for arbitrary product names typed by the user.
CATEGORY_PRICE_BANDS = {
    "kopi": (18_000, 65_000),
    "coffee": (18_000, 65_000),
    "skincare": (45_000, 320_000),
    "serum": (60_000, 350_000),
    "fashion": (75_000, 450_000),
    "muslim": (90_000, 500_000),
    "elektronik": (150_000, 3_500_000),
    "electronic": (150_000, 3_500_000),
    "furnitur": (250_000, 4_200_000),
    "furniture": (250_000, 4_200_000),
    "makanan": (8_000, 55_000),
    "snack": (8_000, 55_000),
    "default": (25_000, 400_000),
}

STORE_NAME_PREFIXES = [
    "Toko", "Warung", "Griya", "Rumah", "Butik", "Gudang", "Pasar",
    "Kios", "Sentra", "Mitra",
]
STORE_NAME_CORES = [
    "Nusantara", "Sejahtera", "Makmur", "Berkah", "Cahaya", "Jaya",
    "Mandiri", "Sentosa", "Elok", "Sinar", "Prima", "Abadi",
    "Merdeka", "Harmoni", "Selaras",
]
STORE_NAME_SUFFIXES = ["Official", "Store", "Grosir", "id", "Shop", ""]
