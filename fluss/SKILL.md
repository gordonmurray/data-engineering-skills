---
name: fluss
description: Design, deploy, and operate Apache Fluss streaming storage. Use for Fluss log or primary-key tables, retention and bucket sizing, tiering to Paimon, Iceberg, or Hudi, Flink integration and Delta Join, $changelog and $binlog virtual tables, Spark access, REST Gateway, native client SDKs, or hot storage for real-time analytics and AI context.
license: MIT
---

# Apache Fluss Expert

## Scope

Fluss table design, low-latency stream storage, Flink integration, tiering to
lakehouse formats, and operational planning.

For the cold lakehouse side of a tiered architecture use the `paimon` or
`iceberg` skills, and for Flink job internals use `flink`.

## Current Facts

Release guidance checked on **2026-11-03**. Recheck the linked sources before
selecting versions for a new deployment; preserve existing project pins.

- **Current stable:** Apache Fluss 1.0.0, announced September 21, 2026. Fluss is a Top-Level Project and is no longer pre-1.0. The older 0.9.1 release retains its incubating suffix.
- **1.0 capabilities:** REST Gateway, coordinator high availability, Hudi tiering, primary-key row TTL, and expanded Flink/Spark integration. Gateway MCP support remains planned; HTTP access does not imply an MCP server exists.
- **Clients:** Rust, Python, and C++ clients now ship from the main repository alongside Java. Check feature support per language instead of carrying forward the old 0.1.0 maturity assumption.
- **Flink:** 1.0 adds Flink 2.3 support. CDC 3.7 still targets Flink 1.20 and 2.2; select compatible versions across the whole pipeline.
- **Docker images:** `apache/fluss:1.0.0` and `apache/fluss-quickstart-flink:1.20-1.0.0` are the documented quickstart tags. Do not append `-incubating` to 1.0 images.

## Inspect First

Establish before recommending or changing anything:

1. Fluss version, and whether the deployment is a real cluster or a
   single-node evaluation setup. Advice differs sharply between the two.
2. Table type (log or primary-key), bucket count, and the tiering target if
   one is configured.
3. Flink version, Flink CDC version, and the Fluss connector version, before
   writing any job code.
4. For latency work, whether reads are being served from Fluss or from the
   tiered lake, and how bucket count compares to consumer parallelism.

## Decision Rules

- Use Fluss for hot, sub-second stream and table access, and tier to Paimon or
  Iceberg for cold history. Do not treat Fluss as the long-retention system of
  record.
- Use log tables for append-only events and primary-key tables for mutable
  keyed state or CDC.
- Size buckets against consumer parallelism. Too few caps read throughput, too
  many adds small-file and tablet overhead.
- Use `$changelog` and `$binlog` virtual tables for audit, replay, CDC, and ML
  reproducibility rather than rebuilding that history downstream.
- Use the aggregation merge engine when moving aggregate state into storage
  measurably simplifies Flink state.
- Pin exact server, client, and connector versions. Keep incubating suffixes
  only for old releases whose published artifacts use them.
- On eligible partitioned 1.0 tables, bucket rescaling changes future
  partitions, not existing ones. Check restrictions before promising a rebalance.

## Safety

- Check the release-specific upgrade path and client compatibility before a
  0.9 to 1.0 rollout; graduation alone does not validate an existing deployment.
- Distinguish local log TTL, total log TTL, primary-key row TTL, partition
  expiry, and lake retention. Eviction from local disk can leave remote logs
  readable; expired rows or partitions have different recovery implications.
- Keep S3, Azure Blob, and ADLS Gen2 credentials out of table properties and
  out of anything committed to a repository.

## Verify

- Confirm the tiering job is running and that the lake target actually receives
  data, by reading the Paimon or Iceberg table directly rather than trusting
  job status.
- Measure end-to-end latency with a timestamped test record instead of quoting
  the project's sub-second claim.
- After bucket or schema changes, confirm existing consumers still read
  successfully.
- Report Fluss, Flink, connector, and client versions, including which tier
  served the verification read.

## Update Checklist

- Recheck Fluss downloads before changing stable versions.
- Recheck client SDK maturity before recommending Python/C++/Rust client use in production.

## Sources

- [Fluss downloads](https://fluss.apache.org/downloads/)
- [Fluss 1.0 release and compatibility notes](https://fluss.apache.org/blog/releases/1.0/)
- [Published quickstart image tags](https://fluss.apache.org/docs/quickstart/flink/)
- [Flink CDC distributions](https://flink.apache.org/downloads/)
