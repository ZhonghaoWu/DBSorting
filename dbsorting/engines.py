"""Engine-specific IO and query helpers."""

from __future__ import annotations

import importlib.util
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Tuple

import pandas as pd


@dataclass
class Engine:
    """Bundle write and read operations for a storage engine."""

    name: str
    setup: Callable[[pd.DataFrame, Path], float]
    query: Callable[[Path], Tuple[pd.DataFrame, float]]


def _load_duckdb():
    if importlib.util.find_spec("duckdb") is None:
        raise RuntimeError("duckdb is not installed; install with `pip install duckdb`.")
    import importlib

    return importlib.import_module("duckdb")


def setup_sqlite(df: pd.DataFrame, db_path: Path) -> float:
    """Write data to SQLite and return seconds elapsed."""

    start = time.perf_counter()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prices (
                symbol TEXT NOT NULL,
                ts TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER
            )
            """
        )
        conn.execute("DELETE FROM prices")
        df.to_sql("prices", conn, if_exists="append", index=False)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_prices_symbol_ts ON prices(symbol, ts)")
        conn.commit()
    finally:
        conn.close()
    return time.perf_counter() - start


def query_sqlite(db_path: Path) -> Tuple[pd.DataFrame, float]:
    """Run an aggregate query in SQLite and return (result, seconds)."""

    start = time.perf_counter()
    conn = sqlite3.connect(db_path)
    try:
        result = pd.read_sql(
            """
            SELECT
                symbol,
                substr(ts, 1, 10) AS day,
                avg(close) AS avg_close,
                sum(volume) AS total_volume
            FROM prices
            GROUP BY symbol, day
            ORDER BY symbol, day
            """,
            conn,
        )
    finally:
        conn.close()
    return result, time.perf_counter() - start


def setup_duckdb(df: pd.DataFrame, db_path: Path) -> float:
    """Write data to DuckDB and return seconds elapsed."""

    duckdb = _load_duckdb()

    start = time.perf_counter()
    con = duckdb.connect(str(db_path))
    try:
        con.execute("DROP TABLE IF EXISTS prices")
        con.execute("CREATE TABLE prices AS SELECT * FROM df")
        con.execute("CREATE INDEX IF NOT EXISTS idx_prices_symbol_ts ON prices(symbol, ts)")
    finally:
        con.close()
    return time.perf_counter() - start


def query_duckdb(db_path: Path) -> Tuple[pd.DataFrame, float]:
    """Run an aggregate query in DuckDB and return (result, seconds)."""

    duckdb = _load_duckdb()

    start = time.perf_counter()
    con = duckdb.connect(str(db_path))
    try:
        result = con.execute(
            """
            SELECT
                symbol,
                DATE(ts) AS day,
                AVG(close) AS avg_close,
                SUM(volume) AS total_volume
            FROM prices
            GROUP BY symbol, day
            ORDER BY symbol, day
            """
        ).fetch_df()
    finally:
        con.close()
    return result, time.perf_counter() - start


def available_engines(include_duckdb: bool = True) -> list[Engine]:
    engines = [Engine(name="sqlite", setup=setup_sqlite, query=query_sqlite)]

    if include_duckdb and importlib.util.find_spec("duckdb") is not None:
        engines.append(Engine(name="duckdb", setup=setup_duckdb, query=query_duckdb))

    return engines
