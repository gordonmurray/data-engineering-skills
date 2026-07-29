---
name: fluss
description: Design, deploy, and operate Apache Fluss (Incubating) streaming storage for sub-second real-time analytics. Use for Fluss log or primary-key table design, bucket sizing, tiering to Paimon, Iceberg, or Lance, Flink integration and Delta Join, $changelog and $binlog virtual tables, Spark access to streams, client SDK choice, or deciding between hot streaming storage and a lakehouse table.
license: MIT
---

# Apache Fluss Expert

## Scope

Fluss table design, low-latency stream storage, Flink integration, tiering to
lakehouse formats, and operational planning.

For the cold lakehouse side of a tiered architecture use the `paimon` or
`iceberg` skills, and for Flink job internals use `flink`.

## Current Facts

- **Current stable:** Apache Fluss 0.9.1.
- **Status:** Apache Incubator project. Incubating releases are not yet fully endorsed ASF products.
- **Important 0.9 line features:** Spark integration, complex nested types, zero-copy schema evolution, aggregation merge engine, auto-increment dictionary tables, `$changelog` and `$binlog` virtual tables, compacted log format, dynamic sink shuffle, KV snapshot leases, cluster rebalance, Azure Blob/ADLS Gen2 support, and Java Client POJO support.
- **Clients:** Fluss Rust, Python, and C++ client 0.1.0 has been announced; do not describe Python SDK as only future roadmap.
- **Flink CDC:** use current Flink CDC 3.6.0 guidance unless working in a pinned 3.5 environment.
- **Docker examples:** prefer `fluss/fluss:0.9.1` for current stable examples.

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
- Pin exact versions. This is a pre-1.0 incubating project and minor releases
  can break compatibility.

## Safety

- Incubating releases carry no ASF compatibility guarantee. Confirm the user
  accepts breaking changes between minor versions before recommending Fluss for
  production.
- The Rust, Python, and C++ clients are at 0.1.0. Check maturity against the
  workload before recommending them for production; the Java client is the
  mature path.
- Tiering settings determine what remains in hot storage. Confirm retention
  before enabling or changing tiering, because data aged out of Fluss is
  available only from the lake target.
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
- Report Fluss, Flink, and connector versions, and state plainly that Fluss is
  incubating.

## Update Checklist

- Recheck Fluss downloads before changing stable versions.
- Recheck client SDK maturity before recommending Python/C++/Rust client use in production.
