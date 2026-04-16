# Vercel Access Policy (Permanent)

## Policy
- Public URL for users/manual QA: **production domain only**.
- Preview deployments: **protected internal environments**.
- Protected preview URLs are never the canonical frontend entry point.

## Dashboard Setup (Do This Once)
1. Open Vercel project: `financial-analysis` (frontend root `frontend-next`).
2. Go to `Settings -> Domains`.
3. Set your canonical production domain (custom domain or production `.vercel.app`).
4. Go to `Settings -> Deployment Protection`.
5. Keep preview protection enabled (recommended: standard protection flow for previews/internal domains).
6. Confirm production is publicly reachable and preview remains protected.

## Approved Ways To Access Protected Previews
1. **Shareable Links**: generate a temporary preview access link for manual external review.
2. **Protection Bypass for Automation**: use Vercel bypass mechanism for CI/E2E checks.
3. **Deployment Protection Exceptions** (optional): only if your plan/add-on supports public preview-domain exceptions and you intentionally want that behavior.

## Team Rules
- Never post preview URLs as the main app URL in docs/tickets.
- For bug reports, include both:
  - production URL (public baseline)
  - preview URL (internal validation only, when needed)
- Frontend env var `NEXT_PUBLIC_API_URL` must point to backend API origin, not preview frontend URL.

## Reference
- Deployment Protection overview: https://vercel.com/docs/deployment-protection
- Shareable Links: https://vercel.com/docs/deployment-protection/methods-to-bypass-deployment-protection/sharable-links/
- Protection Bypass for Automation: https://vercel.com/docs/deployment-protection/methods-to-bypass-deployment-protection/protection-bypass-automation
- Deployment Protection Exceptions: https://vercel.com/docs/deployment-protection/methods-to-bypass-deployment-protection/deployment-protection-exceptions
