# DBSorting

Comparison of SQLite and DuckDB for medium-sized time-series data (e.g., hundreds or thousands of symbols with 5-day, 1-minute OHLCV data from Yahoo Finance). The focus is on setup, querying speed, Python integration, and disk usage.

## Quick comparison

| Area | SQLite | DuckDB |
| --- | --- | --- |
| Setup & ergonomics | Embedded binary available via system packages or `pip install pysqlite3-binary`; no server to manage. Schema definitions needed to enforce types; CSV import via `sqlite3` CLI or `pandas.to_sql`. | Single self-contained binary or `pip install duckdb`; no server. Built-in `read_csv_auto`, Parquet support, and direct Pandas/Arrow imports reduce schema boilerplate. |
| Querying speed (analytical workloads) | Row-oriented engine; adequate for narrow point lookups or small aggregates. Complex analytics (window functions, joins across many symbols) slow once data exceeds RAM; limited parallelism. | Columnar execution with vectorization and automatic parallelism; strong at scans, joins, and windowed analytics. Typical 5-day, per-minute OHLCV aggregates across 1k symbols run several times faster than SQLite on the same hardware. |
| Python integration | Stable `sqlite3` stdlib driver; works anywhere Python runs. Limited type fidelity (no native Arrow); relies on Pandas conversions. Extensions for FTS/json require build flags. | Official `duckdb` Python package exposes DataFrame/Arrow-native queries, `register` for lazy tables, and `sql`/`execute` returning Arrow or Pandas directly. Works in notebooks and scripts without extra servers. |
| Disk usage | Stores pages in row format; indexes can grow quickly for wide tables. 5-day, 1-minute OHLCV for ~1k symbols typically tens to ~100 MB without compression; no built-in columnar compression. | Columnar storage with compression (e.g., Parquet) keeps footprints smaller; same dataset often ~30–60% of SQLite size. External Parquet files can be queried in-place, avoiding duplication. |
| Concurrency & durability | ACID with WAL; good for single-writer, few-reader workflows. Parallel analytical reads limited. | Single-process embedded with MVCC; concurrent writers limited, but parallel read/compute is strong. Suitable for read-mostly analytical use. |
| When to choose | Simple deployments, tiny footprints, or when SQLite portability/ubiquity matters more than speed. | Fast exploratory analytics, heavy aggregations across many symbols, and seamless DataFrame/Arrow interoperability. |

## Project layout

- `dbsorting/data.py`: synthetic OHLCV generator used by the benchmarks.
- `dbsorting/engines.py`: engine-specific setup/query helpers plus discovery of available engines.
- `dbsorting/benchmark.py`: orchestrates writing/querying for each engine and reports timings.
- `dbsorting/cli.py`: argument parsing and the `main()` entry point.
- `compare_engines.py`: thin wrapper to run `dbsorting.cli.main()` for script-style execution.

## Runnable benchmark example

The benchmark generates synthetic 1-minute OHLCV data (no network calls) and times writes plus a representative aggregate query on each engine.

```bash
pip install duckdb pandas numpy  # sqlite3 is in the stdlib
python compare_engines.py --symbols 300 --days 5 --db-dir ./artifacts --duckdb
```

The script reports how long each engine took to load the generated dataset and compute daily average closes and total volumes per symbol, writing separate `sqlite.db` and `duckdb.db` files in the target directory. Pass `--duckdb` to include DuckDB (skipped if the package is missing).
