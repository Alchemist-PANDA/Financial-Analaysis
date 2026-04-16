"""Normalization helpers for Startup Hub."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterable

from app.startup_hub.constants import (
    ENTITY_TYPE_IPO_WATCH,
    ENTITY_TYPE_PRIVATE_OPPORTUNITY,
    ENTITY_TYPE_PUBLIC_STOCK,
    VERIFICATION_LEVEL_UNVERIFIED,
)


_NON_ALNUM_PATTERN = re.compile(r"[^a-z0-9\s-]+")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def safe_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return default

    lowered = text.lower().replace(",", "").replace("$", "").replace("_", "").strip()
    negative = False
    if lowered.startswith("(") and lowered.endswith(")"):
        lowered = lowered[1:-1].strip()
        negative = True
    if lowered.endswith("%"):
        lowered = lowered[:-1].strip()

    multiplier = 1.0
    suffix_multipliers = {
        "k": 1_000.0,
        "m": 1_000_000.0,
        "b": 1_000_000_000.0,
        "t": 1_000_000_000_000.0,
    }
    if lowered and lowered[-1] in suffix_multipliers:
        multiplier = suffix_multipliers[lowered[-1]]
        lowered = lowered[:-1].strip()

    try:
        parsed = float(lowered)
    except (TypeError, ValueError):
        return default

    if negative:
        parsed *= -1.0
    return parsed * multiplier


def safe_int(value: Any, default: int | None = None) -> int | None:
    parsed = safe_float(value, None)
    if parsed is None:
        return default
    return int(round(parsed))


def clean_company_name(value: Any) -> str:
    text = "" if value is None else str(value)
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\u2019", "'").replace("\u2018", "'")
    normalized = normalized.replace("\u2013", "-").replace("\u2014", "-")
    normalized = normalized.replace("&amp;", "&")
    normalized = _WHITESPACE_PATTERN.sub(" ", normalized).strip(" \"'\t\r\n")
    return normalized


def build_slug(value: str) -> str:
    cleaned = clean_company_name(value)
    ascii_value = unicodedata.normalize("NFKD", cleaned).encode("ascii", "ignore").decode("ascii")
    ascii_value = ascii_value.lower().replace("&", " and ")
    ascii_value = _NON_ALNUM_PATTERN.sub(" ", ascii_value)
    ascii_value = _WHITESPACE_PATTERN.sub(" ", ascii_value).strip()
    if not ascii_value:
        return "unknown-company"
    return ascii_value.replace(" ", "-")


def _read(source: Any, key: str, default: Any = None) -> Any:
    if source is None:
        return default
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_source_items(source_items: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    if not isinstance(source_items, Iterable) or isinstance(source_items, (str, bytes, dict)):
        return normalized

    for item in source_items:
        if item is None:
            continue
        source_name = _string_or_none(_read(item, "source_name"))
        source_type = _string_or_none(_read(item, "source_type")) or "reference"
        source_url = _string_or_none(_read(item, "source_url"))
        normalized.append(
            {
                "source_name": source_name or "Unknown Source",
                "source_type": source_type,
                "source_url": source_url,
                "is_official": bool(_read(item, "is_official", False)),
                "verification_level": _string_or_none(_read(item, "verification_level"))
                or VERIFICATION_LEVEL_UNVERIFIED,
                "published_at": _string_or_none(_read(item, "published_at")),
                "last_checked_at": _string_or_none(_read(item, "last_checked_at")),
                "notes": _string_or_none(_read(item, "notes")),
            }
        )
    return normalized


def compute_data_completeness_score(
    payload: dict[str, Any] | None,
    required_fields: list[str] | tuple[str, ...] | None = None,
) -> float:
    data = dict(payload or {})
    fields = list(required_fields or data.keys())
    if not fields:
        return 0.0

    present = 0
    for field in fields:
        value = data.get(field)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, (list, tuple, set, dict)) and len(value) == 0:
            continue
        present += 1

    return round(present / len(fields), 4)


def _normalize_common_company(raw: dict[str, Any] | None, *, entity_type: str) -> dict[str, Any]:
    payload = dict(raw or {})
    company_name = clean_company_name(
        payload.get("company_name") or payload.get("name") or payload.get("title") or "Unknown Company"
    )
    source_items = _normalize_source_items(payload.get("source_items"))
    normalized = {
        "slug": build_slug(payload.get("slug") or company_name),
        "company_name": company_name,
        "entity_type": entity_type,
        "ticker": _string_or_none(payload.get("ticker")),
        "exchange": _string_or_none(payload.get("exchange") or payload.get("proposed_exchange")),
        "sector": _string_or_none(payload.get("sector")),
        "stage": _string_or_none(payload.get("stage")),
        "status_label": _string_or_none(payload.get("status_label")),
        "short_summary": _string_or_none(payload.get("summary") or payload.get("short_summary")),
        "description": _string_or_none(payload.get("description")),
        "website_url": _string_or_none(payload.get("website_url") or payload.get("official_source_url")),
        "verification_level": _string_or_none(payload.get("verification_level"))
        or VERIFICATION_LEVEL_UNVERIFIED,
        "research_only": bool(payload.get("research_only", True)),
        "source_items": source_items,
        "source_count": len(source_items),
        "metrics": {},
        "snapshot": {},
    }
    return normalized


def normalize_public_company(raw: dict[str, Any] | None) -> dict[str, Any]:
    normalized = _normalize_common_company(raw, entity_type=ENTITY_TYPE_PUBLIC_STOCK)
    normalized["ticker"] = _string_or_none(normalized.get("ticker"))
    if normalized["ticker"]:
        normalized["ticker"] = normalized["ticker"].upper()
    normalized["exchange"] = _string_or_none(normalized.get("exchange"))
    if normalized["exchange"]:
        normalized["exchange"] = normalized["exchange"].upper()

    metrics = {
        "revenue_growth_pct": safe_float(_read(raw or {}, "revenue_growth_pct")),
        "revenue_cagr_pct": safe_float(_read(raw or {}, "revenue_cagr_pct")),
        "gross_margin_pct": safe_float(_read(raw or {}, "gross_margin_pct")),
        "ebitda_margin_pct": safe_float(_read(raw or {}, "ebitda_margin_pct")),
        "fcf_margin_pct": safe_float(_read(raw or {}, "fcf_margin_pct")),
        "debt_to_ebitda": safe_float(_read(raw or {}, "debt_to_ebitda")),
        "z_score": safe_float(_read(raw or {}, "z_score")),
    }
    normalized["metrics"] = metrics
    normalized["snapshot"] = {
        "exchange": normalized["exchange"],
        "status_label": normalized["status_label"],
        "ticker": normalized["ticker"],
    }
    normalized["data_completeness_score"] = compute_data_completeness_score(
        {
            "company_name": normalized["company_name"],
            "slug": normalized["slug"],
            "ticker": normalized["ticker"],
            "exchange": normalized["exchange"],
            "sector": normalized["sector"],
            "status_label": normalized["status_label"],
            "summary": normalized["short_summary"],
            "source_items": normalized["source_items"],
        }
    )
    normalized["metadata_payload"] = {
        "seed_notes": _string_or_none(_read(raw or {}, "seed_notes")),
        "normalized_metrics": metrics,
    }
    return normalized


def normalize_ipo_company(raw: dict[str, Any] | None) -> dict[str, Any]:
    normalized = _normalize_common_company(raw, entity_type=ENTITY_TYPE_IPO_WATCH)
    normalized["filing_status"] = _string_or_none(
        _read(raw or {}, "filing_status") or normalized.get("status_label")
    )
    normalized["expected_window"] = _string_or_none(_read(raw or {}, "expected_window"))
    normalized["proposed_exchange"] = _string_or_none(
        _read(raw or {}, "proposed_exchange") or normalized.get("exchange")
    )
    normalized["snapshot"] = {
        "filing_status": normalized["filing_status"],
        "expected_window": normalized["expected_window"],
        "proposed_exchange": normalized["proposed_exchange"],
        "filing_url": _string_or_none(_read(raw or {}, "filing_url")),
    }
    normalized["metrics"] = {}
    normalized["data_completeness_score"] = compute_data_completeness_score(
        {
            "company_name": normalized["company_name"],
            "slug": normalized["slug"],
            "sector": normalized["sector"],
            "stage": normalized["stage"],
            "status_label": normalized["status_label"],
            "proposed_exchange": normalized["proposed_exchange"],
            "source_items": normalized["source_items"],
        }
    )
    normalized["metadata_payload"] = {
        "seed_notes": _string_or_none(_read(raw or {}, "seed_notes")),
        "snapshot": normalized["snapshot"],
    }
    return normalized


def normalize_private_opportunity(raw: dict[str, Any] | None) -> dict[str, Any]:
    normalized = _normalize_common_company(raw, entity_type=ENTITY_TYPE_PRIVATE_OPPORTUNITY)
    normalized["valuation_usd"] = safe_float(_read(raw or {}, "valuation_usd"))
    normalized["minimum_investment_usd"] = safe_float(_read(raw or {}, "minimum_investment_usd"))
    normalized["official_source_url"] = _string_or_none(_read(raw or {}, "official_source_url"))
    normalized["source_name"] = _string_or_none(_read(raw or {}, "source_name"))
    normalized["snapshot"] = {
        "valuation_usd": normalized["valuation_usd"],
        "minimum_investment_usd": normalized["minimum_investment_usd"],
        "official_source_url": normalized["official_source_url"],
        "source_name": normalized["source_name"],
        "research_only": normalized["research_only"],
    }
    normalized["metrics"] = {}
    normalized["data_completeness_score"] = compute_data_completeness_score(
        {
            "company_name": normalized["company_name"],
            "slug": normalized["slug"],
            "sector": normalized["sector"],
            "stage": normalized["stage"],
            "summary": normalized["short_summary"],
            "official_source_url": normalized["official_source_url"],
            "source_name": normalized["source_name"],
            "source_items": normalized["source_items"],
        }
    )
    normalized["metadata_payload"] = {
        "seed_notes": _string_or_none(_read(raw or {}, "seed_notes")),
        "snapshot": normalized["snapshot"],
    }
    return normalized
