# Crypto Market Analyzer

A command-line tool that pulls live market data from [CoinGecko's](https://www.coingecko.com/en/api) public API (no API key required) and runs real analysis on it: top 24h gainers/losers, intraday volatility, liquidity relative to market cap, and market-cap concentration — not just a dump of raw numbers.

## Why this exists

My other projects model a specific rule or domain correctly (VCT roster rules, library due dates, consent-gated data access). This one is the same idea applied to data analysis instead of business logic: given a live, messy, real-world API response, compute something genuinely useful from it, with the analysis code tested independently of the network call that feeds it.

## What it computes

Given the current top N coins by market cap:

- **Top gainers / losers** — ranked by 24h price change.
- **Intraday volatility** — `(24h high − 24h low) / current price`, as a percentage. This is a proxy, not textbook realized volatility (that needs a time series of prices; CoinGecko's markets snapshot only gives today's high/low), but it's a real "how much did this swing today" signal computable from a single request.
- **Liquidity ratio** — `24h volume / market cap`. A coin with a tiny ratio trades rarely relative to its size, which matters more than market cap alone if you actually want to buy or sell it.
- **Market-cap concentration** — what fraction of the *fetched set's* total market cap the top N coins account for. Deliberately scoped to "of what this run fetched," not a claim about the entire crypto market.

## Running it

```bash
pip install -r requirements.txt
python -m crypto_analyzer --top 10 --chart movers.png
```

Options:

| Flag | Default | Meaning |
|---|---|---|
| `--currency` | `usd` | Currency to price coins in |
| `--coins` | `100` | How many coins to fetch, ranked by market cap |
| `--top` | `10` | How many gainers/losers/top-cap coins to show |
| `--chart PATH` | — | Also save a top-movers bar chart (PNG) |

## Design

```
crypto_analyzer/
  fetch.py      # the only file that talks to the network
  analysis.py   # pure functions: DataFrame in, DataFrame out, no I/O
  report.py     # formats analysis results as text / a chart
  cli.py        # argument parsing, wires the above together
```

`fetch.py` is kept separate from `analysis.py` on purpose: the analysis functions never call the network themselves, so `tests/test_analysis.py` can feed them a static fixture (`tests/fixtures/sample_markets.json` — hand-written, clearly fictional coins, not a stale copy of real market data) and check the math without CoinGecko's rate limits or uptime being part of the test suite.

## Tests

```bash
pytest tests/ -v
```

9 tests, covering the analysis math itself (correct ranking, correct volatility/liquidity formulas) and an edge case CoinGecko's real data actually has: some coins come back with `null` fields, which get dropped rather than silently treated as zero.

## Notes

- No API key needed — CoinGecko's `/coins/markets` endpoint is open.
- The free tier is rate-limited; `fetch.py` surfaces a clear error if you hit it, rather than letting a raw `requests` exception or an unhandled 429 bubble up.
- Not financial advice, and not trying to be — this is a data-analysis exercise, not a trading signal generator.
