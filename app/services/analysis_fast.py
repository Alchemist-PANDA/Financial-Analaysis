import asyncio
import json
from typing import Any

from app.calculator import calculate_metrics, numeric_value
from app.engine.orchestrator import run_full_analysis
from app.services.fetch_parallel import fetch_parallel


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _pick_number(data: dict, *keys: str, default: float = 0.0) -> float:
    for key in keys:
        value = numeric_value(data, key, None)
        if value is not None:
            return _to_float(value, default)
    return default


def _derive_color_signal(z_score: float) -> str:
    if z_score > 2.99:
        return "GREEN"
    if z_score > 1.8:
        return "YELLOW"
    return "RED"


def _archetype(metrics: dict) -> str:
    cagr = _to_float(metrics.get("revenue_cagr_pct"))
    fcf = _to_float(metrics.get("current_fcf_conversion_pct"))
    z_score = _to_float(metrics.get("current_z_score"))
    turnover = _to_float(metrics.get("current_inventory_turnover"))
    if z_score < 1.8:
        return "DISTRESSED"
    if cagr > 15 and fcf > 75:
        return "COMPOUNDER"
    if cagr < 0 and fcf < 50:
        return "VALUE TRAP"
    if turnover > 8 and fcf > 70:
        return "ASSET-LIGHT FLYER"
    return "TRANSITION"


def _build_flags(metrics: dict) -> list[dict]:
    flags: list[dict] = []
    z_score = _to_float(metrics.get("current_z_score"))
    fcf = _to_float(metrics.get("current_fcf_conversion_pct"))
    roe = _to_float(metrics.get("current_roe"))
    cagr = _to_float(metrics.get("revenue_cagr_pct"))

    if z_score > 3:
        flags.append({"emoji": "+", "name": "Solvency Cushion", "explanation": f"Altman Z-Score is {z_score:.2f}, well above distress levels."})
    elif z_score < 1.8:
        flags.append({"emoji": "!", "name": "Solvency Pressure", "explanation": f"Altman Z-Score is {z_score:.2f}, which points to elevated balance-sheet risk."})

    if fcf > 80:
        flags.append({"emoji": "+", "name": "Cash Conversion", "explanation": f"Free cash flow conversion is {fcf:.1f}%, indicating strong earnings quality."})
    elif fcf < 50:
        flags.append({"emoji": "!", "name": "Weak Cash Conversion", "explanation": f"Free cash flow conversion is only {fcf:.1f}%, limiting flexibility."})

    if roe > 20:
        flags.append({"emoji": "+", "name": "ROE Strength", "explanation": f"Return on equity is {roe:.1f}%, which is strong for large-cap equities."})
    if cagr < 0:
        flags.append({"emoji": "!", "name": "Revenue Contraction", "explanation": f"Revenue CAGR is {cagr:.1f}%, so growth is moving in reverse."})

    return flags[:3]


def _build_analysis(company_name: str, ticker: str, metrics: dict) -> dict:
    z_score = _to_float(metrics.get("current_z_score"))
    cagr = _to_float(metrics.get("revenue_cagr_pct"))
    roe = _to_float(metrics.get("current_roe"))
    fcf = _to_float(metrics.get("current_fcf_conversion_pct"))
    margin_signal = str(metrics.get("margin_signal", "STABLE"))
    solvency_signal = str(metrics.get("solvency_signal", "GREY_ZONE"))
    archetype = _archetype(metrics)
    color_signal = _derive_color_signal(z_score)

    diagnosis = (
        f"{company_name} screens as {archetype}. Revenue CAGR is {cagr:.1f}%, ROE is {roe:.1f}%, "
        f"free cash flow conversion is {fcf:.1f}%, and the solvency profile is {solvency_signal.lower()}."
    )

    if color_signal == "GREEN":
        retail = "Financial profile is resilient and lower risk."
    elif color_signal == "RED":
        retail = "Balance-sheet and cash-conversion risk are elevated."
    else:
        retail = "Mixed fundamentals; underwriting discipline still matters."

    summary = (
        f"{ticker} shows {margin_signal.lower()} margins with a {solvency_signal.lower()} balance-sheet profile. "
        f"The deterministic view favors cash conversion and solvency over narrative."
    )

    return {
        "pattern_diagnosis": diagnosis,
        "flags": _build_flags(metrics),
        "analyst_verdict_archetype": archetype,
        "analyst_verdict_summary": summary,
        "retail_verdict": retail,
    }


