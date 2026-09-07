from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.config import (
    APP_NAME,
    CITIES,
    DEFAULT_CITY,
    DEFAULT_PRODUCT,
    SAMPLE_PRODUCTS,
    SUPPORTED_LANGUAGES,
)
from app.i18n import get_dictionary, get_direction, normalize_language
from app.market_engine import build_market_snapshot
from app.schemas import AnalyzeRequest, AnalyzeResponse

BASE_DIR = Path(__file__).parent

app = FastAPI(
    title=APP_NAME,
    description="Market and economic intelligence simulation for digital merchants in Indonesia.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _analyze(city: str, product: str, language: str) -> AnalyzeResponse:
    snapshot = build_market_snapshot(city=city, product=product)
    lang = normalize_language(language)
    dictionary = get_dictionary(lang)
    template_text = dictionary.get(snapshot["insight_key"], snapshot["insight_key"])
    try:
        insight_text = template_text.format(**snapshot["insight_params"])
    except (KeyError, IndexError):
        insight_text = template_text
    snapshot["insight_text"] = insight_text
    return AnalyzeResponse(**snapshot)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, lang: str = Query(default="ar")) -> HTMLResponse:
    language = normalize_language(lang)
    dictionary = get_dictionary(language)
    direction = get_direction(language)

    default_city_key = DEFAULT_CITY
    default_city_label = CITIES[default_city_key]["label"]
    snapshot = _analyze(default_city_key, DEFAULT_PRODUCT, language)

    context = {
        "request": request,
        "app_name": APP_NAME,
        "t": dictionary,
        "lang": language,
        "dir": direction,
        "languages": SUPPORTED_LANGUAGES,
        "cities": CITIES,
        "default_city_key": default_city_key,
        "default_city_label": default_city_label,
        "default_product": DEFAULT_PRODUCT,
        "sample_products": SAMPLE_PRODUCTS,
        "initial_snapshot": snapshot.model_dump(),
        "initial_insight_text": snapshot.insight_text,
    }
    return templates.TemplateResponse("index.html", context)


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return _analyze(payload.city, payload.product, payload.language)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/meta")
async def meta(lang: str = Query(default="ar")) -> JSONResponse:
    """Reference data for the frontend: cities, sample products, dictionary."""
    language = normalize_language(lang)
    return JSONResponse(content={
        "language": language,
        "direction": get_direction(language),
        "cities": CITIES,
        "sample_products": SAMPLE_PRODUCTS,
        "dictionary": get_dictionary(language),
    })


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse(content={"status": "ok", "service": APP_NAME})
