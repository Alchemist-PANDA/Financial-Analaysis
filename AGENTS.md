# Apex Analytics — Agent Instructions

## Confirmed Architecture (from repo scan)

### Backend (Python/LangGraph)
- `app/agent.py` — makes ALL AI API calls. DO NOT duplicate AI calls anywhere else.
- `app/calculator.py` — contains ALL financial calculations including Altman-Z. SENTINEL FILE. Import from here, never rewrite.
- `app/graph.py` — LangGraph pipeline controlling execution order. DO NOT modify when adding UI features.
- `app/state.py` — shared state container passed through the graph. READ ONLY.
- `app/main.py` — entry point. DO NOT modify.
- `app/sample_data.py` — example input data. READ ONLY.
- `config.py` — model config at root. DO NOT modify.

### Frontend (Next.js TypeScript in frontend-next/)
- `frontend-next/` — ALL frontend work happens here. This is what deploys to Vercel.
- The main layout/page file inside frontend-next/ → label as LAYOUT. DO NOT modify freely.
- Any existing API service/fetch file inside frontend-next/ → label as FRONTEND_FETCHER. DO NOT duplicate.
- `frontend/` — OLD frontend folder. DO NOT touch at all.

### New Feature Folders to Create
- `frontend-next/src/components/MetricsPanel/` — NEW folder for 50-metric dashboard
- `frontend-next/src/components/ComparisonBoard/` — NEW folder for comparison board
- `frontend-next/src/config/features.ts` — NEW file for feature flags

## Hard Rules
1. app/agent.py is the ONLY file that makes AI/API calls
2. app/calculator.py calculations must be imported via the backend API — never rewritten in frontend
3. New frontend components receive data as props only — never fetch themselves
4. All new features start with feature flag = false
5. Never modify app/graph.py, app/state.py, or app/main.py for frontend features
6. New folders only — never drop new files inside existing component folders
7. frontend/ folder is completely off limits — all work in frontend-next/ only
8. Show only diffs, never full file rewrites
9. After every phase: FILES CREATED / FILES MODIFIED / EXISTING FILES TOUCHED

## Backend API Endpoints That Already Exist
- The Python backend exposes financial data via API routes
- Scan app/ to confirm exact endpoints before building any new frontend component
- New components consume these existing endpoints via props passed from parent — never call endpoints directly

## Features That Must Keep Working
- Altman-Z solvency scoring (calculated in app/calculator.py)
- ROE display
- Analysis history tab
- Watchlist tab
- Execute Analysis button and logs panel
- Existing LangGraph pipeline in app/graph.py

## Context Rule
At 50% context window: STOP. Tell user to run --fork and continue in new session.
