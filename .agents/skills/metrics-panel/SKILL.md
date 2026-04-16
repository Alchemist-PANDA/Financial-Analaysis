---
name: metrics-panel
description: Use when building the 50-metric financial health dashboard panels in Next.js TypeScript
---
## Goal
Build MetricsPanel in frontend-next/src/components/MetricsPanel/ as five separate .tsx files:

ProfitabilityPanel.tsx: ROE, ROA, ROIC, Gross Margin, EBITDA Margin, Net Margin
SolvencyPanel.tsx: Altman-Z (value comes from backend via props — app/calculator.py calculates it), Debt/Equity, Interest Coverage, Current Ratio
LiquidityPanel.tsx: Quick Ratio, Cash Ratio, Operating Cash Flow
ValuationPanel.tsx: P/E, P/B, EV/EBITDA, PEG Ratio, DCF Intrinsic Value
GrowthPanel.tsx: Revenue CAGR, EPS Growth, FCF Growth
index.tsx: parent receiving ONE prop — financialData typed as FinancialData interface

## Constraints
- All files are TypeScript .tsx not .jsx
- Receives data as props only — never calls fetch() or any API directly
- Does NOT import from app/ Python files
- Does NOT modify the main Next.js layout page
- TypeScript interface for financialData must match what app/calculator.py returns

## Gotchas
- Altman-Z is calculated in app/calculator.py — the frontend only displays the value, never recalculates
- One file per panel — never one giant file
- Show diff only, not full files
- Check app/calculator.py first to confirm the exact field names returned before naming TypeScript props
