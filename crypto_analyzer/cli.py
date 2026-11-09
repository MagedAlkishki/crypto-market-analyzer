"""Entry point: `python -m crypto_analyzer`. Wires fetch -> analysis ->
report together; argument parsing and I/O live here so the other modules
stay free of CLI concerns.
"""

from __future__ import annotations

import argparse
import sys

from crypto_analyzer.analysis import (
    intraday_volatility,
    liquidity_ratio,
    market_cap_concentration,
    to_dataframe,
    top_gainers,
    top_losers,
)
from crypto_analyzer.fetch import CoinGeckoError, fetch_market_data
from crypto_analyzer.report import format_summary, save_movers_chart


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crypto-analyzer",
        description="Pulls live market data from CoinGecko's public API and reports top movers, volatility and liquidity.",
    )
    parser.add_argument(
        "--currency", default="usd", help="Currency to price coins in (default: usd)"
    )
    parser.add_argument(
        "--coins", type=int, default=100, help="How many coins to fetch, ranked by market cap (default: 100)"
    )
    parser.add_argument(
        "--top", type=int, default=10, help="How many gainers/losers/top-cap coins to show (default: 10)"
    )
    parser.add_argument(
        "--chart", metavar="PATH", help="Also save a top-movers bar chart as a PNG to this path"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        raw = fetch_market_data(vs_currency=args.currency, per_page=args.coins)
    except CoinGeckoError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    df = to_dataframe(raw)
    if df.empty:
        print("No usable coin data came back - nothing to analyze.", file=sys.stderr)
        return 1

    gainers = top_gainers(df, args.top)
    losers = top_losers(df, args.top)
    volatility = intraday_volatility(df)
    liquidity = liquidity_ratio(df)
    concentration = market_cap_concentration(df, args.top)

    print(format_summary(gainers, losers, volatility, liquidity, concentration, args.top))

    if args.chart:
        save_movers_chart(gainers, losers, args.chart)
        print(f"\nChart saved to {args.chart}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
