"""Talks to CoinGecko's public REST API. Kept deliberately separate from
analysis.py: the analysis functions take a plain list of dicts (or a
DataFrame) as input, so they can be tested against a static fixture without
ever touching the network - see tests/test_analysis.py.
"""

from __future__ import annotations

import requests

COINGECKO_MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"

# A real request timeout, not "wait forever" - a hung network call
# shouldn't make the CLI look frozen.
DEFAULT_TIMEOUT_SECONDS = 10


class CoinGeckoError(RuntimeError):
    """Raised when the CoinGecko API can't be reached or returns something
    we didn't ask for (e.g. an error body instead of a list of coins)."""


def fetch_market_data(
    vs_currency: str = "usd",
    per_page: int = 100,
    page: int = 1,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> list[dict]:
    """Fetches one page of coins ranked by market cap, with current price,
    24h high/low, 24h % change, volume and market cap already included -
    everything analysis.py needs, in a single request. No API key required.
    """
    params = {
        "vs_currency": vs_currency,
        "order": "market_cap_desc",
        "per_page": per_page,
        "page": page,
        # price_change_percentage defaults to 24h already, but asking
        # explicitly documents the intent rather than relying on a default
        # that could change.
        "price_change_percentage": "24h",
    }

    try:
        response = requests.get(COINGECKO_MARKETS_URL, params=params, timeout=timeout)
    except requests.RequestException as e:
        raise CoinGeckoError(f"Couldn't reach CoinGecko: {e}") from e

    if response.status_code == 429:
        raise CoinGeckoError(
            "CoinGecko rate-limited this request (its free tier is capped "
            "per minute) - wait a bit and try again."
        )
    if not response.ok:
        raise CoinGeckoError(
            f"CoinGecko returned {response.status_code}: {response.text[:200]}"
        )

    data = response.json()
    if not isinstance(data, list):
        raise CoinGeckoError(f"Expected a list of coins, got: {type(data).__name__}")

    return data
