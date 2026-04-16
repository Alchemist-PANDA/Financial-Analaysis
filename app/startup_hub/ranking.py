"""Deterministic ranking for Startup Hub."""

from __future__ import annotations

from typing import Any

from app.startup_hub.constants import (
    ENTITY_TYPE_IPO_WATCH,
    ENTITY_TYPE_PRIVATE_OPPORTUNITY,
    RANKING_DEFAULTS,
    RANKING_SCORE_MAX,
    RANKING_SCORE_MIN,
    VERIFICATION_LEVEL_PARTIAL,
    VERIFICATION_LEVEL_SOURCE_VERIFIED_PRIVATE,
    VERIFICATION_LEVEL_UNVERIFIED,
    VERIFICATION_LEVEL_VERIFIED_IPO,
    VERIFICATION_LEVEL_VERIFIED_PUBLIC,
)
from app.startup_hub.verification import (
    verify_ipo_company,
    verify_private_opportunity,
    verify_public_company,
)


def _read(source: Any, key: str, default: Any = None) -> Any:
    if source is None:
        return default
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _clamp(value: float, minimum: float = RANKING_SCORE_MIN, maximum: float = RANKING_SCORE_MAX) -> float:
    return max(minimum, min(maximum, value))


def _string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _to_float(value: Any) -> float | None:
    try:
        if value is None or isinstance(value, bool):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_metrics(company: Any, snapshot: Any) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for source in (
        _read(company, "metrics", {}),
        _read(snapshot, "metrics_payload", {}),
        _read(snapshot, "data_payload", {}),
        _read(company, "metadata_payload", {}),
        _read(company, "snapshot", {}),
    ):
        if isinstance(source, dict):
            metrics.update(source)
    return metrics


