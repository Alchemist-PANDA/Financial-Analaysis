"""Pydantic schemas for Startup Hub."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.startup_hub.constants import (
    DEFAULT_AGENT_MATCH_LIMIT,
    ENTITY_TYPE_PUBLIC_STOCK,
    RANKING_COMPONENT_DEFAULT,
    RANKING_SCORE_DEFAULT,
    VERIFICATION_LEVEL_UNVERIFIED,
)


class StartupHubLinkItem(BaseModel):
    label: str
    href: str


class StartupCacheStatus(BaseModel):
    key: str
    source: str = "live"
    ttl_seconds: float = 0.0
    age_seconds: float = 0.0
    is_stale: bool = False


class StartupSourceItem(BaseModel):
    source_name: str
    source_type: str = "reference"
    source_url: str | None = None
    is_official: bool = False
    verification_level: str = VERIFICATION_LEVEL_UNVERIFIED
    published_at: datetime | None = None
    last_checked_at: datetime | None = None
    notes: str | None = None


class StartupRankingBreakdown(BaseModel):
    total_score: float = RANKING_SCORE_DEFAULT
    growth_score: float = RANKING_COMPONENT_DEFAULT
    quality_score: float = RANKING_COMPONENT_DEFAULT
    risk_score: float = RANKING_COMPONENT_DEFAULT
    verification_score: float = RANKING_COMPONENT_DEFAULT
    momentum_score: float = RANKING_COMPONENT_DEFAULT
    top_drivers: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    explanation: str | None = None


class StartupVerificationInfo(BaseModel):
    level: str = VERIFICATION_LEVEL_UNVERIFIED
    label: str = "Unverified"
    tone: str = "neutral"
    description: str = "The record is missing the evidence needed for verification."
    is_verified: bool = False
    checks: dict[str, bool] = Field(default_factory=dict)
    sources_considered: int = 0
    missing_checks: list[str] = Field(default_factory=list)


class StartupMetricItem(BaseModel):
    key: str
    label: str
    value: Any | None = None
    formatted_value: str = "—"
    context: str | None = None


class StartupCompanyListItem(BaseModel):
    slug: str
    company_name: str
    entity_type: str = ENTITY_TYPE_PUBLIC_STOCK
    sector: str | None = None
    ticker: str | None = None
    exchange: str | None = None
    stage: str | None = None
    status_label: str | None = None
    short_summary: str | None = None
    verification_level: str = VERIFICATION_LEVEL_UNVERIFIED
    ranking: StartupRankingBreakdown = Field(default_factory=StartupRankingBreakdown)
    source_count: int = 0
    data_completeness_score: float = 0.0
    research_only: bool = True
    last_updated: datetime | None = None


class StartupCompanyDetailResponse(BaseModel):
    feature: str = "startup_hub_company"
    status: str = "placeholder"
    enabled: bool = False
    disclaimer: list[str] = Field(default_factory=list)
    company: StartupCompanyListItem
    verification: StartupVerificationInfo = Field(default_factory=StartupVerificationInfo)
    thesis_summary: str | None = None
    long_summary: str | None = None
    description: str | None = None
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    metric_highlights: list[StartupMetricItem] = Field(default_factory=list)
    snapshot: dict[str, Any] = Field(default_factory=dict)
    sources: list[StartupSourceItem] = Field(default_factory=list)
    stale: bool = False
    stale_message: str | None = None
    cache_status: StartupCacheStatus | None = None
    last_updated: datetime | None = None


class StartupHubHomeResponse(BaseModel):
    feature: str = "startup_hub_home"
    status: str = "placeholder"
    enabled: bool = False
    disclaimer: list[str] = Field(default_factory=list)
    routes: list[StartupHubLinkItem] = Field(default_factory=list)
    featured: list[StartupCompanyListItem] = Field(default_factory=list)
    public_companies: list[StartupCompanyListItem] = Field(default_factory=list)
    ipo_preview: list[StartupCompanyListItem] = Field(default_factory=list)
    private_preview: list[StartupCompanyListItem] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)
    stale: bool = False
    stale_message: str | None = None
    cache_status: StartupCacheStatus | None = None
    last_updated: datetime | None = None


class StartupAgentQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    entity_type: str | None = None
    limit: int = Field(DEFAULT_AGENT_MATCH_LIMIT, ge=1, le=25)
    include_explanations: bool = True


class StartupAgentQueryResponse(BaseModel):
    feature: str = "startup_hub_agent"
    status: str = "placeholder"
    enabled: bool = False
    disclaimer: list[str] = Field(default_factory=list)
    query: str
    mode: str = "screen"
    interpreted_filters: dict[str, Any] = Field(default_factory=dict)
    summary: str
    reasoning_points: list[str] = Field(default_factory=list)
    comparison: dict[str, Any] = Field(default_factory=dict)
    matches: list[StartupCompanyListItem] = Field(default_factory=list)
    confidence_level: str = "low"
    stale: bool = False
    stale_message: str | None = None
    cache_status: StartupCacheStatus | None = None
    last_updated: datetime | None = None


class StartupCompareResponse(BaseModel):
    feature: str = "startup_hub_compare"
    status: str = "placeholder"
    enabled: bool = False
    disclaimer: list[str] = Field(default_factory=list)
    left: StartupCompanyListItem
    right: StartupCompanyListItem
    left_summary: str | None = None
    right_summary: str | None = None
    category_winners: dict[str, str] = Field(default_factory=dict)
    overall_summary: str
    ai_explanation: str | None = None
    comparison_notes: list[str] = Field(default_factory=list)
    stale: bool = False
    stale_message: str | None = None
    cache_status: StartupCacheStatus | None = None
    last_updated: datetime | None = None
