"""Benchmark orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from dbsorting.engines import Engine


def benchmark(df: pd.DataFrame, db_dir: Path, engines: Iterable[Engine]) -> None:
    """Execute setup and query for each engine and print timings."""

    db_dir.mkdir(parents=True, exist_ok=True)

    for engine in engines:
        print(f"\n--- {engine.name} ---")
        db_path = db_dir / f"{engine.name}.db"
        write_seconds = engine.setup(df, db_path)
        result, query_seconds = engine.query(db_path)
        print(
            f"Loaded {len(df):,} rows into {db_path} in {write_seconds:.2f}s; "
            f"query returned {len(result):,} rows in {query_seconds:.2f}s"
        )
