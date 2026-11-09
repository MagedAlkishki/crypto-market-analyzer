"""Turns analysis DataFrames into things a human reads: a plain-text
console summary, and an optional bar chart image. Kept separate from
analysis.py so the analysis functions stay testable as pure data
transforms, with no formatting or matplotlib concerns mixed in.
"""

from __future__ import annotations

import pandas as pd


def format_summary(
    gainers: pd.DataFrame,
    losers: pd.DataFrame,
    volatility: pd.DataFrame,
    liquidity: pd.DataFrame,
    concentration: float,
    top_n: int,
) -> str:
    lines: list[str] = []
    lines.append(f"Top {len(gainers)} gainers (24h)")
    for _, row in gainers.iterrows():
        lines.append(f"  {row['symbol'].upper():<6} {row['change_24h_pct']:+.2f}%   ${row['price']:,.4f}")

    lines.append("")
    lines.append(f"Top {len(losers)} losers (24h)")
    for _, row in losers.iterrows():
        lines.append(f"  {row['symbol'].upper():<6} {row['change_24h_pct']:+.2f}%   ${row['price']:,.4f}")

    lines.append("")
    lines.append(f"Most volatile intraday (high/low spread vs. price)")
    for _, row in volatility.head(5).iterrows():
        lines.append(f"  {row['symbol'].upper():<6} {row['intraday_range_pct']:.2f}% range")

    lines.append("")
    lines.append("Most liquid relative to size (24h volume / market cap)")
    for _, row in liquidity.head(5).iterrows():
        lines.append(f"  {row['symbol'].upper():<6} {row['volume_to_mcap']:.3f}")

    lines.append("")
    lines.append(
        f"Top {top_n} coins by market cap account for "
        f"{concentration * 100:.1f}% of this fetched set's total market cap."
    )

    return "\n".join(lines)


def save_movers_chart(gainers: pd.DataFrame, losers: pd.DataFrame, output_path: str) -> None:
    """Saves a horizontal bar chart of top gainers (green) vs. top losers
    (red) to output_path. Imports matplotlib lazily so the rest of the
    package - and its tests - don't need a display backend or matplotlib
    installed just to run the analysis functions.
    """
    import matplotlib

    matplotlib.use("Agg")  # headless: never tries to open a GUI window
    import matplotlib.pyplot as plt

    combined = pd.concat([gainers, losers]).sort_values("change_24h_pct")
    colors = ["#e74c3c" if v < 0 else "#2ecc71" for v in combined["change_24h_pct"]]

    fig, ax = plt.subplots(figsize=(8, max(4, len(combined) * 0.35)))
    ax.barh(combined["symbol"].str.upper(), combined["change_24h_pct"], color=colors)
    ax.set_xlabel("24h change (%)")
    ax.set_title("Top movers (24h)")
    ax.axvline(0, color="#888888", linewidth=0.8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
