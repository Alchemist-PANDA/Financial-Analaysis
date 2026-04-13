"""
agent.py — Calls the Groq API (free, works globally) to produce a
structured financial analysis using LLaMA 3.3 70B.
"""

import json
import sys
import os

from config import GROQ_API_KEY, MODEL_NAME, MAX_TOKENS
from app.engine.narrative import build_narrative_prompt, validate_narrative


def _extract_json_object(text: str) -> str | None:
    """
    Best-effort extraction when the model returns extra text around JSON.
    Keeps things simple to avoid introducing new dependencies.
    """

    if not text:
        return None

    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < 0 or end <= start:
        return None
    return text[start : end + 1]


def _fallback_analysis(company: dict, metrics: dict, reason: str) -> dict:
    ticker = str(company.get("ticker") or "").upper() or "UNKNOWN"
    z = metrics.get("current_z_score")
    try:
        z_val = float(z) if z is not None else 0.0
    except Exception:
        z_val = 0.0

    archetype = "DISTRESSED" if z_val and z_val < 1.8 else "TRANSITION"
    flags = [
        {
            "emoji": "!",
            "name": "LLM Fallback",
            "explanation": f"AI narrative unavailable ({reason}).",
        }
    ]
    if z is not None:
        flags.append(
            {
                "emoji": "Z",
                "name": "Altman Z-Score",
                "explanation": f"Current Z-Score: {z_val:.2f} for {ticker}.",
            }
        )

    return {
        "pattern_diagnosis": (
            f"DIAGNOSIS: FALLBACK MODE for {ticker}. "
            "The AI narrative generator failed, so this result is based on deterministic metrics only. "
            "Retry later for a full institutional narrative."
        ),
        "flags": flags,
        "analyst_verdict_archetype": archetype,
        "analyst_verdict_summary": (
            "Automated fallback summary. Validate key financial statements and rerun analysis when the AI engine is available."
        ),
        "retail_verdict": "AI offline; metrics only.",
    }


def _normalize_analysis_payload(payload: dict) -> dict:
    """
    Ensure the analysis payload matches the frontend contract:
      - keys exist
      - analyst_verdict_archetype is a string (not a list)
      - pattern_diagnosis is a string (not an object)
      - flags is a list of objects
    """

    if not isinstance(payload, dict):
        return {}

    # Some model failures wrap everything under "analysis"
    if isinstance(payload.get("analysis"), dict) and any(
        k in payload["analysis"]
        for k in (
            "pattern_diagnosis",
            "flags",
            "analyst_verdict_archetype",
            "analyst_verdict_summary",
            "retail_verdict",
        )
    ):
        merged = dict(payload.get("analysis") or {})
        # Keep top-level archetype if present (some generations put it outside).
        if "analyst_verdict_archetype" in payload and "analyst_verdict_archetype" not in merged:
            merged["analyst_verdict_archetype"] = payload.get("analyst_verdict_archetype")
        payload = merged

    diagnosis = payload.get("pattern_diagnosis")
    if isinstance(diagnosis, dict):
        payload["pattern_diagnosis"] = json.dumps(diagnosis, ensure_ascii=True)
    elif diagnosis is None:
        payload["pattern_diagnosis"] = "No diagnosis available."
    else:
        payload["pattern_diagnosis"] = str(diagnosis)

    flags = payload.get("flags")
    if not isinstance(flags, list):
        payload["flags"] = []
    else:
        cleaned = []
        for item in flags:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            explanation = item.get("explanation")
            if not name or not explanation:
                continue
            cleaned.append(
                {
                    "emoji": str(item.get("emoji") or ""),
                    "name": str(name),
                    "explanation": str(explanation),
                }
            )
        payload["flags"] = cleaned

    archetype = payload.get("analyst_verdict_archetype")
    if isinstance(archetype, list):
        archetype = archetype[0] if archetype else "TRANSITION"
    if not isinstance(archetype, str) or not archetype.strip():
        archetype = "TRANSITION"
    payload["analyst_verdict_archetype"] = archetype

    summary = payload.get("analyst_verdict_summary")
    payload["analyst_verdict_summary"] = str(summary) if summary is not None else "No summary available."

    retail = payload.get("retail_verdict")
    payload["retail_verdict"] = str(retail) if retail is not None else "No retail verdict."

    return payload


