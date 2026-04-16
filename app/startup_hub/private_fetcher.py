"""Private opportunity refresh flow for Startup Hub."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.startup_hub.constants import ENTITY_TYPE_PRIVATE_OPPORTUNITY, STALE_THRESHOLD_SECONDS
from app.startup_hub.models import StartupCompany, StartupCompanySnapshot, StartupSource
from app.startup_hub.normalizers import normalize_private_opportunity
from app.startup_hub.ranking import compute_total_ranking_score
from app.startup_hub.verification import verify_private_opportunity


_PRIVATE_SEED_PATH = Path(__file__).resolve().parents[2] / "data" / "startup_hub" / "private_opportunities_seed.json"


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


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or isinstance(value, bool):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _source_domain(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    return parsed.netloc or None


def load_private_opportunity_seed() -> list[dict[str, Any]]:
    if not _PRIVATE_SEED_PATH.exists():
        print(f"[SEED ERROR] Private opportunities seed file not found at: {_PRIVATE_SEED_PATH}")
        return []
    payload = json.loads(_PRIVATE_SEED_PATH.read_text(encoding="utf-8"))
    items = payload.get("items") or []
    return [normalize_private_opportunity(item) for item in items if isinstance(item, dict)]


async def fetch_private_opportunity_data(seed_record: dict[str, Any]) -> dict[str, Any]:
    source_items = list(seed_record.get("source_items") or [])
    primary_source = next(
        (
            source
            for source in source_items
            if isinstance(source, dict) and (source.get("is_official") or source.get("source_url"))
        ),
        None,
    )
    return {
        "company_name": seed_record.get("company_name"),
        "valuation_usd": seed_record.get("valuation_usd"),
        "minimum_investment_usd": seed_record.get("minimum_investment_usd"),
        "official_source_url": seed_record.get("official_source_url")
        or (primary_source or {}).get("source_url"),
        "source_name": seed_record.get("source_name") or (primary_source or {}).get("source_name"),
        "research_only": bool(seed_record.get("research_only", True)),
        "source_count": len(source_items),
        "seed_notes": ((seed_record.get("metadata_payload") or {}).get("seed_notes")),
        "fetched_from_seed": True,
    }


def build_private_snapshot(seed_record: dict[str, Any], fetched_data: dict[str, Any]) -> dict[str, Any]:
    now = _utc_now()
    stale_after = now + timedelta(seconds=STALE_THRESHOLD_SECONDS[ENTITY_TYPE_PRIVATE_OPPORTUNITY])

    normalized_seed = normalize_private_opportunity(seed_record)
    source_items = list(normalized_seed.get("source_items") or [])
    valuation_usd = _safe_float(fetched_data.get("valuation_usd"))
    minimum_investment_usd = _safe_float(fetched_data.get("minimum_investment_usd"))
    official_source_url = _string(fetched_data.get("official_source_url")) or normalized_seed.get("official_source_url")
    source_name = _string(fetched_data.get("source_name")) or normalized_seed.get("source_name")
    research_only = bool(fetched_data.get("research_only", normalized_seed.get("research_only", True)))

    metrics_payload = {
        "valuation_usd": valuation_usd,
        "minimum_investment_usd": minimum_investment_usd,
        "freshness_days": 0.0,
        "source_count": len(source_items),
        "research_only": research_only,
    }

    company_payload = {
        **normalized_seed,
        "status_label": normalized_seed.get("status_label") or "research_only",
        "short_summary": normalized_seed.get("short_summary"),
        "valuation_usd": valuation_usd,
        "minimum_investment_usd": minimum_investment_usd,
        "official_source_url": official_source_url,
        "source_name": source_name,
        "research_only": research_only,
        "metrics": metrics_payload,
        "snapshot": {
            "valuation_usd": valuation_usd,
            "minimum_investment_usd": minimum_investment_usd,
            "official_source_url": official_source_url,
            "source_name": source_name,
            "research_only": research_only,
            "snapshot_at": now.isoformat(),
            "stale_after_at": stale_after.isoformat(),
            "analysis_summary": normalized_seed.get("short_summary"),
            "seed_notes": fetched_data.get("seed_notes"),
            "fetched_from_seed": True,
        },
        "source_items": source_items,
        "source_count": len(source_items),
    }

    snapshot_payload = {
        "snapshot_at": now.isoformat(),
        "stale_after_at": stale_after.isoformat(),
        "analysis_summary": normalized_seed.get("short_summary"),
        "valuation_usd": valuation_usd,
        "minimum_investment_usd": minimum_investment_usd,
        "official_source_url": official_source_url,
        "source_name": source_name,
        "research_only": research_only,
        "seed_notes": fetched_data.get("seed_notes"),
        "fetched_from_seed": True,
    }

    verification = verify_private_opportunity(
        company_payload,
        {
            "research_only": research_only,
            "official_source_url": official_source_url,
            "source_name": source_name,
            "data_payload": snapshot_payload,
            "metrics_payload": metrics_payload,
            "completeness_score": company_payload["data_completeness_score"],
        },
        source_items,
    )
    company_payload["verification_level"] = verification["level"]

    ranking = compute_total_ranking_score(
        company_payload,
        {
            "research_only": research_only,
            "official_source_url": official_source_url,
            "source_name": source_name,
            "data_payload": snapshot_payload,
            "metrics_payload": metrics_payload,
            "completeness_score": company_payload["data_completeness_score"],
        },
        source_items,
    )

    return {
        "company": company_payload,
        "snapshot": {
            "snapshot_kind": "private_opportunity_refresh",
            "snapshot_label": f"{company_payload['slug']} private opportunity snapshot",
            "snapshot_at": now,
            "stale_after_at": stale_after,
            "data_payload": snapshot_payload,
            "metrics_payload": metrics_payload,
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
    return age_seconds >= STALE_THRESHOLD_SECONDS[ENTITY_TYPE_PRIVATE_OPPORTUNITY]


def _apply_company_data(company: StartupCompany, payload: dict[str, Any]) -> None:
    company.slug = payload["slug"]
    company.company_name = payload["company_name"]
    company.entity_type = payload["entity_type"]
    company.ticker = payload.get("ticker")
    company.exchange = payload.get("exchange")
    company.sector = payload.get("sector")
    company.stage = payload.get("stage")
    company.status_label = payload.get("status_label")
    company.website_url = payload.get("official_source_url") or payload.get("website_url")
    company.summary_text = payload.get("short_summary")
    company.verification_level = payload.get("verification_level")
    company.source_count = int(payload.get("source_count") or 0)
    company.data_completeness_score = float(payload.get("data_completeness_score") or 0.0)
    company.research_only = bool(payload.get("research_only", True))
    company.latest_snapshot_at = _utc_now()
    company.metadata_payload = {
        "metadata_payload": payload.get("metadata_payload") or {},
        "snapshot": payload.get("snapshot") or {},
        "verification": payload.get("verification") or {},
        "ranking": payload.get("ranking") or {},
    }


async def _refresh_private_opportunities(db: AsyncSession, force_refresh: bool = False) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seed_records = load_private_opportunity_seed()

    for seed_record in seed_records:
        existing_company = (
            await db.execute(
                select(StartupCompany).where(StartupCompany.slug == seed_record["slug"])
            )
        ).scalars().first()

        if not force_refresh and not _is_company_stale(existing_company):
            results.append({"slug": seed_record["slug"], "status": "fresh"})
            continue

        fetched_data = await fetch_private_opportunity_data(seed_record)
        bundle = build_private_snapshot(seed_record, fetched_data)
        bundle["company"]["verification"] = bundle["verification"]
        bundle["company"]["ranking"] = bundle["ranking"]

        company = existing_company or StartupCompany(
            slug=bundle["company"]["slug"],
            company_name=bundle["company"]["company_name"],
            entity_type=ENTITY_TYPE_PRIVATE_OPPORTUNITY,
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
                "status": "refreshed" if existing_company else "created",
                "verification_level": bundle["verification"]["level"],
                "total_score": bundle["ranking"]["total_score"],
            }
        )

    await db.commit()
    return results


async def refresh_private_opportunities(
    db: AsyncSession | None = None,
    force_refresh: bool = False,
) -> list[dict[str, Any]]:
    if db is not None:
        return await _refresh_private_opportunities(db, force_refresh=force_refresh)

    async with async_session() as session:
        return await _refresh_private_opportunities(session, force_refresh=force_refresh)
