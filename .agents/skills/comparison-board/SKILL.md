---
name: comparison-board
description: Use when building the company comparison board feature in Next.js TypeScript
---
## Goal
Build ComparisonBoard in frontend-next/src/components/ComparisonBoard/ with:

MetricRow.tsx: one row, four columns (metric name, companyA value, companyB value, industryAvg)
- GREEN color if value beats industry average, RED if below
WinnerScore.tsx: "Company A stronger on X/50 metrics"
index.tsx: receives companyA, companyB, industryAverage as typed props. Fixed column widths only.

## Constraints
- All TypeScript .tsx files
- Pure display component — zero API calls
- Does NOT modify the main Next.js layout page
- Does NOT touch app/ backend files
- Fixed column widths only — dynamic widths cause layout breaks
- TypeScript types must match app/calculator.py output field names exactly

## Gotchas
- Previous attempt broke because the component tried to fetch its own data — NEVER do this
- All financial calculations happen in app/calculator.py before data reaches this component
- Column widths must be hardcoded — check existing CSS/Tailwind classes used in the project
