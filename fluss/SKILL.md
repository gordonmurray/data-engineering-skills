---
name: fluss
description: Apache Fluss Incubating streaming storage expertise for real-time analytics, streamhouse and lakehouse architectures. Use when the user mentions Fluss, streaming storage, columnar streams, sub-second ingestion, tiered storage, Flink Delta Join, Paimon/Iceberg/Lance tiering, Spark access to streams, or Fluss table design.
---

# Apache Fluss Expert

Use this skill for Fluss table design, low-latency stream storage, Flink integration, tiering to lakehouse formats, and operational planning.

## Current Facts

- **Current stable:** Apache Fluss 0.9.1.
- **Status:** Apache Incubator project. Incubating releases are not yet fully endorsed ASF products.
- **Important 0.9 line features:** Spark integration, complex nested types, zero-copy schema evolution, aggregation merge engine, auto-increment dictionary tables, `$changelog` and `$binlog` virtual tables, compacted log format, dynamic sink shuffle, KV snapshot leases, cluster rebalance, Azure Blob/ADLS Gen2 support, and Java Client POJO support.
- **Clients:** Fluss Rust, Python, and C++ client 0.1.0 has been announced; do not describe Python SDK as only future roadmap.
- **Flink CDC:** use current Flink CDC 3.6.0 guidance unless working in a pinned 3.5 environment.
- **Docker examples:** prefer `fluss/fluss:0.9.1` for current stable examples.

## How To Use

1. Determine whether the table should be a log table or primary-key table.
2. Determine hot/cold architecture: Fluss only, Fluss tiered to Paimon, Fluss tiered to Iceberg, or Lance-oriented AI/vector ingestion.
3. For Flink jobs, align Fluss connector, Flink version, and CDC version before writing examples.
4. For deeper SQL/YAML examples and operational notes, consult [full-reference.md](references/full-reference.md). Treat older version values there as historical if they conflict with this file.

## Design Rules

- Use Fluss for hot, sub-second stream/table access; use Paimon/Iceberg for cold historical lakehouse storage.
- Use log tables for append-only events and primary-key tables for mutable keyed state or CDC.
- Size buckets for parallelism and avoid unnecessary small-file/tablet overhead.
- Use `$changelog`/`$binlog` virtual tables for audit, replay, CDC, and ML reproducibility scenarios.
- Use aggregation merge engine when pushing high-cardinality aggregate state into storage simplifies Flink state.

## Update Checklist

- Recheck Fluss downloads before changing stable versions.
- Recheck client SDK maturity before recommending Python/C++/Rust client use in production.
- Keep this `SKILL.md` concise; move long examples to `references/`.
