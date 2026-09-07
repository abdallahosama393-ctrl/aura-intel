from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    city: str = Field(..., min_length=1, max_length=60)
    product: str = Field(..., min_length=1, max_length=120)
    language: str = Field(default="ar", min_length=2, max_length=2)

    @field_validator("city", "product")
    @classmethod
    def strip_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("empty value")
        return v

    @field_validator("language")
    @classmethod
    def normalize_language(cls, v: str) -> str:
        return v.strip().lower()


class Competitor(BaseModel):
    name: str
    price: int
    rating: float
    sales_last_30d: int


class TrendPoint(BaseModel):
    label: str
    price: int
    demand: int


class AnalyzeResponse(BaseModel):
    city_label: str
    product: str
    generated_at: str
    currency: str = "IDR"

    avg_price: int
    min_price: int
    max_price: int
    median_price: int

    demand_index: int
    market_saturation: int
    competitor_count: int
    opportunity_score: int

    trend: list[TrendPoint]
    competitors: list[Competitor]

    insight_key: str
    insight_params: dict
    insight_text: str
