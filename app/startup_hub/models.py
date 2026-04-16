"""SQLAlchemy models for Startup Hub."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.startup_hub.constants import VERIFICATION_LEVEL_UNVERIFIED


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StartupCompany(Base):
    __tablename__ = "startup_companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255), index=True)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    ticker: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    exchange: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(120), nullable=True)
    stage: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status_label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    headquarters: Mapped[str | None] = mapped_column(String(120), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_level: Mapped[str] = mapped_column(
        String(50), default=VERIFICATION_LEVEL_UNVERIFIED, index=True
    )
    source_count: Mapped[int] = mapped_column(default=0)
    data_completeness_score: Mapped[float] = mapped_column(Float, default=0.0)
    research_only: Mapped[bool] = mapped_column(Boolean, default=True)
    latest_snapshot_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now
    )


class StartupCompanySnapshot(Base):
    __tablename__ = "startup_company_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("startup_companies.id"), index=True)
    snapshot_kind: Mapped[str] = mapped_column(String(50), default="seed")
    snapshot_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    snapshot_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stale_after_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    ranking_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    completeness_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)


class StartupSource(Base):
    __tablename__ = "startup_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("startup_companies.id"), index=True)
    snapshot_id: Mapped[int | None] = mapped_column(
        ForeignKey("startup_company_snapshots.id"), nullable=True, index=True
    )
    source_name: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(80), default="reference")
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verification_level: Mapped[str] = mapped_column(
        String(50), default=VERIFICATION_LEVEL_UNVERIFIED, index=True
    )
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)


class StartupNewsSignal(Base):
    __tablename__ = "startup_news_signals"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("startup_companies.id"), index=True)
    snapshot_id: Mapped[int | None] = mapped_column(
        ForeignKey("startup_company_snapshots.id"), nullable=True, index=True
    )
    headline: Mapped[str] = mapped_column(String(500))
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    signal_type: Mapped[str] = mapped_column(String(80), default="news")
    signal_direction: Mapped[str | None] = mapped_column(String(30), nullable=True)
    signal_strength: Mapped[float] = mapped_column(Float, default=0.0)
    signal_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)


class StartupAgentLog(Base):
    __tablename__ = "startup_agent_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    query_text: Mapped[str] = mapped_column(Text)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    filters_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    response_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    matched_company_slugs: Mapped[list] = mapped_column(JSON, default=list)
    disclaimer_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)


class StartupManualOverride(Base):
    __tablename__ = "startup_manual_overrides"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("startup_companies.id"), index=True)
    field_name: Mapped[str] = mapped_column(String(120), index=True)
    override_value: Mapped[dict] = mapped_column(JSON, default=dict)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
