"""Command-line entry point for benchmarking."""

from __future__ import annotations

import argparse
from pathlib import Path

from dbsorting.benchmark import benchmark
from dbsorting.data import generate_ohlcv
from dbsorting.engines import available_engines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark SQLite vs DuckDB for OHLCV data.")
    parser.add_argument("--symbols", type=int, default=200, help="Number of symbols to generate.")
    parser.add_argument("--days", type=int, default=5, help="Number of trading days (1-minute bars).")
    parser.add_argument("--db-dir", type=Path, default=Path("./artifacts"), help="Where to place db files.")
    parser.add_argument("--duckdb", action="store_true", help="Include DuckDB in the benchmark if installed.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"Generating synthetic data for {args.symbols} symbols over {args.days} day(s)...")
    df = generate_ohlcv(symbols=args.symbols, days=args.days)
    print(f"Generated {len(df):,} rows; starting benchmarks.")

    engines = available_engines(include_duckdb=args.duckdb)
    if not engines:
        raise RuntimeError("No engines available. Install sqlite3/duckdb Python bindings.")

    if args.duckdb and len(engines) == 1:
        print("duckdb package not installed; skipping DuckDB benchmark.")

    benchmark(df, args.db_dir, engines)


if __name__ == "__main__":
    main()
