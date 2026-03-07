---
name: optout-merge
description: "Default opt-out column handling for external dataset joins/merges. Use when merging external tables, files, or lookup datasets into a dataset and you must preserve all columns unless explicitly excluded. Triggers: join/merge steps, enrichment, ETL/ELT, lookup table integration, data integration work."
---

# Optout Merge

## Overview
Preserve all columns by default when merging external datasets; only drop explicitly listed helper columns. Prefer opt-out over opt-in column lists to avoid accidental data loss.

## Workflow
1) Normalize join keys and types on both sides.
2) Join without column selection on the right side.
3) Define `exclude_cols` for temporary/helper fields only, then drop.
4) If a canonical order is required, place canonical columns first and append the rest.

## Patterns

### Polars (LazyFrame or DataFrame)
```python
joined = left.join(right, on=keys, how="left", suffix="_r")
if isinstance(joined, pl.LazyFrame):
    schema_names = joined.collect_schema().names()
else:
    schema_names = list(joined.columns)
exclude_cols = ["tmp_col"]
keep_cols = [c for c in schema_names if c not in exclude_cols]
joined = joined.select(keep_cols)
```

### Pandas
```python
joined = left.merge(right, on=keys, how="left", suffixes=("", "_r"))
exclude_cols = ["tmp_col"]
joined = joined[[c for c in joined.columns if c not in exclude_cols]]
```

## Duplicate Column Resolution
- Prefer renaming before the join or use suffixes, then coalesce or drop only the unwanted duplicates.
