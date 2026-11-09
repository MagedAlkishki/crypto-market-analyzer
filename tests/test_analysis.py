"""Tests run entirely against tests/fixtures/sample_markets.json - a static,
hand-written sample shaped like a real CoinGecko /coins/markets response
(clearly fictional data: "Some Small Coin", "Crashing Coin", etc., not real
market data pulled at some point and left to go stale). No network call
happens anywhere in this file, which is the point of keeping fetch.py
separate from analysis.py.
"""

import json
from pathlib import Path

import pytest

from crypto_analyzer.analysis import (
    intraday_volatility,
    liquidity_ratio,
    market_cap_concentration,
    to_dataframe,
    top_gainers,
    top_losers,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_markets.json"


@pytest.fixture
def raw_coins():
    return json.loads(FIXTURE_PATH.read_text())


@pytest.fixture
def df(raw_coins):
    return to_dataframe(raw_coins)


def test_to_dataframe_drops_coins_missing_required_fields(df):
    # "missing-data-coin" has nulls for market_cap/high_24h/low_24h/change -
    # it should be dropped rather than silently coerced to 0, which would
    # make a coin with genuinely unknown data look like a perfectly flat,
    # zero-cap coin.
    assert "missing-data-coin" not in df["id"].values
    assert len(df) == 5


def test_to_dataframe_renames_columns(df):
    expected = {"id", "symbol", "name", "price", "market_cap", "rank", "volume_24h", "high_24h", "low_24h", "change_24h_pct"}
    assert expected.issubset(set(df.columns))


def test_top_gainers_orders_by_change_descending(df):
    gainers = top_gainers(df, n=3)
    assert list(gainers["id"]) == ["some-small-coin", "bitcoin", "stablecoin-example"]


def test_top_losers_orders_by_change_ascending(df):
    losers = top_losers(df, n=2)
    assert list(losers["id"]) == ["crashing-coin", "ethereum"]


def test_top_gainers_respects_n(df):
    assert len(top_gainers(df, n=2)) == 2


def test_intraday_volatility_ranks_widest_swing_first(df):
    vol = intraday_volatility(df)
    # crashing-coin: (0.0025 - 0.0009) / 0.001 = 160% - by far the widest
    # swing relative to its own price, so it should be first.
    assert vol.iloc[0]["id"] == "crashing-coin"
    assert vol.iloc[0]["intraday_range_pct"] == pytest.approx(160.0, rel=1e-3)


def test_liquidity_ratio_flags_the_stablecoin_as_most_liquid(df):
    # stablecoin-example trades 60B volume against a 95B market cap -
    # the highest volume/market-cap ratio in the fixture by a wide margin.
    liq = liquidity_ratio(df)
    assert liq.iloc[0]["id"] == "stablecoin-example"


def test_market_cap_concentration_is_fraction_of_fetched_set_only(df):
    # Top 2 by market cap here are bitcoin (1.18T) and stablecoin-example
    # (95B) against a fetched-set total of roughly 1.574T.
    concentration = market_cap_concentration(df, top_n=2)
    assert 0.0 < concentration <= 1.0
    # Sanity check against a hand-computed value rather than just
    # "it's between 0 and 1" - bitcoin alone is already ~75% of this set.
    assert concentration > 0.75


def test_market_cap_concentration_handles_empty_dataframe():
    import pandas as pd

    empty = pd.DataFrame(columns=["market_cap"])
    assert market_cap_concentration(empty) == 0.0
