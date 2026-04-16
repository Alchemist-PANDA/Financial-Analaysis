"""IPO Watch refresh flow for Startup Hub."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.startup_hub.constants import ENTITY_TYPE_IPO_WATCH, STALE_THRESHOLD_SECONDS
from app.startup_hub.models import StartupCompany, StartupCompanySnapshot, StartupSource
from app.startup_hub.normalizers import normalize_ipo_company
from app.startup_hub.ranking import compute_total_ranking_score
from app.startup_hub.verification import verify_ipo_company


_IPO_SEED_PATH = Path(__file__).resolve().parents[2] / "data" / "startup_hub" / "ipo_seed.json"


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


def _source_domain(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    return parsed.netloc or None


def load_ipo_seed_companies() -> list[dict[str, Any]]:
    if not _IPO_SEED_PATH.exists():
        return []
    payload = json.loads(_IPO_SEED_PATH.read_text(encoding="utf-8"))
    items = payload.get("items") or []
    return [normalize_ipo_company(item) for item in items if isinstance(item, dict)]


async def fetch_ipo_company_data(seed_record: dict[str, Any]) -> dict[str, Any]:
    source_items = list(seed_record.get("source_items") or [])
    source_names = [source.get("source_name") for source in source_items if isinstance(source, dict) and source.get("source_name")]
    return {
        "company_name": seed_record.get("company_name"),
        "filing_status": seed_record.get("filing_status") or seed_record.get("status_label"),
        "proposed_exchange": seed_record.get("proposed_exchange") or seed_record.get("exchange"),
        "expected_window": seed_record.get("expected_window"),
        "filing_url": (seed_record.get("snapshot") or {}).get("filing_url"),
        "source_count": len(source_items),
        "source_names": source_names,
        "official_source_url": next(
            (
                source.get("source_url")
                for source in source_items
                if isinstance(source, dict) and source.get("is_official") and source.get("source_url")
            ),
            None,
        ),
        "seed_notes": ((seed_record.get("metadata_payload") or {}).get("seed_notes")),
        "fetched_from_seed": True,
    }


def build_ipo_snapshot(seed_record: dict[str, Any], fetched_data: dict[str, Any]) -> dict[str, Any]:
    now = _utc_now()
    stale_after = now + timedelta(seconds=STALE_THRESHOLD_SECONDS[ENTITY_TYPE_IPO_WATCH])

    normalized_seed = normalize_ipo_company(seed_record)
    source_items = list(normalized_seed.get("source_items") or [])
    filing_status = _string(fetched_data.get("filing_status")) or normalized_seed.get("filing_status")
    proposed_exchange = _string(fetched_data.get("proposed_exchange")) or normalized_seed.get("proposed_exchange")
    expected_window = _string(fetched_data.get("expected_window")) or normalized_seed.get("expected_window")
    filing_url = _string(fetched_data.get("filing_url")) or (normalized_seed.get("snapshot") or {}).get("filing_url")

    metrics_payload = {
        "freshness_days": 0.0,
        "source_count": len(source_items),
        "source_evidence_count": len([source for source in source_items if source.get("source_url")]),
    }

    company_payload = {
        **normalized_seed,
        "exchange": proposed_exchange,
        "status_label": filing_status or normalized_seed.get("status_label"),
        "short_summary": normalized_seed.get("short_summary"),
        "metrics": metrics_payload,
        "snapshot": {
            "filing_status": filing_status,
            "expected_window": expected_window,
            "proposed_exchange": proposed_exchange,
            "filing_url": filing_url,
            "snapshot_at": now.isoformat(),
            "stale_after_at": stale_after.isoformat(),
            "analysis_summary": normalized_seed.get("short_summary"),
            "source_names": fetched_data.get("source_names") or [],
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
        "filing_status": filing_status,
        "expected_window": expected_window,
        "proposed_exchange": proposed_exchange,
        "filing_url": filing_url,
        "official_source_url": fetched_data.get("official_source_url"),
        "source_names": fetched_data.get("source_names") or [],
        "seed_notes": fetched_data.get("seed_notes"),
        "fetched_from_seed": True,
    }

    verification = verify_ipo_company(
        company_payload,
        {
            "filing_status": filing_status,
            "status": filing_status,
            "filing_url": filing_url,
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
            "filing_status": filing_status,
            "status": filing_status,
            "filing_url": filing_url,
            "data_payload": snapshot_payload,
            "metrics_payload": metrics_payload,
            "completeness_score": company_payload["data_completeness_score"],
        },
        source_items,
    )

    return {
        "company": company_payload,
        "snapshot": {
            "snapshot_kind": "ipo_watch_refresh",
            "snapshot_label": f"{company_payload['slug']} ipo snapshot",
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
    return age_seconds >= STALE_THRESHOLD_SECONDS[ENTITY_TYPE_IPO_WATCH]


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
        "snapshot": payload.get("snapshot") or {},
        "verification": payload.get("verification") or {},
        "ranking": payload.get("ranking") or {},
    }


async def _refresh_ipo_companies(db: AsyncSession, force_refresh: bool = False) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seed_records = load_ipo_seed_companies()

    for seed_record in seed_records:
        existing_company = (
            await db.execute(
                select(StartupCompany).where(StartupCompany.slug == seed_record["slug"])
            )
        ).scalars().first()

        if not force_refresh and not _is_company_stale(existing_company):
            results.append({"slug": seed_record["slug"], "status": "fresh"})
            continue

        fetched_data = await fetch_ipo_company_data(seed_record)
        bundle = build_ipo_snapshot(seed_record, fetched_data)
        bundle["company"]["verification"] = bundle["verification"]
        bundle["company"]["ranking"] = bundle["ranking"]

        company = existing_company or StartupCompany(
            slug=bundle["company"]["slug"],
            company_name=bundle["company"]["company_name"],
            entity_type=ENTITY_TYPE_IPO_WATCH,
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


async def refresh_ipo_companies(
    db: AsyncSession | None = None,
    force_refresh: bool = False,
) -> list[dict[str, Any]]:
    if db is not None:
        return await _refresh_ipo_companies(db, force_refresh=force_refresh)

    async with async_session() as session:
        return await _refresh_ipo_companies(session, force_refresh=force_refresh)
