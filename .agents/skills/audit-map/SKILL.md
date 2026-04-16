---
name: audit-map
description: Use this skill before ANY code change. Maps all existing files across app/ and frontend-next/ and flags cascade risk.
---
## Goal
Scan both app/ and frontend-next/ completely. Output:

BACKEND FILES (app/):
- agent.py: [what it does]
- calculator.py: [what calculations exist — list them all]
- graph.py: [pipeline steps]
- state.py: [state fields]
- main.py: [entry point]

FRONTEND FILES (frontend-next/):
- List every file found
- Identify the main page/layout file → this is LAYOUT
- Identify any API fetch/service files → these are FRONTEND_FETCHER
- Identify any existing component files

SAFE TO CREATE NEW FILES IN: [folders]
READ ONLY: [files]
DO NOT TOUCH: [files]
CASCADE RISK: [shared state, API contracts between Python backend and Next.js frontend]

API CONTRACT:
- List every endpoint the Python backend exposes
- List what data shape each endpoint returns
- New MetricsPanel and ComparisonBoard will consume this data as props

## Gotchas
- app/calculator.py already has Altman-Z — the frontend must never recalculate this
- The Python backend and Next.js frontend communicate via HTTP — document the exact endpoints
- frontend/ folder is dead code — never scan or touch it
- TypeScript types must match the Python backend's response shape exactly
