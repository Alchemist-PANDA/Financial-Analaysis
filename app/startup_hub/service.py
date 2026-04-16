"""Startup Hub service layer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.startup_hub.cache import (
    build_cache_key,
    get_cached_payload,
    set_cached_payload,
)
from app.startup_hub.agent import (
    build_agent_summary,
    build_compare_narrative,
    parse_agent_query,
    retrieve_matching_companies,
)
from app.startup_hub.constants import (
    DEFAULT_AGENT_MATCH_LIMIT,
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    ENTITY_TYPE_IPO_WATCH,
    ENTITY_TYPE_PRIVATE_OPPORTUNITY,
    ENTITY_TYPE_PUBLIC_STOCK,
    PLACEHOLDER_LAST_UPDATED,
    STALE_THRESHOLD_SECONDS,
    STARTUP_HUB_DISCLAIMERS,
    VERIFICATION_LEVEL_PARTIAL,
    VERIFICATION_LEVEL_UNVERIFIED,
)
from app.startup_hub.ipo_fetcher import refresh_ipo_companies
from app.startup_hub.models import StartupAgentLog, StartupCompany, StartupCompanySnapshot, StartupSource
from app.startup_hub.public_fetcher import refresh_public_companies
from app.startup_hub.private_fetcher import refresh_private_opportunities
from app.startup_hub.schemas import (
    StartupAgentQueryRequest,
    StartupAgentQueryResponse,
    StartupCompanyDetailResponse,
    StartupCompanyListItem,
    StartupCompareResponse,
    StartupHubHomeResponse,
    StartupHubLinkItem,
    StartupMetricItem,
    StartupRankingBreakdown,
    StartupSourceItem,
)
from app.startup_hub.verification import get_verification_badge_meta, verify_public_company


def _placeholder_timestamp() -> datetime:
    return datetime.fromisoformat(PLACEHOLDER_LAST_UPDATED.replace("Z", "+00:00"))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


PRIVATE_OPPORTUNITY_DISCLAIMERS = [
    "Not tradable on this platform.",
    "Research only.",
    "Verify eligibility and terms on official source.",
]

AGENT_DISCLAIMERS = [
    "Research only.",
    "Not investment advice.",
    "Results are grounded in stored Startup Hub scores and source metadata.",
    "No personalized investment advice or eligibility determination is provided.",
]

CACHE_SOURCE_LIVE = "live"
CACHE_SOURCE_CACHE = "cache"
CACHE_SOURCE_STALE_FALLBACK = "stale_cache_fallback"


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


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=_placeholder_timestamp().tzinfo)
    return value


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return _as_utc(value)
    text = _string(value)
    if not text:
        return None
    try:
        return _as_utc(datetime.fromisoformat(text.replace("Z", "+00:00")))
    except ValueError:
        return None


def _humanize_seconds(value: int | float) -> str:
    seconds = max(int(value), 0)
    if seconds < 60:
        return f"{seconds} seconds"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minutes"
    hours = minutes // 60
    if hours < 48:
        return f"{hours} hours"
    days = hours // 24
    return f"{days} days"


def _build_cache_status(cache_key: str, source: str, ttl_seconds: int | float, age_seconds: int | float, is_stale: bool) -> dict[str, Any]:
    return {
        "key": cache_key,
        "source": source,
        "ttl_seconds": float(ttl_seconds),
        "age_seconds": round(float(age_seconds), 2),
        "is_stale": bool(is_stale),
    }


def _attach_response_state(
    payload: dict[str, Any],
    *,
    threshold_seconds: int | float,
    cache_status: dict[str, Any],
    fallback_message: str | None = None,
) -> dict[str, Any]:
    response = dict(payload or {})
    last_updated = _parse_datetime(response.get("last_updated"))
    stale = False
    stale_message = None

    if last_updated is not None:
        age_seconds = max((_utc_now() - last_updated).total_seconds(), 0.0)
        if age_seconds >= float(threshold_seconds):
            stale = True
            stale_message = (
                f"Underlying data is { _humanize_seconds(age_seconds) } old, beyond the expected "
                f"{ _humanize_seconds(threshold_seconds) } freshness window."
            )

    if cache_status.get("source") == CACHE_SOURCE_STALE_FALLBACK:
        stale = True
        stale_message = fallback_message or "Showing a stale cached response because a fresh refresh was unavailable."

    response["stale"] = stale
    response["stale_message"] = stale_message
    response["cache_status"] = cache_status
    return response


async def _run_cached_response(
    *,
    cache_key: str,
    ttl_seconds: int | float,
    threshold_seconds: int | float,
    compute,
    fallback_message: str,
) -> dict[str, Any]:
    cached_entry = get_cached_payload(cache_key, allow_stale=True)
    if cached_entry is not None and not cached_entry["is_stale"]:
        return _attach_response_state(
            dict(cached_entry["payload"] or {}),
            threshold_seconds=threshold_seconds,
            cache_status=_build_cache_status(
                cache_key,
                CACHE_SOURCE_CACHE,
                cached_entry["ttl_seconds"],
                cached_entry["age_seconds"],
                False,
            ),
        )

    try:
        payload = await compute()
        set_cached_payload(cache_key, payload, ttl_seconds)
        return _attach_response_state(
            dict(payload or {}),
            threshold_seconds=threshold_seconds,
            cache_status=_build_cache_status(cache_key, CACHE_SOURCE_LIVE, ttl_seconds, 0.0, False),
        )
    except Exception:
        if cached_entry is not None:
            return _attach_response_state(
                dict(cached_entry["payload"] or {}),
                threshold_seconds=threshold_seconds,
                cache_status=_build_cache_status(
                    cache_key,
                    CACHE_SOURCE_STALE_FALLBACK,
                    cached_entry["ttl_seconds"],
                    cached_entry["age_seconds"],
                    True,
                ),
                fallback_message=fallback_message,
            )
        raise


def _route_links() -> list[StartupHubLinkItem]:
    return [
        StartupHubLinkItem(label="Startup Hub", href="/startup-hub"),
        StartupHubLinkItem(label="Startup Stocks", href="/startup-hub/stocks"),
        StartupHubLinkItem(label="IPO Watch", href="/startup-hub/ipos"),
        StartupHubLinkItem(label="Private Opportunities", href="/startup-hub/private"),
    ]


def _placeholder_ranking(explanation: str) -> StartupRankingBreakdown:
    return StartupRankingBreakdown(
        explanation=explanation,
        top_drivers=["Scaffolded data contract only"],
        red_flags=["No deterministic ranking logic yet"],
    )


def _placeholder_item(
    slug: str,
    company_name: str,
    entity_type: str,
    verification_level: str,
    short_summary: str,
    *,
    ticker: str | None = None,
    exchange: str | None = None,
    sector: str | None = None,
    stage: str | None = None,
    status_label: str | None = None,
) -> StartupCompanyListItem:
    return StartupCompanyListItem(
        slug=slug,
        company_name=company_name,
        entity_type=entity_type,
        ticker=ticker,
        exchange=exchange,
        sector=sector,
        stage=stage,
        status_label=status_label,
        short_summary=short_summary,
        verification_level=verification_level,
        ranking=_placeholder_ranking("Ranking fields are present but not computed in Phase 2."),
        source_count=1 if verification_level != VERIFICATION_LEVEL_UNVERIFIED else 0,
        data_completeness_score=0.2 if verification_level == VERIFICATION_LEVEL_UNVERIFIED else 0.35,
        research_only=True,
        last_updated=_placeholder_timestamp(),
    )


async def _with_session(callback, db: AsyncSession | None):
    if db is not None:
        return await callback(db)
    async with async_session() as session:
        return await callback(session)


async def _latest_snapshot(db: AsyncSession, company_id: int) -> StartupCompanySnapshot | None:
    return (
        await db.execute(
            select(StartupCompanySnapshot)
            .where(StartupCompanySnapshot.company_id == company_id)
            .order_by(StartupCompanySnapshot.created_at.desc())
            .limit(1)
        )
    ).scalars().first()


async def _sources_for_company(
    db: AsyncSession,
    company_id: int,
    snapshot_id: int | None,
) -> list[StartupSource]:
    query = select(StartupSource).where(StartupSource.company_id == company_id)
    if snapshot_id is not None:
        query = query.where(StartupSource.snapshot_id == snapshot_id)
    query = query.order_by(StartupSource.is_official.desc(), StartupSource.created_at.desc())
    return list((await db.execute(query)).scalars().all())


def _last_updated(company: StartupCompany, snapshot: StartupCompanySnapshot | None) -> datetime | None:
    if snapshot and snapshot.snapshot_at:
        return _as_utc(snapshot.snapshot_at)
    return _as_utc(company.latest_snapshot_at)


def _ranking_from_snapshot(snapshot: StartupCompanySnapshot | None) -> StartupRankingBreakdown:
    payload = dict(snapshot.ranking_payload or {}) if snapshot else {}
    return StartupRankingBreakdown(**payload)


def _source_items_from_models(sources: list[StartupSource]) -> list[StartupSourceItem]:
    items: list[StartupSourceItem] = []
    for source in sources:
        items.append(
            StartupSourceItem(
                source_name=source.source_name,
                source_type=source.source_type,
                source_url=source.source_url,
                is_official=source.is_official,
                verification_level=source.verification_level,
                published_at=source.published_at,
                last_checked_at=source.last_checked_at,
                notes=(source.metadata_payload or {}).get("notes") if isinstance(source.metadata_payload, dict) else None,
            )
        )
    return items


def _format_metric_value(value: Any, *, suffix: str = "", decimals: int = 1) -> str:
    numeric = _safe_float(value)
    if numeric is not None:
        formatted = f"{numeric:.{decimals}f}"
        if suffix:
            return f"{formatted}{suffix}"
        return formatted

    text = _string(value)
    return text or "—"


def _build_metric_highlights(metrics_payload: dict[str, Any]) -> list[StartupMetricItem]:
    metric_specs = [
        ("revenue_cagr_pct", "Revenue CAGR", "%", 1, "Multi-year revenue trajectory."),
        ("revenue_growth_pct", "Recent Revenue Growth", "%", 1, "Latest reported growth rate."),
        ("current_roe", "Return On Equity", "%", 1, "Current profitability against equity."),
        ("current_fcf_conversion_pct", "FCF Conversion", "%", 1, "Cash conversion from earnings."),
        ("current_z_score", "Altman Z-Score", "", 2, "Balance-sheet distress indicator."),
        ("ebitda_margin_pct", "EBITDA Margin", "%", 1, "Operating efficiency before non-cash charges."),
        ("health_score", "Health Score", "", 0, "Deterministic scorecard output."),
        ("health_band", "Health Band", "", 0, "Scorecard classification."),
        ("margin_signal", "Margin Signal", "", 0, "Rule-based margin trend label."),
        ("solvency_signal", "Solvency Signal", "", 0, "Rule-based solvency trend label."),
        ("current_dso", "Days Sales Outstanding", " days", 1, "Working-capital collection signal."),
        ("current_inventory_turnover", "Inventory Turnover", "x", 2, "Inventory efficiency signal."),
    ]

    highlights: list[StartupMetricItem] = []
    for key, label, suffix, decimals, context in metric_specs:
        raw_value = metrics_payload.get(key)
        formatted_value = _format_metric_value(raw_value, suffix=suffix, decimals=decimals)
        if key == "health_score" and formatted_value != "—":
            formatted_value = f"{formatted_value}/100"
        highlights.append(
            StartupMetricItem(
                key=key,
                label=label,
                value=raw_value,
                formatted_value=formatted_value,
                context=context,
            )
        )
    return highlights


def _analysis_flag_texts(data_payload: dict[str, Any], emoji: str) -> list[str]:
    flags = (data_payload.get("analysis") or {}).get("flags") or []
    texts: list[str] = []
    for flag in flags:
        if not isinstance(flag, dict) or flag.get("emoji") != emoji:
            continue
        explanation = _string(flag.get("explanation"))
        if explanation:
            texts.append(explanation)
    return texts


def _dedupe_texts(*groups: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for item in group:
            text = _string(item)
            if not text:
                continue
            normalized = text.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(text)
    return deduped


def _company_item_from_records(
    company: StartupCompany,
    snapshot: StartupCompanySnapshot | None,
    sources: list[StartupSource],
) -> StartupCompanyListItem:
    summary = company.summary_text
    if not summary and snapshot and isinstance(snapshot.data_payload, dict):
        summary = snapshot.data_payload.get("analysis_summary")
    return StartupCompanyListItem(
        slug=company.slug,
        company_name=company.company_name,
        entity_type=company.entity_type,
        sector=company.sector,
        ticker=company.ticker,
        exchange=company.exchange,
        stage=company.stage,
        status_label=company.status_label,
        short_summary=summary,
        verification_level=company.verification_level,
        ranking=_ranking_from_snapshot(snapshot),
        source_count=len(sources) or company.source_count,
        data_completeness_score=company.data_completeness_score,
        research_only=company.research_only,
        last_updated=_last_updated(company, snapshot),
    )


async def _public_companies_from_db(db: AsyncSession) -> list[tuple[StartupCompany, StartupCompanySnapshot | None, list[StartupSource]]]:
    return await _companies_from_db(db, ENTITY_TYPE_PUBLIC_STOCK)


async def _companies_from_db(
    db: AsyncSession,
    entity_type: str,
) -> list[tuple[StartupCompany, StartupCompanySnapshot | None, list[StartupSource]]]:
    companies = list(
        (
            await db.execute(
                select(StartupCompany)
                .where(StartupCompany.entity_type == entity_type)
                .order_by(StartupCompany.company_name.asc())
            )
        ).scalars().all()
    )

    bundles: list[tuple[StartupCompany, StartupCompanySnapshot | None, list[StartupSource]]] = []
    for company in companies:
        snapshot = await _latest_snapshot(db, company.id)
        sources = await _sources_for_company(db, company.id, snapshot.id if snapshot else None)
        bundles.append((company, snapshot, sources))
    return bundles


async def _ensure_public_data(db: AsyncSession) -> list[tuple[StartupCompany, StartupCompanySnapshot | None, list[StartupSource]]]:
    await refresh_public_companies(db=db, force_refresh=False)
    return await _public_companies_from_db(db)


async def _ensure_ipo_data(db: AsyncSession) -> list[tuple[StartupCompany, StartupCompanySnapshot | None, list[StartupSource]]]:
    await refresh_ipo_companies(db=db, force_refresh=False)
    return await _companies_from_db(db, ENTITY_TYPE_IPO_WATCH)


async def _ensure_private_data(db: AsyncSession) -> list[tuple[StartupCompany, StartupCompanySnapshot | None, list[StartupSource]]]:
    await refresh_private_opportunities(db=db, force_refresh=False)
    return await _companies_from_db(db, ENTITY_TYPE_PRIVATE_OPPORTUNITY)


def _primary_source(sources: list[StartupSource]) -> StartupSource | None:
    if not sources:
        return None
    for source in sources:
        if source.is_official:
            return source
    return sources[0]


def _ipo_item_payload(
    company: StartupCompany,
    snapshot: StartupCompanySnapshot | None,
    sources: list[StartupSource],
) -> dict[str, Any]:
    item = _company_item_from_records(company, snapshot, sources)
    data_payload = dict(snapshot.data_payload or {}) if snapshot else {}
    primary_source = _primary_source(sources)
    return {
        **item.model_dump(),
        "filing_status": _string(data_payload.get("filing_status")) or company.status_label,
        "proposed_exchange": _string(data_payload.get("proposed_exchange")) or company.exchange,
        "expected_window": _string(data_payload.get("expected_window")),
        "filing_freshness_label": _string(data_payload.get("filing_freshness_label")),
        "official_source_url": (
            primary_source.source_url
            if primary_source and primary_source.source_url
            else _string(data_payload.get("official_source_url") or data_payload.get("filing_url"))
        ),
        "source_name": primary_source.source_name if primary_source else None,
        "source_is_official": bool(primary_source.is_official) if primary_source else False,
        "risk_snippet": item.ranking.red_flags[0] if item.ranking.red_flags else None,
    }


def _private_item_payload(
    company: StartupCompany,
    snapshot: StartupCompanySnapshot | None,
    sources: list[StartupSource],
) -> dict[str, Any]:
    item = _company_item_from_records(company, snapshot, sources)
    data_payload = dict(snapshot.data_payload or {}) if snapshot else {}
    metrics_payload = dict(snapshot.metrics_payload or {}) if snapshot else {}
    primary_source = _primary_source(sources)
    official_source_url = (
        primary_source.source_url
        if primary_source and primary_source.source_url
        else _string(data_payload.get("official_source_url"))
    )
    return {
        **item.model_dump(),
        "valuation_usd": _safe_float(data_payload.get("valuation_usd") or metrics_payload.get("valuation_usd")),
        "minimum_investment_usd": _safe_float(
            data_payload.get("minimum_investment_usd") or metrics_payload.get("minimum_investment_usd")
        ),
        "official_source_url": official_source_url,
        "source_name": (
            primary_source.source_name
            if primary_source
            else _string(data_payload.get("source_name"))
        ),
        "source_is_official": bool(primary_source.is_official) if primary_source else False,
        "verification": get_verification_badge_meta(company.verification_level),
        "research_only_label": "Research only",
        "platform_availability_note": "Not tradable on this platform.",
        "eligibility_note": "Verify eligibility and terms on official source.",
        "risk_snippet": item.ranking.red_flags[0] if item.ranking.red_flags else None,
    }


def _agent_candidate_payload(
    company: StartupCompany,
    snapshot: StartupCompanySnapshot | None,
    sources: list[StartupSource],
) -> dict[str, Any]:
    item = _company_item_from_records(company, snapshot, sources)
    return {
        "company": item.model_dump(),
        "data_payload": dict(snapshot.data_payload or {}) if snapshot else {},
        "metrics_payload": dict(snapshot.metrics_payload or {}) if snapshot else {},
        "source_count": len(sources),
    }


async def _get_public_company_bundle(
    db: AsyncSession,
    slug: str,
) -> tuple[StartupCompany, StartupCompanySnapshot | None, list[StartupSource]] | None:
    company = (
        await db.execute(
            select(StartupCompany)
            .where(StartupCompany.entity_type == ENTITY_TYPE_PUBLIC_STOCK)
            .where(StartupCompany.slug == slug)
            .limit(1)
        )
    ).scalars().first()
    if not company:
        return None
    snapshot = await _latest_snapshot(db, company.id)
    sources = await _sources_for_company(db, company.id, snapshot.id if snapshot else None)
    return company, snapshot, sources


async def get_home_payload(db: AsyncSession | None = None) -> dict:
    async def _run(session: AsyncSession) -> dict:
        cache_key = build_cache_key("startup_hub_home")

        async def _compute() -> dict:
            public_bundles = await _ensure_public_data(session)
            public_items = [
                _company_item_from_records(company, snapshot, sources)
                for company, snapshot, sources in public_bundles
            ]
            public_items.sort(key=lambda item: item.ranking.total_score, reverse=True)

            ipo_bundles = await _ensure_ipo_data(session)
            ipo_items = [
                _company_item_from_records(company, snapshot, sources)
                for company, snapshot, sources in ipo_bundles
            ]
            ipo_items.sort(key=lambda item: item.ranking.total_score, reverse=True)

            private_bundles = await _ensure_private_data(session)
            private_items = [
                _company_item_from_records(company, snapshot, sources)
                for company, snapshot, sources in private_bundles
            ]
            private_items.sort(key=lambda item: item.ranking.total_score, reverse=True)

            last_updated = max(
                (item.last_updated for item in [*public_items, *ipo_items, *private_items] if item.last_updated),
                default=None,
            )
            return StartupHubHomeResponse(
                status="ready",
                disclaimer=STARTUP_HUB_DISCLAIMERS,
                routes=_route_links(),
                featured=public_items[:3],
                public_companies=public_items,
                ipo_preview=ipo_items[:3],
                private_preview=private_items[:3],
                counts={
                    "featured": len(public_items[:3]),
                    "public_companies": len(public_items),
                    "ipo_preview": len(ipo_items[:3]),
                    "private_preview": len(private_items[:3]),
                },
                last_updated=last_updated,
            ).model_dump(mode="json")

        return await _run_cached_response(
            cache_key=cache_key,
            ttl_seconds=STALE_THRESHOLD_SECONDS["home_payload"],
            threshold_seconds=STALE_THRESHOLD_SECONDS["home_payload"],
            compute=_compute,
            fallback_message="Showing a cached Startup Hub home payload because a fresh refresh was unavailable.",
        )

    return await _with_session(_run, db)


async def list_companies(filters: dict | None = None, db: AsyncSession | None = None) -> dict:
    active_filters = dict(filters or {})

    async def _run(session: AsyncSession) -> dict:
        cache_key = build_cache_key(
            "startup_hub_company_list",
            entity_type=active_filters.get("entity_type") or ENTITY_TYPE_PUBLIC_STOCK,
            search=_string(active_filters.get("search")) or "",
        )

        async def _compute() -> dict:
            requested_type = active_filters.get("entity_type")
            if requested_type and requested_type != ENTITY_TYPE_PUBLIC_STOCK:
                return {
                    "feature": "startup_hub_companies",
                    "status": "ready",
                    "enabled": False,
                    "disclaimer": STARTUP_HUB_DISCLAIMERS,
                    "filters": active_filters,
                    "items": [],
                    "pagination": {"page": DEFAULT_PAGE, "page_size": DEFAULT_PAGE_SIZE, "total": 0},
                    "last_updated": None,
                }

            bundles = await _ensure_public_data(session)
            items = [
                _company_item_from_records(company, snapshot, sources)
                for company, snapshot, sources in bundles
            ]

            search = str(active_filters.get("search") or "").strip().lower()
            if search:
                items = [
                    item
                    for item in items
                    if search in item.company_name.lower()
                    or search in (item.ticker or "").lower()
                    or search in (item.sector or "").lower()
                ]

            items.sort(key=lambda item: item.ranking.total_score, reverse=True)
            last_updated = max((item.last_updated for item in items if item.last_updated), default=None)
            return {
                "feature": "startup_hub_companies",
                "status": "ready",
                "enabled": False,
                "disclaimer": STARTUP_HUB_DISCLAIMERS,
                "filters": {**active_filters, "entity_type": ENTITY_TYPE_PUBLIC_STOCK},
                "items": [item.model_dump(mode="json") for item in items],
                "pagination": {"page": DEFAULT_PAGE, "page_size": DEFAULT_PAGE_SIZE, "total": len(items)},
                "last_updated": last_updated,
            }

        return await _run_cached_response(
            cache_key=cache_key,
            ttl_seconds=STALE_THRESHOLD_SECONDS["company_list"],
            threshold_seconds=STALE_THRESHOLD_SECONDS[ENTITY_TYPE_PUBLIC_STOCK],
            compute=_compute,
            fallback_message="Showing a cached company list because a fresh public-stock refresh was unavailable.",
        )

    return await _with_session(_run, db)


async def get_company_detail(slug: str, db: AsyncSession | None = None) -> dict:
    async def _run(session: AsyncSession) -> dict:
        cache_key = build_cache_key("startup_hub_company_detail", slug=slug)

        async def _compute() -> dict:
            await refresh_public_companies(db=session, force_refresh=False)
            company = (
                await session.execute(
                    select(StartupCompany)
                    .where(StartupCompany.entity_type == ENTITY_TYPE_PUBLIC_STOCK)
                    .where(StartupCompany.slug == slug)
                    .limit(1)
                )
            ).scalars().first()
            if not company:
                raise LookupError(slug)

            snapshot = await _latest_snapshot(session, company.id)
            sources = await _sources_for_company(session, company.id, snapshot.id if snapshot else None)
            company_item = _company_item_from_records(company, snapshot, sources)
            source_items = _source_items_from_models(sources)

            metrics_payload = dict(snapshot.metrics_payload or {}) if snapshot else {}
            data_payload = dict(snapshot.data_payload or {}) if snapshot else {}
            verification_result = verify_public_company(company, snapshot, sources)
            metrics_payload["verification"] = verification_result
            analysis_payload = dict(data_payload.get("analysis") or {})
            description = (
                _string(company.summary_text)
                or _string(data_payload.get("analysis_summary"))
                or _string(analysis_payload.get("analyst_verdict_summary"))
            )
            thesis_summary = (
                _string(analysis_payload.get("retail_verdict"))
                or description
                or "Deterministic thesis summary is not available yet."
            )
            strengths = _dedupe_texts(
                list(company_item.ranking.top_drivers),
                _analysis_flag_texts(data_payload, "+"),
            )
            risks = _dedupe_texts(
                list(company_item.ranking.red_flags),
                _analysis_flag_texts(data_payload, "!"),
                [_string(data_payload.get("fetch_error")) or ""],
            )
            return StartupCompanyDetailResponse(
                status="ready",
                disclaimer=STARTUP_HUB_DISCLAIMERS,
                company=company_item,
                verification=verification_result,
                thesis_summary=thesis_summary,
                long_summary=(data_payload.get("analysis") or {}).get("pattern_diagnosis"),
                description=description,
                strengths=strengths,
                risks=risks,
                metrics=metrics_payload,
                metric_highlights=_build_metric_highlights(metrics_payload),
                snapshot=data_payload,
                sources=source_items,
                last_updated=_last_updated(company, snapshot),
            ).model_dump(mode="json")

        return await _run_cached_response(
            cache_key=cache_key,
            ttl_seconds=STALE_THRESHOLD_SECONDS["company_detail"],
            threshold_seconds=STALE_THRESHOLD_SECONDS[ENTITY_TYPE_PUBLIC_STOCK],
            compute=_compute,
            fallback_message=f"Showing cached detail for {slug} because a fresh public-stock refresh was unavailable.",
        )

    return await _with_session(_run, db)


async def get_company_ranking(slug: str, db: AsyncSession | None = None) -> dict:
    async def _run(session: AsyncSession) -> dict:
        cache_key = build_cache_key("startup_hub_company_ranking", slug=slug)

        async def _compute() -> dict:
            await refresh_public_companies(db=session, force_refresh=False)
            company = (
                await session.execute(
                    select(StartupCompany)
                    .where(StartupCompany.entity_type == ENTITY_TYPE_PUBLIC_STOCK)
                    .where(StartupCompany.slug == slug)
                    .limit(1)
                )
            ).scalars().first()
            if not company:
                raise LookupError(slug)

            snapshot = await _latest_snapshot(session, company.id)
            ranking = dict(snapshot.ranking_payload or {}) if snapshot else {}
            return {
                "feature": "startup_hub_company_ranking",
                "status": "ready",
                "enabled": False,
                "disclaimer": STARTUP_HUB_DISCLAIMERS,
                "company": {
                    "slug": company.slug,
                    "company_name": company.company_name,
                    "ticker": company.ticker,
                    "verification_level": company.verification_level,
                    "last_updated": _last_updated(company, snapshot),
                },
                "ranking": ranking,
                "verification": get_verification_badge_meta(company.verification_level),
                "summary": company.summary_text,
                "last_updated": _last_updated(company, snapshot),
            }

        return await _run_cached_response(
            cache_key=cache_key,
            ttl_seconds=STALE_THRESHOLD_SECONDS["company_detail"],
            threshold_seconds=STALE_THRESHOLD_SECONDS[ENTITY_TYPE_PUBLIC_STOCK],
            compute=_compute,
            fallback_message=f"Showing cached ranking for {slug} because a fresh public-stock refresh was unavailable.",
        )

    return await _with_session(_run, db)


async def compare_companies(
    left: str,
    right: str,
    db: AsyncSession | None = None,
) -> dict:
    async def _run(session: AsyncSession) -> dict:
        cache_key = build_cache_key("startup_hub_compare", left=left, right=right)

        async def _compute() -> dict:
            await refresh_public_companies(db=session, force_refresh=False)

            left_bundle = await _get_public_company_bundle(session, left)
            right_bundle = await _get_public_company_bundle(session, right)
            if left_bundle is None:
                raise LookupError(left)
            if right_bundle is None:
                raise LookupError(right)

            left_company, left_snapshot, left_sources = left_bundle
            right_company, right_snapshot, right_sources = right_bundle

            left_item = _company_item_from_records(left_company, left_snapshot, left_sources)
            right_item = _company_item_from_records(right_company, right_snapshot, right_sources)
            left_candidate = _agent_candidate_payload(left_company, left_snapshot, left_sources)
            right_candidate = _agent_candidate_payload(right_company, right_snapshot, right_sources)

            comparison = build_compare_narrative(left_candidate, right_candidate)
            left_ranking = left_item.ranking
            right_ranking = right_item.ranking

            transparency_left = (left_item.data_completeness_score * 100.0) + min(left_item.source_count, 5) * 5.0
            transparency_right = (right_item.data_completeness_score * 100.0) + min(right_item.source_count, 5) * 5.0

            def winner(left_value: float, right_value: float, *, higher_is_better: bool = True) -> str:
                if left_value == right_value:
                    return "tie"
                if higher_is_better:
                    return left_item.company_name if left_value > right_value else right_item.company_name
                return left_item.company_name if left_value < right_value else right_item.company_name

            category_winners = {
                "growth": winner(left_ranking.growth_score, right_ranking.growth_score),
                "quality": winner(left_ranking.quality_score, right_ranking.quality_score),
                "risk": winner(left_ranking.risk_score, right_ranking.risk_score),
                "momentum": winner(left_ranking.momentum_score, right_ranking.momentum_score),
                "verification": winner(left_ranking.verification_score, right_ranking.verification_score),
                "transparency": winner(transparency_left, transparency_right),
            }

            if left_ranking.total_score > right_ranking.total_score:
                leading_company = left_item.company_name
                overall_summary = (
                    f"{leading_company} leads on the current Startup Hub comparison because it has the stronger stored total score "
                    f"and wins more deterministic comparison categories."
                )
            elif right_ranking.total_score > left_ranking.total_score:
                leading_company = right_item.company_name
                overall_summary = (
                    f"{leading_company} leads on the current Startup Hub comparison because it has the stronger stored total score "
                    f"and wins more deterministic comparison categories."
                )
            else:
                overall_summary = (
                    f"{left_item.company_name} and {right_item.company_name} are tied on total score, so the comparison turns on category-level differences and disclosure quality."
                )

            comparison_notes = list(comparison.get("notes") or [])
            if left_item.ranking.top_drivers:
                comparison_notes.append(f"{left_item.company_name}: {left_item.ranking.top_drivers[0]}")
            if right_item.ranking.top_drivers:
                comparison_notes.append(f"{right_item.company_name}: {right_item.ranking.top_drivers[0]}")
            comparison_notes = comparison_notes[:4]

            ai_explanation = (
                f"{comparison.get('summary')} "
                f"{left_item.company_name} scores {left_ranking.total_score:.1f} versus {right_item.company_name} at {right_ranking.total_score:.1f}. "
                f"Category winners are derived from stored growth, quality, risk, momentum, verification, and transparency fields only."
            )

            last_updated = max(
                value
                for value in [left_item.last_updated, right_item.last_updated, _placeholder_timestamp()]
                if value is not None
            )

            return StartupCompareResponse(
                status="ready",
                disclaimer=STARTUP_HUB_DISCLAIMERS,
                left=left_item,
                right=right_item,
                left_summary=left_item.short_summary,
                right_summary=right_item.short_summary,
                category_winners=category_winners,
                overall_summary=overall_summary,
                ai_explanation=ai_explanation,
                comparison_notes=comparison_notes,
                last_updated=last_updated,
            ).model_dump(mode="json")

        return await _run_cached_response(
            cache_key=cache_key,
            ttl_seconds=STALE_THRESHOLD_SECONDS["company_detail"],
            threshold_seconds=STALE_THRESHOLD_SECONDS[ENTITY_TYPE_PUBLIC_STOCK],
            compute=_compute,
            fallback_message="Showing a cached comparison because a fresh public-stock refresh was unavailable.",
        )

    return await _with_session(_run, db)


async def list_ipos(db: AsyncSession | None = None) -> dict:
    async def _run(session: AsyncSession) -> dict:
        cache_key = build_cache_key("startup_hub_ipos")

        async def _compute() -> dict:
            bundles = await _ensure_ipo_data(session)
            items = [
                _ipo_item_payload(company, snapshot, sources)
                for company, snapshot, sources in bundles
            ]
            items.sort(key=lambda item: item["ranking"]["total_score"], reverse=True)
            last_updated = max(
                (
                    _last_updated(company, snapshot)
                    for company, snapshot, _ in bundles
                    if _last_updated(company, snapshot) is not None
                ),
                default=None,
            )
            return {
                "feature": "startup_hub_ipos",
                "status": "ready",
                "enabled": False,
                "disclaimer": STARTUP_HUB_DISCLAIMERS,
                "items": items,
                "pagination": {"page": DEFAULT_PAGE, "page_size": DEFAULT_PAGE_SIZE, "total": len(items)},
                "last_updated": last_updated,
            }

        return await _run_cached_response(
            cache_key=cache_key,
            ttl_seconds=STALE_THRESHOLD_SECONDS["company_list"],
            threshold_seconds=STALE_THRESHOLD_SECONDS[ENTITY_TYPE_IPO_WATCH],
            compute=_compute,
            fallback_message="Showing a cached IPO Watch list because a fresh IPO refresh was unavailable.",
        )

    return await _with_session(_run, db)


async def list_private_opportunities(db: AsyncSession | None = None) -> dict:
    async def _run(session: AsyncSession) -> dict:
        cache_key = build_cache_key("startup_hub_private")

        async def _compute() -> dict:
            bundles = await _ensure_private_data(session)
            items = [
                _private_item_payload(company, snapshot, sources)
                for company, snapshot, sources in bundles
            ]
            items.sort(key=lambda item: item["ranking"]["total_score"], reverse=True)
            last_updated = max(
                (
                    _last_updated(company, snapshot)
                    for company, snapshot, _ in bundles
                    if _last_updated(company, snapshot) is not None
                ),
                default=None,
            )
            return {
                "feature": "startup_hub_private",
                "status": "ready",
                "enabled": False,
                "disclaimer": PRIVATE_OPPORTUNITY_DISCLAIMERS,
                "items": items,
                "pagination": {"page": DEFAULT_PAGE, "page_size": DEFAULT_PAGE_SIZE, "total": len(items)},
                "last_updated": last_updated,
            }

        return await _run_cached_response(
            cache_key=cache_key,
            ttl_seconds=STALE_THRESHOLD_SECONDS["company_list"],
            threshold_seconds=STALE_THRESHOLD_SECONDS[ENTITY_TYPE_PRIVATE_OPPORTUNITY],
            compute=_compute,
            fallback_message="Showing a cached private-opportunities list because a fresh refresh was unavailable.",
        )

    return await _with_session(_run, db)


async def query_agent(
    payload: StartupAgentQueryRequest | dict[str, Any],
    db: AsyncSession | None = None,
) -> dict:
    request_payload = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload or {})
    query_text = _string(request_payload.get("query")) or ""
    requested_limit = int(request_payload.get("limit") or DEFAULT_AGENT_MATCH_LIMIT)
    include_explanations = bool(request_payload.get("include_explanations", True))

    async def _run(session: AsyncSession) -> dict:
        interpreted = parse_agent_query(query_text)
        explicit_entity_type = _string(request_payload.get("entity_type"))
        if explicit_entity_type:
            interpreted["entity_type"] = explicit_entity_type

        candidate_bundles: list[dict[str, Any]] = []
        entity_type = interpreted.get("entity_type")
        if entity_type in (None, ENTITY_TYPE_PUBLIC_STOCK):
            public_bundles = await _ensure_public_data(session)
            candidate_bundles.extend(
                _agent_candidate_payload(company, snapshot, sources)
                for company, snapshot, sources in public_bundles
            )
        if entity_type in (None, ENTITY_TYPE_IPO_WATCH):
            ipo_bundles = await _ensure_ipo_data(session)
            candidate_bundles.extend(
                _agent_candidate_payload(company, snapshot, sources)
                for company, snapshot, sources in ipo_bundles
            )
        if entity_type in (None, ENTITY_TYPE_PRIVATE_OPPORTUNITY):
            private_bundles = await _ensure_private_data(session)
            candidate_bundles.extend(
                _agent_candidate_payload(company, snapshot, sources)
                for company, snapshot, sources in private_bundles
            )

        effective_limit = max(requested_limit, 2) if interpreted.get("mode") == "compare" else requested_limit
        matches = retrieve_matching_companies(interpreted, effective_limit, companies=candidate_bundles)
        summary_payload = build_agent_summary(query_text, matches, interpreted)
        confidence_level = "low"
        if interpreted.get("mode") == "compare" and len(matches) >= 2:
            confidence_level = "high"
        elif matches and (interpreted.get("entity_type") or interpreted.get("sector")):
            confidence_level = "medium"
        elif matches:
            confidence_level = "medium" if len(matches) >= 2 else "low"

        reasoning_points = list(summary_payload.get("reasoning_points") or [])
        if not include_explanations:
            reasoning_points = []

        response_model = StartupAgentQueryResponse(
            status="ready",
            disclaimer=AGENT_DISCLAIMERS,
            query=query_text,
            mode=interpreted.get("mode") or "screen",
            interpreted_filters=interpreted,
            summary=_string(summary_payload.get("summary"))
            or "No deterministic agent summary was produced.",
            reasoning_points=reasoning_points,
            comparison=dict(summary_payload.get("comparison") or {}),
            matches=[StartupCompanyListItem(**candidate["company"]) for candidate in matches],
            confidence_level=confidence_level,
            last_updated=max(
                (
                    _parse_datetime(candidate["company"].get("last_updated"))
                    for candidate in matches
                    if _parse_datetime(candidate["company"].get("last_updated")) is not None
                ),
                default=_utc_now(),
            ),
        )
        response = response_model.model_dump(mode="json")

        log = StartupAgentLog(
            query_text=query_text,
            entity_type=interpreted.get("entity_type"),
            filters_payload=interpreted,
            response_payload=response,
            matched_company_slugs=[candidate["company"]["slug"] for candidate in matches],
            disclaimer_text=" | ".join(AGENT_DISCLAIMERS),
        )
        session.add(log)
        await session.commit()

        return response

    return await _with_session(_run, db)