def run_snapshot_agent(company_data: dict | None, metrics: dict | None, search_results: list = None) -> dict:
    """Call Groq and return a structured institutional-grade financial trend analysis."""

    # Guard against None inputs from the graph
    safe_company = dict(company_data or {})
    safe_metrics = dict(metrics or {})

    # [ENHANCED SCRAPER] Add extended metrics if ticker is available
    ticker = safe_company.get("ticker")
    if ticker:
        safe_company.update(scrape_extended_financials(ticker))

    # Prepare data for prompt
    data_summary = json.dumps({
        "company": safe_company,
        "5yr_metrics_table": safe_metrics.get("yearly", []),
        "senior_indicators": {
            "revenue_cagr": f"{safe_metrics.get('revenue_cagr_pct', 0)}%",
            "revenue_trajectory": safe_metrics.get("revenue_trajectory", "STABLE"),
            "margin_signal": safe_metrics.get("margin_signal", "STABLE"),
            "solvency_signal": safe_metrics.get("solvency_signal", "SAFE"),
            "current_z_score": safe_metrics.get("current_z_score", 0),
            "current_roe": f"{safe_metrics.get('current_roe', 0)}%",
            "current_dso": safe_metrics.get("current_dso", 0),
            "current_inventory_turnover": safe_metrics.get("current_inventory_turnover", 0),
            "current_fcf_conversion": f"{safe_metrics.get('current_fcf_conversion_pct', 0)}%",
            "debt_trajectory": safe_metrics.get("debt_signal", "STABLE")
        },
        "recent_news": search_results or []
    }, indent=2)

    prompt = f"""## IDENTITY & INSTITUTIONAL STANDARD
You are a Senior Institutional Partner & Global Head of Equities. Your mandate is to provide a BRUTALLY HONEST, forensics-first analysis of the provided 5-year financial dataset. You do not hedge. You do not use "could" or "might". You provide cold, hard institutional verdicts.

## ANALYTICAL DIRECTIVES: "THE PARTNER STANDARD"
1. **Forensic Quality of Earnings**: 
   - Analyze **DSO** (Days Sales Outstanding) and **Inventory Turnover**. Are they hiding bad debt or obsolete stock? 
   - Analyze **FCF Conversion**. Is EBITDA converting to cash, or is it a "paper profit"?
2. **DuPont & Solvency**: 
   - Use the **Altman Z-Score** to identify "Metabolic Distress".
   - Break down **ROE** into Margin, Turnover, and Leverage. Is the return earned through efficiency or just borrowing money?
3. **Pattern Diagnosis Archetypes**:
   - **THE CANNIBAL**: Flat revenue/EBITDA but aggressive buybacks driving EPS. "Eating itself to look healthy."
   - **THE CAPITAL DESTROYER**: High growth/revenue but negative FCF conversion and falling ROE. "Burning furniture to keep the house warm."
   - **THE MARGIN SCISSOR**: Revenue up, EBITDA margins down. "Scale is a myth here."
   - **ASSET-LIGHT FLYER**: High Asset Turnover (>1.5x) and high FCF conversion.

## DATA INPUTS
{data_summary}

## OUTPUT FORMAT — JSON STRICT
Return ONLY a JSON object matching this schema (double quotes required):
{{
  "pattern_diagnosis": "string",
  "flags": [{{"emoji": "string", "name": "string", "explanation": "string"}}],
  "analyst_verdict_archetype": "string",
  "analyst_verdict_summary": "string",
  "retail_verdict": "string"
}}
"""

    analysis: dict

    # If Groq isn't configured, keep the system usable with a deterministic fallback.
    if not GROQ_API_KEY:
        analysis = _fallback_analysis(safe_company, safe_metrics, reason="missing GROQ_API_KEY")
    else:
        try:
            from groq import Groq

            client = Groq(api_key=GROQ_API_KEY)
            response = client.chat.completions.create(
                model=MODEL_NAME,
                max_tokens=MAX_TOKENS,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Return ONLY a valid JSON object. No markdown. No code fences. "
                            "Use double quotes for all keys and string values."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )

            raw_text = (response.choices[0].message.content or "").strip()
            try:
                analysis = json.loads(raw_text)
            except Exception:
                extracted = _extract_json_object(raw_text)
                if extracted:
                    analysis = json.loads(extracted)
                else:
                    analysis = _fallback_analysis(safe_company, safe_metrics, reason="invalid JSON from model")
                    analysis["analysis_raw"] = raw_text[:2000]
        except Exception as e:
            analysis = _fallback_analysis(safe_company, safe_metrics, reason=str(e))

    analysis = _normalize_analysis_payload(analysis)

    return {
        "company_name":       safe_company.get("company_name", "Unknown"),
        "raw_inputs":         safe_company,
        "calculated_metrics": safe_metrics,
        "search_results":     search_results,
        "analysis":           analysis,
    }


