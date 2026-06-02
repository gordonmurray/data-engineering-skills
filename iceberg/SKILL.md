---
name: iceberg
description: Apache Iceberg table format expertise for data lakehouses. Use when the user mentions Iceberg, lakehouse, table format v2 or v3, deletion vectors, partition evolution, time travel, snapshot isolation, Polaris, Nessie, REST catalogs, metadata.json, manifest lists, snapshots, Spark, Flink, Trino, Athena, Snowflake, or table maintenance.
---

# Apache Iceberg Expert

Use this skill for Iceberg table design, engine integration, catalog choice, schema and partition evolution, time travel, row-level operations, and maintenance.

## Current Facts

- **Current Apache Iceberg project release:** 1.11.0, published May 20, 2026.
- **Format versions:** v1, v2, and v3 are complete and adopted by the Iceberg community.
- **Format v2:** production baseline for row-level deletes and broad engine compatibility.
- **Format v3:** adds nanosecond timestamp types, `variant`, geometry/geography, unknown type, default values, multi-argument transforms, row lineage, binary deletion vectors, and table encryption keys.
- **Format v4:** under active development and not formally adopted.
- **Polaris:** Apache Polaris graduated to a Top-Level Project in February/March 2026 and is a vendor-neutral Iceberg REST catalog implementation.
- **Engine support:** v3 support broadened in 2025-2026, including AWS and Snowflake GA support. Do not describe Trino/Athena/Snowflake support as universally pending; check the target engine/version.

## How To Use

1. Identify the engine and catalog first; Iceberg behavior varies across Spark, Flink, Trino, Athena, Snowflake, REST, Glue, Hive, Nessie, and Polaris.
2. Choose format v2 for maximum compatibility; choose v3 only when all critical engines support required v3 features.
3. For maintenance requests, inspect snapshot retention, orphan file risk, manifest counts, delete files/deletion vectors, and small-file patterns.

## Design Rules

- Use hidden partitioning and transform functions rather than exposing physical partition columns to users.
- Avoid over-partitioning; prefer partition transforms that match query predicates.
- Compact small files after streaming or high-frequency writes.
- Expire snapshots only after confirming retention, rollback, and audit requirements.
- Remove orphan files carefully; use a conservative `older_than` value to avoid deleting in-flight writes.
- Treat v2 to v3 upgrades as compatibility events, not simple property edits.

## Update Checklist

- Recheck Apache Iceberg releases before changing library/runtime versions.
- Recheck the spec page before changing format-version wording.
- Recheck engine-specific v3 support before making upgrade recommendations.
