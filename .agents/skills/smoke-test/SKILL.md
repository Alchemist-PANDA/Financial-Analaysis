---
name: smoke-test
description: Run after every phase to verify existing features still work in both backend and frontend
---
## Goal
Run backend: cd app && python main.py — verify it runs without errors
Run frontend: cd frontend-next && npm run dev — verify it starts without errors
Check browser console at localhost for red errors
Test each existing feature:

1. Altman-Z solvency score appears when a ticker is entered
2. ROE displays correctly
3. History tab loads without error
4. Watchlist tab - SKIP (not yet implemented, pre-existing)
5. Execute Analysis button triggers the analysis
6. Analysis logs appear after execution
7. Python backend responds to API requests without 500 errors

## Output
BACKEND STATUS: [running/error]
FRONTEND STATUS: [running/error]
PASS: [list]
FAIL: [list with exact error]
REGRESSION: [previously working features now broken]
CONSOLE ERRORS: [count and text]

## Rule
If ANY test fails: halt all work immediately, report exact error, wait for user instruction.