def scrape_extended_financials(ticker: str) -> dict:
    """
    Scrapes COGS, Interest Expense, Current Assets, Current Liabilities
    from Yahoo Finance using yfinance. 
    Runs in a background thread with a 5-second timeout to prevent blocking.
    """
    import concurrent.futures

    def _fetch():
        extended = {
            "cogs": 0,
            "interest_expense": 0,
            "current_assets": 0,
            "current_liabilities": 0,
        }
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)

            # Income Statement
            income_stmt = stock.financials
            if income_stmt is not None and not income_stmt.empty:
                if "Cost Of Revenue" in income_stmt.index:
                    extended["cogs"] = float(income_stmt.loc["Cost Of Revenue"].iloc[0]) / 1_000_000
                if "Interest Expense" in income_stmt.index:
                    extended["interest_expense"] = abs(float(income_stmt.loc["Interest Expense"].iloc[0])) / 1_000_000

            # Balance Sheet
            balance_sheet = stock.balance_sheet
            if balance_sheet is not None and not balance_sheet.empty:
                if "Current Assets" in balance_sheet.index:
                    extended["current_assets"] = float(balance_sheet.loc["Current Assets"].iloc[0]) / 1_000_000
                if "Current Liabilities" in balance_sheet.index:
                    extended["current_liabilities"] = float(balance_sheet.loc["Current Liabilities"].iloc[0]) / 1_000_000
                if "Total Assets" in balance_sheet.index:
                    extended["total_assets"] = float(balance_sheet.loc["Total Assets"].iloc[0]) / 1_000_000
        except Exception:
            pass
        return extended

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_fetch)
        try:
            return future.result(timeout=1)  # Strict 1s timeout
        except concurrent.futures.TimeoutError:
            print(f"[SCRAPER TIMEOUT] Failed to fetch extended data for {ticker} in 1s.")
            return {
                "cogs": 0,
                "interest_expense": 0,
                "current_assets": 0,
                "current_liabilities": 0,
            }


def get_llm_client():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set.")
    from groq import Groq
    return Groq(api_key=GROQ_API_KEY)


def generate_scorecard_narrative(result: dict) -> str:
    prompt = build_narrative_prompt(result)
    client = get_llm_client()

    narrative = ""
    for attempt in range(2):
        response = client.chat.completions.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior equity and credit analyst. Respond with the required structure only.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        narrative = (response.choices[0].message.content or "").strip()
        if validate_narrative(narrative):
            return narrative
        if attempt == 0:
            print("WARN: Narrative failed validation (missing numbers). Retrying...")

    return "[AUTO-GENERATED - verify numbers] " + narrative


def generate_chart_intel_verdict(ticker: str, price_change: float, signals: dict) -> str:
    """
    Optional LLM enhancement for Chart Intelligence.

    Note: All AI calls must live in this module (see AGENTS.md hard rule #1).
    """

    if not GROQ_API_KEY:
        return ""

    # Keep the payload lean to reduce serialization surprises.
    safe_signals = {
        "price_change": float(price_change),
        "news": signals.get("news"),
        "volume": signals.get("volume"),
        "technical": signals.get("technical"),
    }

    prompt = (
        f"You are a Senior Institutional Analyst. Explain why {ticker.upper()} moved "
        f"{price_change:.1f}% given these signals:\n{json.dumps(safe_signals, indent=2)}\n\n"
        "Write ONE concise sentence (max 30 words). Be direct. Use terms like "
        "'catalyst-driven', 'institutional accumulation', 'resistance breach', or "
        "'momentum exhaustion'. Include the % move explicitly."
    )

    client = get_llm_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        max_tokens=min(MAX_TOKENS, 120),
        messages=[
            {
                "role": "system",
                "content": "Return a single sentence only. No JSON. No quotes. No extra text.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    return (response.choices[0].message.content or "").strip().strip('"')