def _scorecard_inputs(company_name: str, historical_data: list[dict]) -> dict:
    latest = historical_data[-1] if historical_data else {}
    prior = historical_data[-2] if len(historical_data) > 1 else {}

    revenue = _pick_number(latest, "revenue")
    ebitda = _pick_number(latest, "ebitda")
    net_income = _pick_number(latest, "net_income")
    total_debt = _pick_number(latest, "debt", "total_debt")
    cash = _pick_number(latest, "cash", "cash_equivalents")
    total_assets = _pick_number(latest, "total_assets")
    total_equity = _pick_number(latest, "equity", "total_equity")
    market_cap = _pick_number(latest, "market_value_equity", "market_cap")
    cogs = _pick_number(latest, "cogs")

    return {
        "company_name": company_name,
        "revenue": revenue,
        "ebitda": ebitda,
        "net_income": net_income,
        "interest_expense": _pick_number(latest, "interest_expense"),
        "total_debt": total_debt,
        "cash_equivalents": cash,
        "total_assets": total_assets,
        "current_assets": _pick_number(latest, "current_assets"),
        "current_liabilities": _pick_number(latest, "current_liabilities"),
        "short_term_debt": _pick_number(latest, "short_term_debt"),
        "gross_profit": max(revenue - cogs, 0.0) if revenue else 0.0,
        "cfo": max(ebitda * 0.8, 0.0),
        "capex": _pick_number(latest, "capex"),
        "accounts_receivable": _pick_number(latest, "accounts_receivable"),
        "inventory": _pick_number(latest, "inventory"),
        "accounts_payable": _pick_number(latest, "accounts_payable"),
        "cogs": cogs,
        "market_cap": market_cap,
        "ev": market_cap + total_debt - cash if market_cap else 0.0,
        "retained_earnings": _pick_number(latest, "retained_earnings", default=net_income),
        "total_equity": total_equity,
        "revenue_prior": _pick_number(prior, "revenue"),
        "ebitda_prior": _pick_number(prior, "ebitda"),
        "net_income_prior": _pick_number(prior, "net_income"),
        "total_debt_prior": _pick_number(prior, "debt", "total_debt"),
        "cash_prior": _pick_number(prior, "cash", "cash_equivalents"),
        "total_equity_prior": _pick_number(prior, "equity", "total_equity"),
        "working_capital": _pick_number(latest, "working_capital"),
        "working_capital_prior": _pick_number(prior, "working_capital"),
        "revenue_cagr_years": max(len(historical_data) - 1, 1),
        "data_source": "ticker",
    }


def _sanitize(payload: dict) -> dict:
    return json.loads(json.dumps(payload))


def _trim_metrics(metrics: dict) -> dict:
    yearly = []
    for year in metrics.get("yearly", []) or []:
        yearly.append(
            {
                "year": year.get("year"),
                "revenue": year.get("revenue"),
                "dso": year.get("dso"),
                "inventory_turnover": year.get("inventory_turnover"),
                "fcf_conversion_pct": year.get("fcf_conversion_pct"),
                "ebitda_margin": year.get("ebitda_margin"),
                "asset_turnover": year.get("asset_turnover"),
                "roe": year.get("roe"),
                "z_score": year.get("z_score"),
            }
        )

    return {
        "yearly": yearly,
        "revenue_cagr_pct": metrics.get("revenue_cagr_pct"),
        "margin_signal": metrics.get("margin_signal"),
        "solvency_signal": metrics.get("solvency_signal"),
        "current_z_score": metrics.get("current_z_score"),
        "current_fcf_conversion_pct": metrics.get("current_fcf_conversion_pct"),
        "current_roe": metrics.get("current_roe"),
        "current_dso": metrics.get("current_dso"),
        "current_inventory_turnover": metrics.get("current_inventory_turnover"),
    }


def _trim_scorecard(scorecard: dict) -> dict:
    trimmed = dict(scorecard)
    trimmed.pop("inputs", None)
    if not trimmed.get("narrative_error"):
        trimmed.pop("narrative_error", None)
    return trimmed


async def run_fast_analysis(ticker: str) -> dict:
    fetched = await fetch_parallel(ticker, include_news=False)
    historical_data = list(fetched.get("historical_data") or [])
    if not historical_data:
        raise ValueError(f"No historical data available for {ticker}")

    metrics = await asyncio.to_thread(calculate_metrics, historical_data)
    company_name = str(fetched.get("company_name") or ticker).strip() or ticker.upper()
    normalized_ticker = str(fetched.get("ticker") or ticker).strip().upper()
    analysis = _build_analysis(company_name, normalized_ticker, metrics)
    scorecard = await asyncio.to_thread(run_full_analysis, _scorecard_inputs(company_name, historical_data), "credit")
    payload = {
        "ticker": normalized_ticker,
        "company_name": company_name,
        "metrics": _trim_metrics(metrics),
        "analysis": analysis,
        "color_signal": _derive_color_signal(_to_float(metrics.get("current_z_score"))),
        "scorecard": _trim_scorecard(scorecard),
    }
    return _sanitize(payload)
