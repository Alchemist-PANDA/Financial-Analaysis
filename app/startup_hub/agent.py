"""Deterministic Startup Hub research assistant logic.

This module intentionally avoids AI API calls. It interprets user queries,
filters deterministic Startup Hub data, and produces grounded explanations.
"""

from __future__ import annotations

import re
from typing import Any

from app.startup_hub.constants import (
    ENTITY_TYPE_IPO_WATCH,
    ENTITY_TYPE_PRIVATE_OPPORTUNITY,
    ENTITY_TYPE_PUBLIC_STOCK,
)
from app.startup_hub.normalizers import build_slug


_COMPARE_PATTERN = re.compile(
    r"(?:compare|versus|vs\.?|against)\s+(.+?)\s+(?:vs\.?|versus|against|and)\s+(.+)",
    re.IGNORECASE,
)
_WORD_PATTERN = re.compile(r"[a-z0-9]+")

_STOPWORDS = {
    "a",
    "an",
    "and",
    "best",
    "candidate",
    "compare",
    "companies",
    "company",
    "explain",
    "first",
    "for",
    "fundamentals",
    "highest",
    "lower",
    "lowest",
    "opportunities",
    "opportunity",
    "rank",
    "ranked",
    "research",
    "risk",
    "show",
    "startup",
    "startups",
    "strongest",
    "summarize",
    "this",
    "top",
    "why",
    "with",
}

_SECTOR_KEYWORDS = {
    "ai": ["enterprise ai", "artificial intelligence", "machine learning", " ai "],
    "cybersecurity": ["cybersecurity", "cloud security", "security"],
    "robotics": ["robotics", "industrial automation", "automation"],
    "digital health": ["digital health", "telehealth", "health"],
    "biotech": ["biotech", "bio"],
    "education": ["education", "edtech", "learning", "language"],
    "computer vision": ["computer vision", "vision"],
}


def _string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalized_text(value: Any) -> str:
    return f" {(_string(value) or '').lower()} "


def _tokens(value: str) -> list[str]:
    return [token for token in _WORD_PATTERN.findall((value or "").lower()) if token not in _STOPWORDS]


def _company_from_candidate(candidate: Any) -> dict[str, Any]:
    if isinstance(candidate, dict):
        company = candidate.get("company")
        if isinstance(company, dict):
            return company
    return {}


def _ranking_from_candidate(candidate: Any) -> dict[str, Any]:
    company = _company_from_candidate(candidate)
    ranking = company.get("ranking")
    return ranking if isinstance(ranking, dict) else {}


def _candidate_text(candidate: Any) -> str:
    company = _company_from_candidate(candidate)
    data_payload = candidate.get("data_payload") if isinstance(candidate, dict) else {}
    return " ".join(
        filter(
            None,
            [
                _string(company.get("company_name")),
                _string(company.get("slug")),
                _string(company.get("ticker")),
                _string(company.get("sector")),
                _string(company.get("status_label")),
                _string(company.get("short_summary")),
                _string((data_payload or {}).get("analysis_summary")),
            ],
        )
    ).lower()


def _sort_key(candidate: Any, sort_preference: str) -> float:
    ranking = _ranking_from_candidate(candidate)
    mapping = {
        "quality_desc": ranking.get("quality_score", 0.0),
        "risk_desc": ranking.get("risk_score", 0.0),
        "momentum_desc": ranking.get("momentum_score", 0.0),
        "verification_desc": ranking.get("verification_score", 0.0),
        "growth_desc": ranking.get("growth_score", 0.0),
        "score_desc": ranking.get("total_score", 0.0),
    }
    return float(mapping.get(sort_preference, ranking.get("total_score", 0.0)) or 0.0)


def infer_entity_type(query: str) -> str | None:
    lowered = (query or "").lower()
    if "ipo" in lowered or "pre-ipo" in lowered or "filing" in lowered:
        return ENTITY_TYPE_IPO_WATCH
    if "private" in lowered or "series a" in lowered or "series b" in lowered:
        return ENTITY_TYPE_PRIVATE_OPPORTUNITY
    if "public" in lowered or "ticker" in lowered or "stock" in lowered:
        return ENTITY_TYPE_PUBLIC_STOCK
    return None


def infer_sector(query: str) -> str | None:
    lowered = f" {(query or '').lower()} "
    for sector, keywords in _SECTOR_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return sector
    return None


def infer_sort_preference(query: str) -> str:
    lowered = (query or "").lower()
    if any(token in lowered for token in ("lower-risk", "lower risk", "safer", "lowest risk")):
        return "risk_desc"
    if any(token in lowered for token in ("quality", "fundamentals", "strongest fundamentals")):
        return "quality_desc"
    if "momentum" in lowered:
        return "momentum_desc"
    if "verification" in lowered or "source verified" in lowered:
        return "verification_desc"
    if "growth" in lowered:
        return "growth_desc"
    return "score_desc"


