"""Public stock refresh flow for Startup Hub."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import get_cached_entry, set_cached
from app.database import async_session
from app.services.analysis_fast import run_fast_analysis
from app.startup_hub.constants import (
    ENTITY_TYPE_PUBLIC_STOCK,
    STALE_THRESHOLD_SECONDS,
)
from app.startup_hub.models import StartupCompany, StartupCompanySnapshot, StartupSource
from app.startup_hub.normalizers import (
    compute_data_completeness_score,
    normalize_public_company,
    safe_float,
)
from app.startup_hub.ranking import compute_total_ranking_score
from app.startup_hub.verification import verify_public_company


_PUBLIC_SEED_PATH = Path(__file__).resolve().parents[2] / "data" / "startup_hub" / "public_startups_seed.json"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _latest_year(metrics_payload: dict[str, Any]) -> dict[str, Any]:
    yearly = list(metrics_payload.get("yearly") or [])
    return yearly[-1] if yearly else {}


def _revenue_growth_pct(metrics_payload: dict[str, Any]) -> float | None:
    yearly = list(metrics_payload.get("yearly") or [])
    if len(yearly) < 2:
        return safe_float(metrics_payload.get("revenue_cagr_pct"))

    latest_revenue = safe_float(yearly[-1].get("revenue"))
    prior_revenue = safe_float(yearly[-2].get("revenue"))
    if latest_revenue is None or prior_revenue in (None, 0):
        return safe_float(metrics_payload.get("revenue_cagr_pct"))
    return round(((latest_revenue / prior_revenue) - 1.0) * 100.0, 2)


def _source_domain(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    return parsed.netloc or None


def load_public_seed_companies() -> list[dict[str, Any]]:
    if not _PUBLIC_SEED_PATH.exists():
        print(f"[SEED ERROR] Public startups seed file not found at: {_PUBLIC_SEED_PATH}")
        return []
    payload = json.loads(_PUBLIC_SEED_PATH.read_text(encoding="utf-8"))
    items = payload.get("items") or []
    return [normalize_public_company(item) for item in items if isinstance(item, dict)]


async def fetch_public_company_data(seed_record: dict[str, Any]) -> dict[str, Any]:
    ticker = _string(seed_record.get("ticker"))
    if not ticker:
        return {
            "ticker": None,
            "company_name": seed_record.get("company_name"),
            "metrics": {},
            "analysis": {},
            "scorecard": {},
            "color_signal": None,
            "fetch_error": "Ticker missing from seed record.",
        }

    normalized_ticker = ticker.upper()
    cached_entry = get_cached_entry(normalized_ticker)
    if cached_entry is not None and not cached_entry["stale"]:
        return dict(cached_entry["data"] or {})

    try:
        fetched = await run_fast_analysis(normalized_ticker)
        set_cached(normalized_ticker, fetched)
        return dict(fetched or {})
    except Exception as exc:
        return {
            "ticker": normalized_ticker,
            "company_name": seed_record.get("company_name") or normalized_ticker,
            "metrics": {},
            "analysis": {},
            "scorecard": {},
            "color_signal": None,
            "fetch_error": str(exc),
        }


def build_public_snapshot(seed_record: dict[str, Any], fetched_data: dict[str, Any]) -> dict[str, Any]:
    now = _utc_now()
    stale_after = now + timedelta(seconds=STALE_THRESHOLD_SECONDS[ENTITY_TYPE_PUBLIC_STOCK])

    normalized_seed = normalize_public_company(seed_record)
    fetched_metrics = dict(fetched_data.get("metrics") or {})
    latest_year = _latest_year(fetched_metrics)
    analysis = dict(fetched_data.get("analysis") or {})
    scorecard = dict(fetched_data.get("scorecard") or {})

    enriched_metrics = {
        **dict(normalized_seed.get("metrics") or {}),
        "revenue_growth_pct": _revenue_growth_pct(fetched_metrics),
        "revenue_cagr_pct": safe_float(fetched_metrics.get("revenue_cagr_pct")),
        "ebitda_margin_pct": safe_float(latest_year.get("ebitda_margin")),
        "fcf_conversion_pct": safe_float(fetched_metrics.get("current_fcf_conversion_pct")),
        "current_fcf_conversion_pct": safe_float(fetched_metrics.get("current_fcf_conversion_pct")),
        "current_roe": safe_float(fetched_metrics.get("current_roe")),
        "current_dso": safe_float(fetched_metrics.get("current_dso")),
        "current_inventory_turnover": safe_float(fetched_metrics.get("current_inventory_turnover")),
        "z_score": safe_float(fetched_metrics.get("current_z_score")),
        "current_z_score": safe_float(fetched_metrics.get("current_z_score")),
        "health_score": safe_float(scorecard.get("health_score")),
        "health_band": _string(scorecard.get("health_band")),
        "margin_signal": _string(fetched_metrics.get("margin_signal")),
        "solvency_signal": _string(fetched_metrics.get("solvency_signal")),
        "freshness_days": 0.0,
    }

    source_items = list(normalized_seed.get("source_items") or [])
    company_payload = {
        **normalized_seed,
        "ticker": _string(fetched_data.get("ticker")) or normalized_seed.get("ticker"),
        "company_name": _string(fetched_data.get("company_name")) or normalized_seed.get("company_name"),
        "short_summary": _string(analysis.get("analyst_verdict_summary")) or normalized_seed.get("short_summary"),
        "status_label": normalized_seed.get("status_label") or "active",
        "metrics": enriched_metrics,
        "snapshot": {
            "ticker": _string(fetched_data.get("ticker")) or normalized_seed.get("ticker"),
            "exchange": normalized_seed.get("exchange"),
            "status_label": normalized_seed.get("status_label") or "active",
            "snapshot_at": now.isoformat(),
            "stale_after_at": stale_after.isoformat(),
            "analysis_summary": _string(analysis.get("analyst_verdict_summary")),
            "color_signal": _string(fetched_data.get("color_signal")),
        },
        "source_items": source_items,
        "source_count": len(source_items),
    }

    company_payload["data_completeness_score"] = compute_data_completeness_score(
        {
            "company_name": company_payload["company_name"],
            "ticker": company_payload["ticker"],
            "exchange": company_payload.get("exchange"),
            "sector": company_payload.get("sector"),
            "summary": company_payload.get("short_summary"),
            "revenue_cagr_pct": enriched_metrics.get("revenue_cagr_pct"),
            "ebitda_margin_pct": enriched_metrics.get("ebitda_margin_pct"),
            "current_roe": enriched_metrics.get("current_roe"),
            "current_z_score": enriched_metrics.get("current_z_score"),
            "source_items": source_items,
        }
    )

    snapshot_payload = {
        "snapshot_at": now.isoformat(),
        "stale_after_at": stale_after.isoformat(),
        "analysis_summary": _string(analysis.get("analyst_verdict_summary")),
        "analysis": analysis,
        "scorecard": scorecard,
        "color_signal": _string(fetched_data.get("color_signal")),
        "fetch_error": _string(fetched_data.get("fetch_error")),
        "historical_metrics": list(fetched_metrics.get("yearly") or []),
    }

    verification = verify_public_company(
        company_payload,
        {
            "exchange": company_payload.get("exchange"),
            "ticker": company_payload.get("ticker"),
            "metrics_payload": enriched_metrics,
            "data_payload": snapshot_payload,
            "completeness_score": company_payload["data_completeness_score"],
        },
        source_items,
    )
    company_payload["verification_level"] = verification["level"]

    ranking = compute_total_ranking_score(
        company_payload,
        {
            "exchange": company_payload.get("exchange"),
            "ticker": company_payload.get("ticker"),
            "metrics_payload": enriched_metrics,
            "data_payload": snapshot_payload,
            "completeness_score": company_payload["data_completeness_score"],
        },
        source_items,
    )

    return {
        "company": company_payload,
        "snapshot": {
            "snapshot_kind": "public_stock_refresh",
            "snapshot_label": f"{company_payload['ticker'] or company_payload['slug']} public snapshot",
            "snapshot_at": now,
            "stale_after_at": stale_after,
            "data_payload": snapshot_payload,
            "metrics_payload": enriched_metrics,
            "ranking_payload": ranking,
            "completeness_score": company_payload["data_completeness_score"],
        },
        "sources": source_items,
        "verification": verification,
        "ranking": ranking,
        "fetched_data": fetched_data,
    }


def _is_company_stale(company: StartupCompany | None) -> bool:
    if company is None or company.latest_snapshot_at is None:
        return True
    snapshot_at = _as_utc(company.latest_snapshot_at)
    if snapshot_at is None:
        return True
    age_seconds = (_utc_now() - snapshot_at).total_seconds()
    return age_seconds >= STALE_THRESHOLD_SECONDS[ENTITY_TYPE_PUBLIC_STOCK]


def _apply_company_data(company: StartupCompany, payload: dict[str, Any]) -> None:
    company.slug = payload["slug"]
    company.company_name = payload["company_name"]
    company.entity_type = payload["entity_type"]
    company.ticker = payload.get("ticker")
    company.exchange = payload.get("exchange")
    company.sector = payload.get("sector")
    company.stage = payload.get("stage")
    company.status_label = payload.get("status_label")
    company.website_url = payload.get("website_url")
    company.summary_text = payload.get("short_summary")
    company.verification_level = payload.get("verification_level")
    company.source_count = int(payload.get("source_count") or 0)
    company.data_completeness_score = float(payload.get("data_completeness_score") or 0.0)
    company.research_only = bool(payload.get("research_only", True))
    company.latest_snapshot_at = _utc_now()
    company.metadata_payload = {
        "metadata_payload": payload.get("metadata_payload") or {},
        "verification": payload.get("verification") or {},
        "ranking": payload.get("ranking") or {},
    }


async def _refresh_public_companies(db: AsyncSession, force_refresh: bool = False) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seed_records = load_public_seed_companies()

    for seed_record in seed_records:
        existing_company = (
            await db.execute(select(StartupCompany).where(StartupCompany.slug == seed_record["slug"]))
        ).scalars().first()

        if not force_refresh and not _is_company_stale(existing_company):
            results.append({"slug": seed_record["slug"], "status": "fresh"})
            continue

        fetched_data = await fetch_public_company_data(seed_record)
        bundle = build_public_snapshot(seed_record, fetched_data)
        bundle["company"]["verification"] = bundle["verification"]
        bundle["company"]["ranking"] = bundle["ranking"]

        company = existing_company or StartupCompany(
            slug=bundle["company"]["slug"],
            company_name=bundle["company"]["company_name"],
            entity_type=ENTITY_TYPE_PUBLIC_STOCK,
        )
        db.add(company)
        await db.flush()

        _apply_company_data(company, bundle["company"])
        await db.flush()

        await db.execute(delete(StartupSource).where(StartupSource.company_id == company.id))
        await db.execute(delete(StartupCompanySnapshot).where(StartupCompanySnapshot.company_id == company.id))

        snapshot = StartupCompanySnapshot(
            company_id=company.id,
            snapshot_kind=bundle["snapshot"]["snapshot_kind"],
            snapshot_label=bundle["snapshot"]["snapshot_label"],
            snapshot_at=bundle["snapshot"]["snapshot_at"],
            stale_after_at=bundle["snapshot"]["stale_after_at"],
            data_payload=bundle["snapshot"]["data_payload"],
            metrics_payload=bundle["snapshot"]["metrics_payload"],
            ranking_payload=bundle["snapshot"]["ranking_payload"],
            completeness_score=bundle["snapshot"]["completeness_score"],
        )
        db.add(snapshot)
        await db.flush()

        for source in bundle["sources"]:
            db.add(
                StartupSource(
                    company_id=company.id,
                    snapshot_id=snapshot.id,
                    source_name=source.get("source_name") or "Unknown Source",
                    source_type=source.get("source_type") or "reference",
                    source_url=source.get("source_url"),
                    source_domain=_source_domain(source.get("source_url")),
                    source_title=None,
                    verification_level=source.get("verification_level") or bundle["verification"]["level"],
                    is_official=bool(source.get("is_official", False)),
                    published_at=None,
                    last_checked_at=_utc_now(),
                    metadata_payload={"notes": source.get("notes")},
                )
            )

        results.append(
            {
                "slug": company.slug,
                "ticker": company.ticker,
                "status": "refreshed" if existing_company else "created",
                "total_score": bundle["ranking"]["total_score"],
                "verification_level": bundle["verification"]["level"],
            }
        )

    await db.commit()
    return results


async def refresh_public_companies(
    db: AsyncSession | None = None,
    force_refresh: bool = False,
) -> list[dict[str, Any]]:
    if db is not None:
        return await _refresh_public_companies(db, force_refresh=force_refresh)

    async with async_session() as session:
        return await _refresh_public_companies(session, force_refresh=force_refresh)
