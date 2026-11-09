"""Pure analysis functions - no network calls in this file at all. Every
function here takes data that's already been fetched (a DataFrame, or the
raw list of dicts CoinGecko returns) and returns a new DataFrame. That split
is what makes tests/test_analysis.py possible without hitting the network:
it feeds these functions a static fixture instead of a live API response.
"""

from __future__ import annotations

import pandas as pd

# The subset of CoinGecko's response we actually use, renamed to something
# readable. Anything not listed here is dropped when building the
# DataFrame - we don't need ath_date, roi, image URLs, etc. for this.
_COLUMNS = {
    "id": "id",
    "symbol": "symbol",
    "name": "name",
    "current_price": "price",
    "market_cap": "market_cap",
    "market_cap_rank": "rank",
    "total_volume": "volume_24h",
    "high_24h": "high_24h",
    "low_24h": "low_24h",
    "price_change_percentage_24h": "change_24h_pct",
}


def to_dataframe(raw_coins: list[dict]) -> pd.DataFrame:
    """Converts CoinGecko's raw list-of-dicts response into a DataFrame with
    just the columns this project uses, renamed for readability. Coins
    missing a field we need (CoinGecko returns null for some of the more
    obscure ones) get dropped rather than silently treated as 0 - a missing
    24h change shouldn't be mistaken for "unchanged".
    """
    df = pd.DataFrame(raw_coins)
    missing = [col for col in _COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Response is missing expected columns: {missing}")

    df = df[list(_COLUMNS.keys())].rename(columns=_COLUMNS)
    required_for_analysis = ["price", "market_cap", "volume_24h", "high_24h", "low_24h", "change_24h_pct"]
    return df.dropna(subset=required_for_analysis).reset_index(drop=True)


def top_gainers(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """The n coins with the largest positive 24h price change."""
    return df.sort_values("change_24h_pct", ascending=False).head(n).reset_index(drop=True)


def top_losers(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """The n coins with the largest negative 24h price change."""
    return df.sort_values("change_24h_pct", ascending=True).head(n).reset_index(drop=True)


def intraday_volatility(df: pd.DataFrame) -> pd.DataFrame:
    """Adds intraday_range_pct = (24h high - 24h low) / current price, as a
    percentage. This is a volatility proxy, not a textbook one (realized
    volatility would need a time series of prices, which the /coins/markets
    snapshot doesn't give us) - it answers "how much did this swing today
    relative to its price", which is close enough for a portfolio project
    and doesn't need a second API call per coin.
    """
    out = df.copy()
    out["intraday_range_pct"] = (out["high_24h"] - out["low_24h"]) / out["price"] * 100
    return out.sort_values("intraday_range_pct", ascending=False).reset_index(drop=True)


def liquidity_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """Adds volume_to_mcap = 24h trading volume / market cap. A coin with a
    tiny ratio trades rarely relative to its size - useful as a rough "how
    easily could you actually buy/sell this" signal, distinct from just
    looking at market cap or volume alone.
    """
    out = df.copy()
    out["volume_to_mcap"] = out["volume_24h"] / out["market_cap"]
    return out.sort_values("volume_to_mcap", ascending=False).reset_index(drop=True)


def market_cap_concentration(df: pd.DataFrame, top_n: int = 10) -> float:
    """What fraction of the TOTAL MARKET CAP IN THIS FETCHED SET the top_n
    coins by market cap account for. Deliberately not a claim about the
    whole crypto market - only about however many coins were fetched (the
    CLI's --per-page controls that), since that's all this process ever
    saw.
    """
    if df.empty:
        return 0.0
    ranked = df.sort_values("market_cap", ascending=False)
    total = ranked["market_cap"].sum()
    if total == 0:
        return 0.0
    return float(ranked.head(top_n)["market_cap"].sum() / total)