def infer_risk_preference(query: str) -> str:
    lowered = (query or "").lower()
    if any(token in lowered for token in ("lower-risk", "lower risk", "safer", "lowest risk")):
        return "low"
    if any(token in lowered for token in ("aggressive", "higher-risk", "higher risk")):
        return "high"
    return "balanced"


def parse_agent_query(query: str) -> dict[str, Any]:
    cleaned = (query or "").strip()
    lowered = cleaned.lower()
    mode = "screen"
    compare_terms: list[str] = []

    compare_match = _COMPARE_PATTERN.search(cleaned)
    if compare_match:
        mode = "compare"
        compare_terms = [compare_match.group(1).strip(), compare_match.group(2).strip()]
    elif "ranks first" in lowered or "rank first" in lowered or "why this ranks" in lowered:
        mode = "explain_top"
    elif "summarize" in lowered or "summary" in lowered:
        mode = "summarize"

    tokens = _tokens(cleaned)
    if compare_terms:
        compare_tokens = []
        for term in compare_terms:
            compare_tokens.extend(_tokens(term))
        tokens = [token for token in tokens if token not in compare_tokens]

    return {
        "query": cleaned,
        "mode": mode,
        "entity_type": infer_entity_type(cleaned),
        "sector": infer_sector(cleaned),
        "sort_preference": infer_sort_preference(cleaned),
        "risk_preference": infer_risk_preference(cleaned),
        "compare_terms": compare_terms,
        "search_terms": tokens[:6],
    }


