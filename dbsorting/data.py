"""Synthetic OHLCV data generation helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate_ohlcv(symbols: int, days: int, *, seed: int = 42) -> pd.DataFrame:
    """Create synthetic 1-minute OHLCV data for the given symbol count and days.

    The output matches a common OHLCV schema: symbol, ts, open, high, low, close,
    and volume. Prices follow a simple random walk so downstream aggregates behave
    realistically enough for performance checks.
    """

    minutes_per_day = 60 * 24
    ts_index = pd.date_range("2024-01-01", periods=minutes_per_day * days, freq="1min")

    rng = np.random.default_rng(seed=seed)
    base_prices = rng.normal(100, 1, size=symbols)

    frames = []
    for idx in range(symbols):
        deltas = rng.normal(0, 0.2, size=len(ts_index))
        prices = base_prices[idx] + np.cumsum(deltas)
        highs = prices + rng.uniform(0.01, 0.5, size=len(ts_index))
        lows = prices - rng.uniform(0.01, 0.5, size=len(ts_index))
        volumes = rng.integers(1_000, 5_000, size=len(ts_index))

        df = pd.DataFrame(
            {
                "symbol": f"SYM{idx:04d}",
                "ts": ts_index,
                "open": prices,
                "high": highs,
                "low": lows,
                "close": prices + rng.normal(0, 0.05, size=len(ts_index)),
                "volume": volumes,
            }
        )
        frames.append(df)

    return pd.concat(frames, ignore_index=True)