def _pick_metric(metrics: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        if key in metrics:
            value = _to_float(metrics.get(key))
            if value is not None:
                return value
    return None


def _score_from_range(value: float | None, low: float, high: float, *, invert: bool = False) -> float | None:
    if value is None:
        return None
    if high == low:
        return 50.0
    bounded = _clamp(((value - low) / (high - low)) * 100.0)
    return _clamp(100.0 - bounded if invert else bounded)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def _normalized_completeness(company: Any, snapshot: Any) -> float:
    value = _to_float(_read(company, "data_completeness_score"))
    if value is None:
        value = _to_float(_read(snapshot, "completeness_score"))
    if value is None:
        return 0.0
    return value * 100.0 if value <= 1.0 else _clamp(value)


def _resolve_verification(company: Any, snapshot: Any, sources: list[Any] | None) -> dict[str, Any]:
    entity_type = _string(_read(company, "entity_type"))
    if entity_type == ENTITY_TYPE_IPO_WATCH:
        return verify_ipo_company(company, snapshot, sources)
    if entity_type == ENTITY_TYPE_PRIVATE_OPPORTUNITY:
        return verify_private_opportunity(company, snapshot, sources)
    return verify_public_company(company, snapshot, sources)


def compute_growth_score(company: Any, snapshot: Any | None = None) -> float:
    metrics = _extract_metrics(company, snapshot)
    candidates: list[float] = []
    for key_group in (
        ("revenue_growth_pct", "revenue_cagr_pct", "growth_rate_pct", "growth_rate"),
        ("user_growth_pct", "subscriber_growth_pct", "arr_growth_pct"),
        ("funding_growth_pct", "bookings_growth_pct"),
    ):
        metric = _pick_metric(metrics, *key_group)
        score = _score_from_range(metric, -20.0, 60.0)
        if score is not None:
            candidates.append(score)

    completeness = _normalized_completeness(company, snapshot)
    if not candidates:
        return round(completeness * 0.35, 2)
    return round(_average(candidates) * 0.85 + completeness * 0.15, 2)


def compute_quality_score(company: Any, snapshot: Any | None = None) -> float:
    metrics = _extract_metrics(company, snapshot)
    candidates: list[float] = []
    for key_group, low, high, invert in (
        (("gross_margin_pct",), 20.0, 80.0, False),
        (("ebitda_margin_pct", "operating_margin_pct"), -20.0, 35.0, False),
        (("fcf_margin_pct", "free_cash_flow_margin_pct"), -20.0, 25.0, False),
        (("current_fcf_conversion_pct", "fcf_conversion_pct"), 20.0, 100.0, False),
        (("current_roe", "roe"), 0.0, 25.0, False),
        (("rule_of_40",), 0.0, 60.0, False),
        (("retention_pct", "net_dollar_retention_pct"), 75.0, 140.0, False),
    ):
        metric = _pick_metric(metrics, *key_group)
        score = _score_from_range(metric, low, high, invert=invert)
        if score is not None:
            candidates.append(score)

    completeness = _normalized_completeness(company, snapshot)
    if not candidates:
        return round(completeness * 0.30, 2)
    return round(_average(candidates) * 0.85 + completeness * 0.15, 2)


def compute_risk_score(company: Any, snapshot: Any | None = None) -> float:
    metrics = _extract_metrics(company, snapshot)
    candidates: list[float] = []
    for key_group, low, high, invert in (
        (("z_score", "current_z_score"), 0.0, 4.5, False),
        (("cash_runway_months",), 0.0, 24.0, False),
        (("debt_to_ebitda", "leverage"), 0.0, 6.0, True),
        (("current_dso", "dso"), 20.0, 120.0, True),
        (("volatility_pct",), 15.0, 80.0, True),
        (("max_drawdown_pct", "drawdown_pct"), 10.0, 70.0, True),
    ):
        metric = _pick_metric(metrics, *key_group)
        score = _score_from_range(metric, low, high, invert=invert)
        if score is not None:
            candidates.append(score)

    base_score = _average(candidates) if candidates else 45.0
    completeness = _normalized_completeness(company, snapshot)
    adjusted = base_score * 0.8 + completeness * 0.2
    return round(_clamp(adjusted), 2)


def compute_verification_score(
    company: Any,
    snapshot: Any | None = None,
    sources: list[Any] | None = None,
) -> float:
    verification = _resolve_verification(company, snapshot, sources)
    base_map = {
        VERIFICATION_LEVEL_VERIFIED_PUBLIC: 92.0,
        VERIFICATION_LEVEL_VERIFIED_IPO: 88.0,
        VERIFICATION_LEVEL_SOURCE_VERIFIED_PRIVATE: 84.0,
        VERIFICATION_LEVEL_PARTIAL: 56.0,
        VERIFICATION_LEVEL_UNVERIFIED: 20.0,
    }
    base = base_map.get(verification["level"], 20.0)
    completeness = _normalized_completeness(company, snapshot)
    source_count = len(list(sources or []))
    return round(_clamp(base + min(source_count, 5) * 2.0 + completeness * 0.06), 2)


def compute_momentum_score(company: Any, snapshot: Any | None = None) -> float:
    metrics = _extract_metrics(company, snapshot)
    candidates: list[float] = []
    for key_group, low, high, invert in (
        (("price_momentum_pct", "share_price_momentum_pct"), -25.0, 40.0, False),
        (("news_signal_strength", "signal_strength"), 0.0, 10.0, False),
        (("funding_momentum_pct",), -20.0, 40.0, False),
        (("freshness_days", "days_since_update"), 0.0, 60.0, True),
    ):
        metric = _pick_metric(metrics, *key_group)
        score = _score_from_range(metric, low, high, invert=invert)
        if score is not None:
            candidates.append(score)

    completeness = _normalized_completeness(company, snapshot)
    if not candidates:
        return round(completeness * 0.25, 2)
    return round(_average(candidates) * 0.8 + completeness * 0.2, 2)


def build_ranking_explanation(
    company: Any,
    snapshot: Any | None,
    component_scores: dict[str, float],
    verification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metrics = _extract_metrics(company, snapshot)
    verification_result = verification or _resolve_verification(company, snapshot, None)
    drivers: list[str] = []
    red_flags: list[str] = []

    revenue_growth = _pick_metric(metrics, "revenue_growth_pct", "revenue_cagr_pct")
    if revenue_growth is not None and revenue_growth > 15:
        drivers.append(f"Revenue growth is {revenue_growth:.1f}%")
    elif revenue_growth is not None and revenue_growth < 0:
        red_flags.append(f"Revenue growth is negative at {revenue_growth:.1f}%")

    gross_margin = _pick_metric(metrics, "gross_margin_pct")
    if gross_margin is not None and gross_margin >= 60:
        drivers.append(f"Gross margin is strong at {gross_margin:.1f}%")
    elif gross_margin is not None and gross_margin < 30:
        red_flags.append(f"Gross margin is thin at {gross_margin:.1f}%")

    z_score = _pick_metric(metrics, "z_score", "current_z_score")
    if z_score is not None and z_score >= 3.0:
        drivers.append(f"Altman Z-Score is healthy at {z_score:.2f}")
    elif z_score is not None and z_score < 1.8:
        red_flags.append(f"Altman Z-Score is weak at {z_score:.2f}")

    cash_runway = _pick_metric(metrics, "cash_runway_months")
    if cash_runway is not None and cash_runway >= 18:
        drivers.append(f"Cash runway is {cash_runway:.0f} months")
    elif cash_runway is not None and cash_runway < 9:
        red_flags.append(f"Cash runway is short at {cash_runway:.0f} months")

    leverage = _pick_metric(metrics, "debt_to_ebitda", "leverage")
    if leverage is not None and leverage > 4:
        red_flags.append(f"Leverage is elevated at {leverage:.1f}x")

    if verification_result.get("is_verified"):
        drivers.append(f"Verification level is {verification_result['level']}")
    elif verification_result.get("level") == VERIFICATION_LEVEL_PARTIAL:
        red_flags.append("Verification evidence is only partial")
    else:
        red_flags.append("Verification evidence is limited")

    completeness = _normalized_completeness(company, snapshot)
    if completeness < 40:
        red_flags.append(f"Data completeness is low at {completeness:.0f}%")
    elif completeness >= 75:
        drivers.append(f"Data completeness is {completeness:.0f}%")

    ordered_components = sorted(component_scores.items(), key=lambda item: item[1], reverse=True)
    strongest = ", ".join(name.replace("_score", "") for name, _ in ordered_components[:2])
    weakest = ", ".join(name.replace("_score", "") for name, _ in ordered_components[-2:])

    return {
        "top_drivers": drivers[:3],
        "red_flags": red_flags[:3],
        "explanation": f"Highest scoring factors: {strongest}. Weakest factors: {weakest}.",
    }


def compute_total_ranking_score(
    company: Any,
    snapshot: Any | None = None,
    sources: list[Any] | None = None,
) -> dict[str, Any]:
    verification = _resolve_verification(company, snapshot, sources)
    component_scores = {
        "growth_score": compute_growth_score(company, snapshot),
        "quality_score": compute_quality_score(company, snapshot),
        "risk_score": compute_risk_score(company, snapshot),
        "verification_score": compute_verification_score(company, snapshot, sources),
        "momentum_score": compute_momentum_score(company, snapshot),
    }
    weights = RANKING_DEFAULTS["weights"]
    total_score = round(
        component_scores["growth_score"] * weights["growth"]
        + component_scores["quality_score"] * weights["quality"]
        + component_scores["risk_score"] * weights["risk"]
        + component_scores["verification_score"] * weights["verification"]
        + component_scores["momentum_score"] * weights["momentum"],
        2,
    )
    explanation = build_ranking_explanation(company, snapshot, component_scores, verification)
    return {
        "total_score": total_score,
        **component_scores,
        "top_drivers": explanation["top_drivers"],
        "red_flags": explanation["red_flags"],
        "explanation": explanation["explanation"],
        "verification_level": verification["level"],
    }
