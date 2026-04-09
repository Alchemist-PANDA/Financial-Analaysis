"""
calculator.py — Pure Python financial metric calculations.

No AI here — just math. Takes raw company data and returns
a dict of computed ratios used by the agent for analysis.
"""

def numeric_value(data: dict, key: str, default: float = 0.0) -> float:
    value = data.get(key, default)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def calculate_metrics(historical_data: list[dict]) -> dict:
    """
    Calculate 5-year financial trends and classification signals.
    Expects 5 years of data in chronological order (Y-4 to Y0).
    """
    if len(historical_data) < 5:
        raise ValueError("Institutional standard requires exactly 5 years of data.")

    years_metrics = []
    for data in historical_data:
        rev = numeric_value(data, "revenue")
        ebitda = numeric_value(data, "ebitda")
        ni = numeric_value(data, "net_income")
        cash = numeric_value(data, "cash")
        debt = numeric_value(data, "debt")
        assets = numeric_value(data, "total_assets", 1.0) or 1.0
        equity = numeric_value(data, "equity", 1.0) or 1.0
        wc = numeric_value(data, "working_capital")
        re = numeric_value(data, "retained_earnings")
        ebit = numeric_value(data, "ebit")
        mve = numeric_value(data, "market_value_equity")
        
        ebitda_margin = round((ebitda / rev) * 100, 1) if rev else 0
        net_margin    = round((ni / rev) * 100, 1) if rev else 0
        net_debt      = round(debt - cash, 1)
        leverage      = round(net_debt / ebitda, 2) if ebitda else 0
        
        # DuPont Components
        asset_turnover = round(rev / assets, 2) if assets else 0
        equity_multiplier = round(assets / equity, 2) if equity else 0
        roe = round(net_margin * asset_turnover * equity_multiplier, 1)

        # Efficiency & Profitability Metrics
        ar    = numeric_value(data, "accounts_receivable")
        inv   = numeric_value(data, "inventory")
        capex = numeric_value(data, "capex")
        cogs  = numeric_value(data, "cogs")
        
        dso = round((ar / rev) * 365, 0) if rev > 0 else 0
        inv_turnover = round(rev / inv, 1) if inv > 0 else 0
        fcf_conv = round(((ebitda - capex) / ebitda) * 100, 1) if ebitda > 0 else 0
        roa = round((ni / assets) * 100, 1) if assets > 0 else 0
        gross_margin = round(((rev - cogs) / rev) * 100, 1) if rev > 0 else 0

        # Capital Structure & Solvency
        int_exp = numeric_value(data, "interest_expense")
        curr_assets = numeric_value(data, "current_assets")
        curr_liab = numeric_value(data, "current_liabilities")
        
        debt_equity = round(debt / equity, 2) if equity > 0 else 0
        curr_ratio = round(curr_assets / curr_liab, 2) if curr_liab > 0 else 0
        quick_ratio = round((curr_assets - inv) / curr_liab, 2) if curr_liab > 0 else 0
        cash_ratio = round(cash / curr_liab, 2) if curr_liab > 0 else 0
        int_coverage = round(ebit / int_exp, 2) if int_exp > 0 else 10.0

        # Valuation
        pe_ratio = round(mve / ni, 1) if ni > 0 else 0
        pb_ratio = round(mve / equity, 1) if equity > 0 else 0
        ev_ebitda = round((mve + debt - cash) / ebitda, 1) if ebitda > 0 else 0

        # Altman Z-Score Calculation
        A = wc / assets
        B = re / assets
        C = ebit / assets
        D = mve / debt if debt > 0 else 10.0
        E = rev / assets
        z_score = round(1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E, 2)

        years_metrics.append({
            "year": data["year"],
            "revenue": rev,
            "ebitda": ebitda,
            "net_income": ni,
            "ebitda_margin": ebitda_margin,
            "net_margin": net_margin,
            "net_debt": net_debt,
            "leverage": leverage,
            "asset_turnover": asset_turnover,
            "equity_multiplier": equity_multiplier,
            "roe": roe,
            "dso": dso,
            "inventory_turnover": inv_turnover,
            "fcf_conversion_pct": fcf_conv,
            "z_score": z_score,
            "roa": roa,
            "gross_margin": gross_margin,
            "debt_equity": debt_equity,
            "current_ratio": curr_ratio,
            "quick_ratio": quick_ratio,
            "cash_ratio": cash_ratio,
            "interest_coverage": int_coverage,
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "ev_ebitda": ev_ebitda
        })

    # 1. Revenue CAGR Calculation
    years_count = len(historical_data)
    y0_rev = numeric_value(historical_data[-1], "revenue")
    y_first_rev = numeric_value(historical_data[0], "revenue")
    if y_first_rev <= 0:
        cagr = 0.0
    else:
        cagr = round(((y0_rev / y_first_rev) ** (1 / (years_count - 1)) - 1) * 100, 1)

    # ... [keep trajectory logic] ...
    recent_5_years = historical_data[-5:]
    growths = []
    for i in range(1, 5):
        prev_revenue = numeric_value(recent_5_years[i - 1], "revenue")
        current_revenue = numeric_value(recent_5_years[i], "revenue")
        if prev_revenue <= 0:
            g = 0
        else:
            g = (current_revenue / prev_revenue) - 1
        growths.append(g)
    
    if all(growths[i] > growths[i-1] for i in range(1, 4)): trajectory = "ACCELERATING"
    elif all(abs(growths[i] - growths[i-1]) < 0.02 for i in range(1, 4)): trajectory = "STEADY"
    elif growths[-1] < growths[-2] and growths[-1] > 0: trajectory = "DECELERATING"
    else: trajectory = "STALLING"

    # 3. Margin & Debt Trends
    margin_diff = years_metrics[-1]["ebitda_margin"] - years_metrics[-2]["ebitda_margin"]
    if margin_diff >= 0.5: margin_signal = "EXPANDING"
    elif margin_diff <= -2.0: margin_signal = "COLLAPSING"
    else: margin_signal = "STABLE"

    lev_y0 = years_metrics[-1]["leverage"]
    lev_y1 = years_metrics[-2]["leverage"]
    if lev_y0 < lev_y1: debt_signal = "DELEVERAGING"
    elif lev_y0 > 5.0: debt_signal = "OVERLEVERAGED"
    else: debt_signal = "STABLE"

    # 4. Solvency Signal (Altman Z)
    z0 = years_metrics[-1]["z_score"]
    if z0 > 2.99: solvency_signal = "SAFE"
    elif z0 > 1.8: solvency_signal = "GREY_ZONE"
    else: solvency_signal = "DISTRESS"

    return {
        "yearly": years_metrics,
        "revenue_cagr_pct": cagr,
        "revenue_trajectory": trajectory,
        "margin_signal": margin_signal,
        "debt_signal": debt_signal,
        "solvency_signal": solvency_signal,
        "current_z_score": z0,
        "current_roe": years_metrics[-1]["roe"],
        "current_roa": years_metrics[-1]["roa"],
        "current_gross_margin": years_metrics[-1]["gross_margin"],
        "current_debt_equity": years_metrics[-1]["debt_equity"],
        "current_ratio": years_metrics[-1]["current_ratio"],
        "current_quick_ratio": years_metrics[-1]["quick_ratio"],
        "current_cash_ratio": years_metrics[-1]["cash_ratio"],
        "current_interest_coverage": years_metrics[-1]["interest_coverage"],
        "current_dso": years_metrics[-1]["dso"],
        "current_inventory_turnover": years_metrics[-1]["inventory_turnover"],
        "current_fcf_conversion_pct": years_metrics[-1]["fcf_conversion_pct"]
    }
