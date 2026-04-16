import asyncio
import os

from app.cache import clear_expired, get_cached_entry, set_cached
from app.services.analysis_fast import run_fast_analysis
from app.tickers import PRIORITY, REMAINING_TOP_100

_IN_FLIGHT: set[str] = set()
_IN_FLIGHT_LOCK = asyncio.Lock()


async def warm_ticker(ticker: str, force: bool = False) -> dict | None:
    normalized = (ticker or "").strip().upper()
    if not normalized:
        return None

    if not force:
        cached_entry = get_cached_entry(normalized)
        if cached_entry is not None and not cached_entry["stale"]:
            return cached_entry["data"]

    async with _IN_FLIGHT_LOCK:
        if normalized in _IN_FLIGHT:
            return None
        _IN_FLIGHT.add(normalized)

    try:
        result = await run_fast_analysis(normalized)
        set_cached(normalized, result)
        return result
    except Exception as exc:
        print(f"[PRECOMPUTE ERROR] {normalized}: {exc}")
        return None
    finally:
        async with _IN_FLIGHT_LOCK:
            _IN_FLIGHT.discard(normalized)


def trigger_compute(ticker: str) -> None:
    normalized = (ticker or "").strip().upper()
    if not normalized:
        return
    asyncio.create_task(warm_ticker(normalized))


def _refresh_seconds() -> int:
    try:
        configured = int(os.getenv("ANALYSIS_PRECOMPUTE_INTERVAL_SECONDS", "60") or "60")
    except Exception:
        configured = 60
    return max(30, configured)


def _concurrency() -> int:
    try:
        configured = int(os.getenv("ANALYSIS_PRECOMPUTE_CONCURRENCY", "10") or "10")
    except Exception:
        configured = 10
    return max(1, configured)


async def _warm_many(tickers: list[str], force: bool = False) -> dict[str, bool]:
    results: dict[str, bool] = {}
    batch_size = _concurrency()

    async def _warm_one(ticker: str) -> tuple[str, bool]:
        result = await warm_ticker(ticker, force=force)
        return ticker, result is not None

    for start in range(0, len(tickers), batch_size):
        batch = tickers[start:start + batch_size]
        batch_results = await asyncio.gather(*[_warm_one(ticker) for ticker in batch])
        for ticker, success in batch_results:
            results[ticker] = success
    return results


async def warm_startup_cache() -> dict[str, bool]:
    clear_expired()
    results = await _warm_many(PRIORITY, force=False)
    background_results = await _warm_many(REMAINING_TOP_100, force=False)
    results.update(background_results)
    warmed = sum(1 for success in results.values() if success)
    print(f"[CACHE WARM STARTUP] warmed={warmed} total={len(results)}")
    return results


async def precompute_loop() -> None:
    refresh_seconds = _refresh_seconds()

    # Startup warm handles the initial fill. Background loop force-refreshes the
    # full popular set before entries expire so common tickers stay hot.
    await asyncio.sleep(refresh_seconds)

    while True:
        clear_expired()
        await _warm_many(PRIORITY, force=True)
        await _warm_many(REMAINING_TOP_100, force=True)
        await asyncio.sleep(refresh_seconds)
