---
name: paimon
description: Apache Paimon streaming lake format expertise for real-time ingestion and lakehouse architectures. Use when the user mentions Paimon, streaming lakehouse, primary-key tables, changelog, Flink CDC into a lake, Paimon Materialized Tables, PyPaimon, deletion vectors, lookup joins, buckets, compaction, or Spark/Flink Paimon tables.
---

# Apache Paimon Expert

Use this skill for Paimon table design, Flink-native streaming ingestion, changelog semantics, compaction, lookup joins, Spark reads, and Iceberg compatibility.

## Current Facts

- **Current stable Paimon:** 1.4.1. A 1.4.2 release candidate exists; do not recommend it as stable unless the user explicitly wants RC testing.
- **PyPaimon:** 1.4.1 on PyPI, pure Python package.
- **Flink CDC:** 3.6.0 is the current CDC line; older 3.5 examples remain useful but should not be described as latest.
- **Recommended Flink:** Flink 1.20.x or 2.2.x for new work when connector compatibility allows.
- **Recommended Spark:** verify against the Paimon connector matrix for the selected Paimon version; do not hard-code Spark 3.4.3 for new projects without checking.
- **Recent focus areas:** PyPaimon, data evolution, Iceberg compatibility, deletion vectors, REST Catalog authorization interfaces, lookup join performance, multimodal/blob storage, and Paimon/Lance integration work.

## How To Use

1. Determine table type first: append-only table or primary-key table.
2. Determine workload: streaming ingest, CDC upsert, lookup dimension table, batch analytics, or cross-format Iceberg exposure.
3. Choose bucket strategy early; bucket count affects write parallelism, small files, and lookup performance.
4. For deeper SQL/API examples and operational patterns, consult [full-reference.md](references/full-reference.md). Treat older version values there as historical if they conflict with this file.

## Design Rules

- Use primary-key tables for upserts, deletes, and CDC; use append-only tables for immutable event logs.
- Include partition fields in primary keys when tables are partitioned.
- Avoid single-bucket defaults for large tables; choose fixed or dynamic buckets deliberately.
- Use changelog producer settings based on downstream needs: `input`, `lookup`, `full-compaction`, or none.
- Plan compaction separately from ingestion for high-volume streaming tables.
- Use lookup cache only when dimension-table size and freshness requirements justify it.

## Update Checklist

- Recheck Apache Paimon tags/downloads and PyPI `pypaimon` before changing versions.
- Recheck Flink CDC compatibility for the selected Flink and Paimon releases.
- Keep this `SKILL.md` concise; move long DDL and migration examples to `references/`.
