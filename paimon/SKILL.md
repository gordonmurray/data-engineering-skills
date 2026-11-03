---
name: paimon
description: Design, ingest into, tune, and operate Apache Paimon tables for streaming lakehouses and multimodal data. Use for Paimon primary-key or append-only table design, bucket sizing, changelog producer choice, Flink CDC ingestion, compaction backlog, lookup joins, PyPaimon, blob and vector storage, Spark reads, or Iceberg compatibility.
license: MIT
---

# Apache Paimon Expert

## Scope

Paimon table design, Flink-native streaming ingestion, changelog semantics,
compaction, lookup joins, Spark reads, Iceberg compatibility, and Paimon 2.x
multimodal tables and Python integrations.

For Flink job architecture and operations use the `flink` skill. For Iceberg
table internals use `iceberg`; this skill covers Paimon's Iceberg compatibility
mode, not Iceberg itself.

## Current Facts

Release guidance checked on **2026-11-03**. Recheck the linked sources before
selecting versions for a new deployment; preserve existing project pins.

- **Current stable Paimon and PyPaimon:** 2.1.0, published October 12, 2026. Paimon 2.0 shipped in August; it is no longer a roadmap-only release.
- **Release authority:** use signed ASF distributions and matching Maven/PyPI artifacts. Paimon and PyPaimon share a release version and vote; do not infer availability from a development branch or GitHub Releases alone.
- **Python:** install `pypaimon`; its source lives in `apache/paimon`. Verify optional native accelerators and their versions separately from the Python SDK.
- **Flink integration:** 2.1.0 engine artifacts cover Flink 1.16–1.20 and 2.0–2.2. `paimon-flink-2.3:2.1.0` is not published. CDC 3.7.0 distributes for 1.20.x and 2.2.x, so choose their intersection for CDC pipelines.
- **Spark integration:** 2.1.0 publishes Spark 4.1 and 4.0 artifacts with Scala 2.13, and Spark 3.2–3.5 artifacts with Scala 2.12. Spark 4.1 is no longer master-only.
- **2.x scope:** the released documentation covers data evolution, blob and vector storage, global indexes, full-text search, and PyPaimon integration with Ray and PyTorch. Check the specific table mode and engine before applying primary-key streaming advice to a multimodal table.

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
5. For a 1.x to 2.x upgrade, inspect the target release's migration notes and
   each reader/writer dependency. For multimodal work, identify blob storage,
   index type, and the Python/native components actually installed.

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

- Recheck Apache Paimon tags and signed ASF distributions, then confirm Maven
  artifacts and PyPI `pypaimon` publication for the selected release.
- Recheck Flink CDC compatibility for the selected Flink and Paimon releases.

## Sources

- [Signed Paimon and PyPaimon releases](https://downloads.apache.org/paimon/)
- [Paimon 2.1 engine artifacts](https://paimon.apache.org/docs/2.1/project/download/)
- [Paimon 2.1 documentation](https://paimon.apache.org/docs/2.1/)
- [Paimon/PyPaimon release model](https://paimon.apache.org/docs/2.1/project/releases/)
- [PyPaimon package](https://pypi.org/project/pypaimon/)
- [Flink CDC distributions and compatibility](https://flink.apache.org/downloads/)
