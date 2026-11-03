---
name: iceberg
description: Design, migrate, tune, and maintain Apache Iceberg tables across query engines. Use for Iceberg schema and partition evolution, v2 to v3 upgrades, catalog selection, time travel and rollback, row-level deletes, snapshot expiry, orphan file cleanup, small-file compaction, or slow queries and metadata bloat on a lakehouse table. Covers Spark, Flink, Trino, Athena, Snowflake, REST catalogs, Polaris, Nessie, Glue, and Hive.
license: MIT
---

# Apache Iceberg Expert

## Scope

Iceberg table design, engine integration, catalog choice, schema and partition
evolution, time travel, row-level operations, and maintenance.

For Flink job architecture use the `flink` skill, for Paimon streaming ingestion
use `paimon`, and for Fluss hot storage use `fluss`. This skill applies to the
Iceberg table those systems read or write, not to the engine itself.

## Current Facts

Release guidance checked on **2026-11-03**. Recheck the linked sources before
selecting versions for a new deployment; preserve existing project pins.

- **Current Apache Iceberg project release:** 1.12.0, released September 29, 2026. Runtime artifacts include Spark 3.5, 4.0, and 4.1, and Flink 1.20, 2.1, 2.2, and 2.3; match the engine and Scala binary version.
- **Format versions:** v1, v2, and v3 are complete and adopted by the Iceberg community.
- **Format v2:** production baseline for row-level deletes and broad engine compatibility.
- **Format v3:** adds nanosecond timestamp types, `variant`, geometry/geography, unknown type, default values, multi-argument transforms, row lineage, binary deletion vectors, and table encryption keys.
- **Format v4:** under active development and not formally adopted. The spec now names it "Metadata Structure and Representation", headlined by relative locations in metadata.
- **Polaris:** the vendor-neutral Iceberg REST catalog's current release is 1.8.0, published September 28, 2026. Keep catalog service versions separate from table format versions.
- **Engine v3 support is feature-specific.** Snowflake supports external-engine reads and writes to Snowflake-managed v3 tables through Horizon REST Catalog, including customer-managed and Snowflake-managed storage. The previous blanket prohibition on external v3 writes is obsolete. Check the supported operations for the table's catalog and storage configuration.
- **AWS:** S3 Tables documents v3 support with compatible engines, but Athena still cannot read v3 tables. Verify each reader before upgrading a shared table.

## Inspect First

Establish before recommending or changing anything:

1. Engine and version, and catalog type. Behaviour varies across Spark, Flink,
   Trino, Athena, Snowflake, REST, Glue, Hive, Nessie, and Polaris.
2. Current format version, from the table's `format-version` property.
3. For maintenance work, read the `snapshots`, `manifests`, `files`, and
   `partitions` metadata tables. Get snapshot count and age, manifest count,
   delete file and deletion vector counts, and the actual file size
   distribution rather than assuming a small-file problem.
4. Which other engines and jobs write to the table.

## Decision Rules

- Choose v2 for maximum compatibility. Choose v3 only when every engine that
  reads or writes the table supports the v3 features you need.
- Treat a v2 to v3 upgrade as a compatibility event, not a property edit.
- Use hidden partitioning and transform functions rather than exposing physical
  partition columns to users.
- Match partition transforms to real query predicates. Over-partitioning
  inflates metadata and slows planning more often than it speeds scans.
- Prefer deletion vectors over positional delete files where the engine
  supports them; merge-on-read cost scales with delete file count.
- Compact after streaming or high-frequency writes, driven by the observed file
  size distribution rather than a schedule alone.

## Safety

- `expire_snapshots` permanently deletes data files unreachable from retained
  snapshots. Before running it, confirm the retention window against rollback,
  audit, and time-travel requirements, state how many snapshots will be
  dropped, and get confirmation for a production table.
- `remove_orphan_files` deletes files not referenced by metadata, and files
  being written by in-flight jobs look exactly like orphans. Keep `older_than`
  comfortably longer than the longest-running writer. The Spark procedure
  defaults to three days for this reason; do not lower it to reclaim space
  without first confirming no writers are active.
- `DROP TABLE` semantics differ by catalog. Some purge data, some only remove
  the catalog entry. Confirm which applies before running it.
- Do not run maintenance against a production table without knowing every
  engine that writes to it.

## Verify

- After compaction, re-read `files` and report file count and average size
  before and after, plus a row count showing data is unchanged.
- After snapshot expiry, report the snapshots remaining and confirm the oldest
  retained snapshot still satisfies the stated time-travel requirement.
- After partition evolution, read `partitions` to confirm new writes land in
  the new spec while existing data stays readable.
- After a v3 upgrade, run a read from every engine that touches the table.
- Report the engine and version you validated with, and name any engine you
  could not test.

## Update Checklist

- Recheck Apache Iceberg releases before changing library/runtime versions.
- Recheck the spec page before changing format-version wording.
- Recheck engine-specific v3 support before making upgrade recommendations.

## Sources

- [Iceberg releases and engine artifacts](https://iceberg.apache.org/releases/)
- [Iceberg format specification](https://iceberg.apache.org/spec/)
- [Polaris 1.8.0 release](https://github.com/apache/polaris/releases/tag/apache-polaris-1.8.0)
- [Snowflake Horizon external-engine access](https://docs.snowflake.com/en/user-guide/tables-iceberg-access-using-external-query-engine-snowflake-horizon)
- [S3 Tables Iceberg v3 support and limits](https://docs.aws.amazon.com/AmazonS3/latest/userguide/working-with-apache-iceberg-v3.html)
