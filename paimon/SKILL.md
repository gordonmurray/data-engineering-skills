---
name: paimon
description: Design, ingest into, tune, and operate Apache Paimon tables for streaming lakehouses. Use for Paimon primary-key or append-only table design, bucket sizing, changelog producer choice, Flink CDC ingestion, compaction backlog, lookup join performance, PyPaimon, Spark reads, Iceberg compatibility, or streaming writes that produce too many small files.
license: MIT
---

# Apache Paimon Expert

## Scope

Paimon table design, Flink-native streaming ingestion, changelog semantics,
compaction, lookup joins, Spark reads, and Iceberg compatibility.

For Flink job architecture and operations use the `flink` skill. For Iceberg
table internals use `iceberg`; this skill covers Paimon's Iceberg compatibility
mode, not Iceberg itself.

## Current Facts

- **Current stable Paimon:** 1.4.1. A 1.4.2 release candidate exists; do not recommend it as stable unless the user explicitly wants RC testing.
- **PyPaimon:** 1.4.1 on PyPI, pure Python package.
- **Flink CDC:** 3.6.0 is the current CDC line; older 3.5 examples remain useful but should not be described as latest.
- **Recommended Flink:** Flink 1.20.x or 2.2.x for new work when connector compatibility allows.
- **Recommended Spark:** verify against the Paimon connector matrix for the selected Paimon version; do not hard-code Spark 3.4.3 for new projects without checking.
- **Recent focus areas:** PyPaimon, data evolution, Iceberg compatibility, deletion vectors, REST Catalog authorization interfaces, lookup join performance, multimodal/blob storage, and Paimon/Lance integration work.

## Inspect First

Establish before recommending or changing anything:

1. Table type, bucket mode, and bucket count, from the DDL or `DESCRIBE`.
   Primary-key and append-only tables behave differently under every subsequent
   decision.
2. Paimon, Flink, and Flink CDC versions actually in use.
3. The current changelog producer setting, and whether any downstream consumer
   reads changelog at all.
4. For performance work, read the `$files`, `$snapshots`, `$manifests`, and
   `$options` system tables. Get file count per bucket, average file size,
   compaction backlog, and snapshot expiry settings rather than assuming.

## Decision Rules

- Include partition fields in the primary key when the table is partitioned.
- Size buckets up front. Changing the bucket count of a fixed-bucket table
  requires rewriting existing data, so choose against expected volume rather
  than accepting the default.
- Choose the changelog producer from real downstream need: `none` when nothing
  consumes changelog, `input` when the source already emits a complete
  changelog, and `lookup` or `full-compaction` when it must be generated. The
  last two carry real write-side cost.
- Run compaction as a dedicated job for high-volume streaming tables so
  compaction cannot backpressure ingestion.
- Use lookup cache only when the dimension table fits in memory and the
  staleness it introduces is acceptable.

## Safety

- Changing bucket count, primary key, or partition spec on an existing table
  requires a data rewrite. State the data volume and expected duration before
  proposing it.
- Snapshot expiry deletes files that time travel and lagging streaming
  consumers still need. Check consumer lag before shortening retention.
- Do not drop and recreate a table to resolve a schema problem that schema
  evolution can handle; recreating discards snapshot history.
- Keep REST catalog and object storage credentials out of table properties and
  out of SQL committed to the repository.

## Verify

- After an ingestion change, confirm the snapshot count is advancing and the
  commit interval matches expectation.
- After compaction or bucket changes, compare file count and average file size
  per bucket via `$files`.
- For CDC pipelines, check row counts and a sample of updated and deleted keys
  against the source. A running job is not evidence of correct output.
- Report the Paimon and Flink versions and which system tables you read.

## Update Checklist

- Recheck Apache Paimon tags/downloads and PyPI `pypaimon` before changing versions.
- Recheck Flink CDC compatibility for the selected Flink and Paimon releases.
