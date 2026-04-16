"""Verification rules for Startup Hub."""

from __future__ import annotations

from typing import Any

from app.startup_hub.constants import (
    VERIFICATION_LEVEL_PARTIAL,
    VERIFICATION_LEVEL_SOURCE_VERIFIED_PRIVATE,
    VERIFICATION_LEVEL_UNVERIFIED,
    VERIFICATION_LEVEL_VERIFIED_IPO,
    VERIFICATION_LEVEL_VERIFIED_PUBLIC,
)


def _read(source: Any, key: str, default: Any = None) -> Any:
    if source is None:
        return default
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalized_sources(sources: list[Any] | None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for source in list(sources or []):
        normalized.append(
            {
                "source_name": _string(_read(source, "source_name")),
                "source_type": _string(_read(source, "source_type")) or "reference",
                "source_url": _string(_read(source, "source_url")),
                "is_official": bool(_read(source, "is_official", False)),
            }
        )
    return normalized


def _has_source_evidence(sources: list[dict[str, Any]]) -> bool:
    return any(source.get("source_name") and source.get("source_url") for source in sources)


def _has_official_source_page(sources: list[dict[str, Any]], company: Any | None = None) -> bool:
    if any(source.get("is_official") and source.get("source_url") for source in sources):
        return True
    return bool(_string(_read(company, "official_source_url")) or _string(_read(company, "website_url")))


def _resolve_snapshot_value(snapshot: Any, *keys: str) -> Any:
    for key in keys:
        value = _read(snapshot, key)
        if value is not None:
            return value
        data_payload = _read(snapshot, "data_payload", {})
        if isinstance(data_payload, dict) and key in data_payload:
            return data_payload.get(key)
    return None


def get_verification_badge_meta(level: str) -> dict[str, str]:
    badge_map = {
        VERIFICATION_LEVEL_VERIFIED_PUBLIC: {
            "level": VERIFICATION_LEVEL_VERIFIED_PUBLIC,
            "label": "Verified Public",
            "tone": "success",
            "description": "Ticker and listing evidence are present.",
        },
        VERIFICATION_LEVEL_VERIFIED_IPO: {
            "level": VERIFICATION_LEVEL_VERIFIED_IPO,
            "label": "Verified IPO",
            "tone": "info",
            "description": "Status and filing or official source evidence are present.",
        },
        VERIFICATION_LEVEL_SOURCE_VERIFIED_PRIVATE: {
            "level": VERIFICATION_LEVEL_SOURCE_VERIFIED_PRIVATE,
            "label": "Source Verified Private",
            "tone": "info",
            "description": "Official source page and research-only classification are present.",
        },
        VERIFICATION_LEVEL_PARTIAL: {
            "level": VERIFICATION_LEVEL_PARTIAL,
            "label": "Partial",
            "tone": "warning",
            "description": "Some evidence exists, but key checks are still missing.",
        },
        VERIFICATION_LEVEL_UNVERIFIED: {
            "level": VERIFICATION_LEVEL_UNVERIFIED,
            "label": "Unverified",
            "tone": "neutral",
            "description": "The record is missing the evidence needed for verification.",
        },
    }
    return badge_map.get(level, badge_map[VERIFICATION_LEVEL_UNVERIFIED]).copy()


def verify_public_company(company: Any, snapshot: Any, sources: list[Any] | None) -> dict[str, Any]:
    source_items = _normalized_sources(sources)
    ticker = _string(_read(company, "ticker"))
    exchange = _string(_read(company, "exchange") or _resolve_snapshot_value(snapshot, "exchange"))
    has_source_evidence = _has_source_evidence(source_items)
    has_official_source = _has_official_source_page(source_items, company)

    checks = {
        "has_ticker": bool(ticker),
        "has_exchange": bool(exchange),
        "has_source_evidence": has_source_evidence,
        "has_official_source": has_official_source,
    }

    if checks["has_ticker"] and (checks["has_exchange"] or checks["has_source_evidence"]) and has_official_source:
        level = VERIFICATION_LEVEL_VERIFIED_PUBLIC
    elif checks["has_ticker"] or checks["has_exchange"] or checks["has_source_evidence"]:
        level = VERIFICATION_LEVEL_PARTIAL
    else:
        level = VERIFICATION_LEVEL_UNVERIFIED

    missing = [name for name, passed in checks.items() if not passed]
    result = get_verification_badge_meta(level)
    result.update(
        {
            "is_verified": level == VERIFICATION_LEVEL_VERIFIED_PUBLIC,
            "checks": checks,
            "sources_considered": len(source_items),
            "missing_checks": missing,
        }
    )
    return result


def verify_ipo_company(company: Any, snapshot: Any, sources: list[Any] | None) -> dict[str, Any]:
    source_items = _normalized_sources(sources)
    status = _string(_read(company, "status_label") or _resolve_snapshot_value(snapshot, "filing_status", "status"))
    source_evidence = _has_source_evidence(source_items)
    filing_evidence = any(
        any(token in (source.get("source_type") or "").lower() for token in ("filing", "prospectus", "s-1", "f-1"))
        for source in source_items
    ) or bool(_resolve_snapshot_value(snapshot, "filing_url", "filing_date", "cik"))

    checks = {
        "has_status": bool(status),
        "has_source_evidence": source_evidence,
        "has_filing_evidence": filing_evidence,
    }

    if checks["has_status"] and (checks["has_filing_evidence"] or checks["has_source_evidence"]):
        level = VERIFICATION_LEVEL_VERIFIED_IPO
    elif checks["has_status"] or checks["has_source_evidence"] or checks["has_filing_evidence"]:
        level = VERIFICATION_LEVEL_PARTIAL
    else:
        level = VERIFICATION_LEVEL_UNVERIFIED

    missing = [name for name, passed in checks.items() if not passed]
    result = get_verification_badge_meta(level)
    result.update(
        {
            "is_verified": level == VERIFICATION_LEVEL_VERIFIED_IPO,
            "checks": checks,
            "sources_considered": len(source_items),
            "missing_checks": missing,
        }
    )
    return result


def verify_private_opportunity(company: Any, snapshot: Any, sources: list[Any] | None) -> dict[str, Any]:
    source_items = _normalized_sources(sources)
    official_source_page = _has_official_source_page(source_items, company)
    source_name = _string(_read(company, "source_name")) or next(
        (source.get("source_name") for source in source_items if source.get("source_name")),
        None,
    )
    research_only = bool(
        _read(company, "research_only", _resolve_snapshot_value(snapshot, "research_only"))
    )

    checks = {
        "has_official_source_page": official_source_page,
        "has_source_name": bool(source_name),
        "is_research_only": research_only,
    }

    if all(checks.values()):
        level = VERIFICATION_LEVEL_SOURCE_VERIFIED_PRIVATE
    elif sum(1 for passed in checks.values() if passed) >= 2:
        level = VERIFICATION_LEVEL_PARTIAL
    else:
        level = VERIFICATION_LEVEL_UNVERIFIED

    missing = [name for name, passed in checks.items() if not passed]
    result = get_verification_badge_meta(level)
    result.update(
        {
            "is_verified": level == VERIFICATION_LEVEL_SOURCE_VERIFIED_PRIVATE,
            "checks": checks,
            "sources_considered": len(source_items),
            "missing_checks": missing,
        }
    )
    return result
