"""Refresh and cache-maintenance tasks for Startup Hub."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.startup_hub.cache import invalidate_cache
from app.startup_hub.ipo_fetcher import refresh_ipo_companies
from app.startup_hub.private_fetcher import refresh_private_opportunities
from app.startup_hub.public_fetcher import refresh_public_companies


async def _with_session(callback, db: AsyncSession | None):
    if db is not None:
        return await callback(db)
    async with async_session() as session:
        return await callback(session)


async def refresh_public_data(db: AsyncSession | None = None, *, force_refresh: bool = True) -> dict[str, Any]:
    async def _run(session: AsyncSession) -> dict[str, Any]:
        results = await refresh_public_companies(db=session, force_refresh=force_refresh)
        return {
            "entity_type": "public_stock",
            "count": len(results),
            "items": results,
        }

    return await _with_session(_run, db)


async def refresh_ipo_data(db: AsyncSession | None = None, *, force_refresh: bool = True) -> dict[str, Any]:
    async def _run(session: AsyncSession) -> dict[str, Any]:
        results = await refresh_ipo_companies(db=session, force_refresh=force_refresh)
        return {
            "entity_type": "ipo_watch",
            "count": len(results),
            "items": results,
        }

    return await _with_session(_run, db)


async def refresh_private_data(db: AsyncSession | None = None, *, force_refresh: bool = True) -> dict[str, Any]:
    async def _run(session: AsyncSession) -> dict[str, Any]:
        results = await refresh_private_opportunities(db=session, force_refresh=force_refresh)
        return {
            "entity_type": "private_opportunity",
            "count": len(results),
            "items": results,
        }

    return await _with_session(_run, db)


async def seed_startup_hub_data(db: AsyncSession | None = None) -> dict[str, Any]:
    async def _run(session: AsyncSession) -> dict[str, Any]:
        public_result = await refresh_public_data(session, force_refresh=True)
        ipo_result = await refresh_ipo_data(session, force_refresh=True)
        private_result = await refresh_private_data(session, force_refresh=True)
        invalidated = invalidate_cache()
        return {
            "status": "seeded",
            "public": public_result,
            "ipos": ipo_result,
            "private": private_result,
            "cache_invalidated_entries": invalidated,
        }

    return await _with_session(_run, db)


async def refresh_startup_hub_data(db: AsyncSession | None = None) -> dict[str, Any]:
    async def _run(session: AsyncSession) -> dict[str, Any]:
        public_result = await refresh_public_data(session, force_refresh=True)
        ipo_result = await refresh_ipo_data(session, force_refresh=True)
        private_result = await refresh_private_data(session, force_refresh=True)
        invalidated = invalidate_cache()
        return {
            "status": "refreshed",
            "public": public_result,
            "ipos": ipo_result,
            "private": private_result,
            "cache_invalidated_entries": invalidated,
        }

    return await _with_session(_run, db)


async def recompute_all_rankings(db: AsyncSession | None = None) -> dict[str, Any]:
    async def _run(session: AsyncSession) -> dict[str, Any]:
        public_result = await refresh_public_data(session, force_refresh=True)
        ipo_result = await refresh_ipo_data(session, force_refresh=True)
        private_result = await refresh_private_data(session, force_refresh=True)
        invalidated = invalidate_cache()
        return {
            "status": "recomputed",
            "note": "Rankings are recomputed during each entity refresh snapshot build.",
            "public": public_result,
            "ipos": ipo_result,
            "private": private_result,
            "cache_invalidated_entries": invalidated,
        }

    return await _with_session(_run, db)