def retrieve_matching_companies(
    filters: dict[str, Any],
    limit: int,
    companies: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    candidates = list(companies or [])
    if not candidates:
        return []

    entity_type = filters.get("entity_type")
    if entity_type:
        candidates = [
            candidate
            for candidate in candidates
            if _company_from_candidate(candidate).get("entity_type") == entity_type
        ]

    sector = _string(filters.get("sector"))
    if sector:
        candidates = [
            candidate
            for candidate in candidates
            if sector.lower() in _candidate_text(candidate)
        ]

    if filters.get("mode") == "compare" and filters.get("compare_terms"):
        matched: list[dict[str, Any]] = []
        used_slugs: set[str] = set()
        for term in list(filters.get("compare_terms") or [])[:2]:
            term_slug = build_slug(term)
            best: dict[str, Any] | None = None
            best_score = -1
            for candidate in candidates:
                company = _company_from_candidate(candidate)
                slug = company.get("slug")
                if slug in used_slugs:
                    continue
                exact_score = 0
                text = _candidate_text(candidate)
                if company.get("slug") == term_slug:
                    exact_score += 5
                if build_slug(company.get("company_name") or "") == term_slug:
                    exact_score += 5
                if term.lower() == (company.get("ticker") or "").lower():
                    exact_score += 6
                if term.lower() in text:
                    exact_score += 2
                if exact_score > best_score:
                    best = candidate
                    best_score = exact_score
            if best is not None and best_score > 0:
                matched.append(best)
                used_slugs.add(_company_from_candidate(best).get("slug"))
        return matched[: max(limit, 2)]

    search_terms = list(filters.get("search_terms") or [])
    if search_terms:
        filtered: list[dict[str, Any]] = []
        for candidate in candidates:
            text = _candidate_text(candidate)
            score = sum(1 for term in search_terms if term in text)
            if score > 0:
                candidate = {**candidate, "_search_score": score}
                filtered.append(candidate)
        if filtered:
            candidates = filtered

    sort_preference = _string(filters.get("sort_preference")) or "score_desc"
    candidates.sort(
        key=lambda candidate: (
            float(candidate.get("_search_score", 0.0) or 0.0),
            _sort_key(candidate, sort_preference),
        ),
        reverse=True,
    )

    if filters.get("risk_preference") == "low":
        low_risk = [candidate for candidate in candidates if _sort_key(candidate, "risk_desc") >= 55.0]
        if low_risk:
            candidates = low_risk

    return candidates[:limit]


def build_compare_narrative(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_company = _company_from_candidate(left)
    right_company = _company_from_candidate(right)
    left_ranking = _ranking_from_candidate(left)
    right_ranking = _ranking_from_candidate(right)

    categories = {
        "growth": "growth_score",
        "quality": "quality_score",
        "risk": "risk_score",
        "momentum": "momentum_score",
        "verification": "verification_score",
        "transparency": "verification_score",
    }
    category_winners: dict[str, str] = {}
    notes: list[str] = []
    for label, key in categories.items():
        left_value = float(left_ranking.get(key, 0.0) or 0.0)
        right_value = float(right_ranking.get(key, 0.0) or 0.0)
        if left_value > right_value:
            winner = left_company.get("company_name")
        elif right_value > left_value:
            winner = right_company.get("company_name")
        else:
            winner = "tie"
        category_winners[label] = winner

    left_total = float(left_ranking.get("total_score", 0.0) or 0.0)
    right_total = float(right_ranking.get("total_score", 0.0) or 0.0)
    if left_total > right_total:
        leader = left_company
        trailer = right_company
        leader_ranking = left_ranking
    elif right_total > left_total:
        leader = right_company
        trailer = left_company
        leader_ranking = right_ranking
    else:
        leader = left_company
        trailer = right_company
        leader_ranking = left_ranking

    if left_total != right_total and leader_ranking.get("top_drivers"):
        notes.append(f"{leader.get('company_name')} leads because {leader_ranking['top_drivers'][0].rstrip('.')}.")
    if leader_ranking.get("red_flags"):
        notes.append(f"Key caution: {leader_ranking['red_flags'][0].rstrip('.')}.")

    if left_total == right_total:
        summary = (
            f"{left_company.get('company_name')} and {right_company.get('company_name')} are tied on the current deterministic Startup Hub score. "
            f"The comparison falls back to category-level winners and disclosure quality."
        )
    else:
        summary = (
            f"{leader.get('company_name')} ranks ahead of {trailer.get('company_name')} on the current deterministic Startup Hub score. "
            f"The strongest category edge is in "
            f"{next((label for label, winner in category_winners.items() if winner == leader.get('company_name')), 'overall score')}."
        )

    return {
        "left_slug": left_company.get("slug"),
        "right_slug": right_company.get("slug"),
        "left_name": left_company.get("company_name"),
        "right_name": right_company.get("company_name"),
        "category_winners": category_winners,
        "summary": summary,
        "notes": notes,
    }


def build_agent_summary(
    query: str,
    companies: list[dict[str, Any]],
    filters: dict[str, Any],
) -> dict[str, Any]:
    mode = filters.get("mode") or "screen"
    matches = [_company_from_candidate(candidate) for candidate in companies]
    reasoning_points: list[str] = []
    comparison: dict[str, Any] = {}

    if mode == "compare":
        if len(companies) >= 2:
            comparison = build_compare_narrative(companies[0], companies[1])
            reasoning_points.extend(comparison.get("notes") or [])
            return {
                "summary": comparison.get("summary"),
                "reasoning_points": reasoning_points,
                "comparison": comparison,
            }
        return {
            "summary": "I could not match two distinct companies for that comparison from the current Startup Hub dataset.",
            "reasoning_points": ["Try using company names, tickers, or exact Startup Hub slugs."],
            "comparison": {},
        }

    if not companies:
        return {
            "summary": "I could not find deterministic Startup Hub matches for that query.",
            "reasoning_points": ["Try a company name, ticker, sector, or entity type such as IPO or private."],
            "comparison": {},
        }

    top_company = matches[0]
    top_ranking = _ranking_from_candidate(companies[0])
    entity_type = top_company.get("entity_type")

    if mode == "explain_top":
        if top_ranking.get("top_drivers"):
            reasoning_points.extend(top_ranking.get("top_drivers")[:2])
        if top_ranking.get("red_flags"):
            reasoning_points.append(f"Caution: {top_ranking['red_flags'][0]}")
        return {
            "summary": (
                f"{top_company.get('company_name')} is currently first within the interpreted filter set because its total score is "
                f"{float(top_ranking.get('total_score', 0.0) or 0.0):.1f} and its strongest drivers are grounded in the stored ranking breakdown."
            ),
            "reasoning_points": reasoning_points,
            "comparison": {},
        }

    if mode == "summarize":
        if entity_type == ENTITY_TYPE_IPO_WATCH:
            reasoning_points.append(
                f"Status is {top_company.get('status_label') or 'not confirmed'} with verification {top_company.get('verification_level')}."
            )
        elif entity_type == ENTITY_TYPE_PRIVATE_OPPORTUNITY:
            reasoning_points.append("This listing is research-only and not tradable on the platform.")
        else:
            reasoning_points.append(
                f"Verification is {top_company.get('verification_level')} with total score {float(top_ranking.get('total_score', 0.0) or 0.0):.1f}."
            )
        if top_company.get("short_summary"):
            reasoning_points.append(top_company["short_summary"])
        return {
            "summary": f"{top_company.get('company_name')} is the closest deterministic match for: {query.strip()}",
            "reasoning_points": reasoning_points[:3],
            "comparison": {},
        }

    if top_ranking.get("top_drivers"):
        reasoning_points.extend(top_ranking.get("top_drivers")[:2])
    if top_ranking.get("red_flags"):
        reasoning_points.append(f"Caution: {top_ranking['red_flags'][0]}")

    summary = (
        f"I found {len(matches)} deterministic Startup Hub match"
        f"{'' if len(matches) == 1 else 'es'} and ranked them using the stored Startup Hub score. "
        f"The current top result is {top_company.get('company_name')} with total score "
        f"{float(top_ranking.get('total_score', 0.0) or 0.0):.1f}."
    )
    return {
        "summary": summary,
        "reasoning_points": reasoning_points[:3],
        "comparison": {},
    }
