import asyncio

from app.dynamic_fetcher import fetch_historical_data
from app.search import get_company_news


async def fetch_parallel(ticker: str, include_news: bool = False) -> dict:
    normalized = (ticker or "").strip().upper()
    if not normalized:
        return {
            "ticker": "",
            "company_name": "",
            "historical_data": [],
            "search_results": [],
        }

    history_task = asyncio.create_task(fetch_historical_data(normalized))
    news_task = None
    if include_news:
        news_task = asyncio.create_task(asyncio.to_thread(get_company_news, normalized, 2))

    history_result = await history_task
    if news_task is not None:
        search_results = await news_task
    else:
        search_results = []

    if not history_result:
        return {
            "ticker": normalized,
            "company_name": normalized,
            "historical_data": [],
            "search_results": search_results,
        }

    company_name, historical_data = history_result
    return {
        "ticker": normalized,
        "company_name": company_name or normalized,
        "historical_data": historical_data or [],
        "search_results": search_results,
    }
