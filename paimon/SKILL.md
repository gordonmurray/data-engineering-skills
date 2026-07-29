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

- **Current stable Paimon:** 1.4.2, released June 23, 2026. There is no 1.5 release candidate; master is 1.5-SNAPSHOT.
- **apache/paimon publishes no GitHub Releases.** Git tags and the ASF dist area are the authoritative signal for what has actually shipped.
- **PyPaimon:** 1.4.2 on PyPI, sdist only, a pure Python SDK with no JDK dependency. `pypaimon-rust` 0.3.0 is a separate optional Rust accelerator shipping binary wheels; it is not a dependency of pypaimon. The old `apache/paimon-python` repository is abandoned and PyPaimon now lives inside `apache/paimon`.
- **Flink CDC:** 3.6.0 is the current CDC line; older 3.5 examples remain useful but should not be described as latest.
- **The Flink ceiling is 2.2.x, and the reason matters.** Flink 2.3.0 is now the latest stable engine, but `paimon-flink-2.3` is not published to Maven Central and Flink CDC 3.6 requires 1.20.x or 2.2.x. Use 1.20.x or 2.2.x, and expect users who checked flink.apache.org to ask why 2.3 is excluded.
- **Spark connectors published for 1.4.2:** Spark 4.0 as `paimon-spark-4.0_2.13`, and Spark 3.5, 3.4, 3.3, and 3.2 as `_2.12`. Spark 4.1 exists only on master and is not published, so do not recommend it.
- **Current roadmap is "Paimon 2.0 Planning":** unified storage for structured, multimodal, and vector data; search across data, vectors, and full text; and PyPaimon integration with Ray and PyTorch. Named workstreams include data evolution, blob store, vector store, and a global index framework. Lookup join performance remains active.
- **New Rust sub-projects with independent releases:** `paimon-vector-index` (IVF-PQ for lake vector search), `paimon-full-text`, `paimon-mosaic` (columnar-bucket hybrid format for wide tables), plus `paimon-rust` and `paimon-cpp`.

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

- Recheck Apache Paimon git tags and the ASF dist area, not GitHub Releases, which the project leaves empty. Recheck PyPI `pypaimon` separately.
- Recheck Flink CDC compatibility for the selected Flink and Paimon releases.
