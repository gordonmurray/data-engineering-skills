---
name: flink
description: Architect, implement, deploy, upgrade, and troubleshoot Apache Flink stream processing jobs. Use for Flink SQL, Table API, or DataStream implementation, 1.x to 2.x migration, savepoint and state compatibility, checkpoint failures, backpressure, watermark and late-data problems, Kubernetes Operator deployment, Flink CDC pipelines, or Iceberg, Paimon, and Fluss connector work.
license: MIT
---

# Apache Flink Data Streaming Expert

## Scope

Production Flink architecture, operations, SQL and DataStream implementation,
upgrade planning, and lakehouse streaming integrations.

For table-format internals use the `iceberg`, `paimon`, or `fluss` skills. This
skill covers the Flink job and its connectors, not the storage format's own
maintenance operations.

## Current Facts

- **Current Flink line:** 2.2.x. Downloads include Apache Flink 2.2.1, while the site still labels 2.2.0 as the latest stable line.
- **Maintained 2.x patch lines:** 2.2.1, 2.1.2, 2.0.2.
- **1.x maintenance line:** 1.20.4. Use this as the 1.x migration baseline unless the project is pinned elsewhere.
- **Kubernetes Operator:** 1.15.0, compatible with Flink 2.2.x, 2.1.x, 2.0.x, 1.20.x, and 1.19.x.
- **Flink CDC:** 3.6.0, with artifacts for Flink 1.20.x and 2.2.x.
- **Java:** Flink 2.x requires Java 11+; Java 17 is the practical default for new deployments.

## Critical 2.x Notes

- DataSet API removed; use DataStream, Table API, or SQL.
- Scala DataStream/DataSet APIs removed from the core distribution.
- SourceFunction/SinkFunction and Sink V1 patterns are obsolete; prefer Source/Sink V2 connectors.
- `flink-conf.yaml` was replaced by standard YAML `config.yaml` in Flink 2.x.
- Per-job deployment mode was removed; use Application mode or Kubernetes Operator patterns.
- Validate savepoint compatibility carefully before 1.x to 2.x migrations.

## Inspect First

Establish before recommending or changing anything:

1. The Flink version of the running cluster and of the job's dependencies.
   These drift apart more often than users expect.
2. Deployment mode: Application, Session, Kubernetes Operator, YARN, or
   standalone.
3. State backend, checkpoint storage location, and whether a recent savepoint
   exists.
4. For migrations, the exact source version, every connector version, and
   whether the existing savepoint can be restored by the target version.
5. For troubleshooting, read real metrics rather than inferring: checkpoint
   duration and failure count, backpressure, restart count, state size, and
   watermark lag.

## Decision Rules

- Prefer Flink 2.2.x with current connector artifacts for greenfield work.
- Enable checkpointing and set explicit checkpoint storage. The default is not
  durable across cluster restarts.
- Use savepoints, not checkpoints, for planned upgrades and topology changes.
- Set explicit operator UIDs before the first production deploy. A generated
  UID changes when the job graph changes and silently breaks state restore.
- Make event-time assumptions visible: choose watermark strategy and allowed
  lateness deliberately, and decide explicitly where late data goes.
- Prefer the Kubernetes Operator for long-running production jobs on Kubernetes.
- Use Iceberg, Paimon, and Fluss connectors only at versions compatible with
  the selected Flink line.

## Safety

- Take a savepoint before any upgrade, topology change, or parallelism change,
  and confirm it completed before stopping the job.
- `--allowNonRestoredState` silently discards state for operators missing from
  the new job graph. Never pass it to get past a restore failure without first
  identifying which operator's state is being dropped and confirming that loss
  is acceptable.
- Do not delete checkpoint or savepoint directories until the replacement job
  has run and completed a checkpoint of its own.
- Keep credentials out of `config.yaml` and job arguments; use platform secrets.
- Rescaling and state migration are not free. State the expected downtime
  before proposing them for a production job.

## Verify

- Confirm the job reaches RUNNING and completes at least one checkpoint after
  deployment. A RUNNING job that never checkpoints is not healthy.
- After a restore, check that state size is in the expected range. Near-zero
  state after a restore usually means state was silently dropped.
- Compare checkpoint duration, restart count, and backpressure against the
  values from before the change.
- For SQL changes, read the `EXPLAIN` plan before running against production
  data.
- Report the Flink version, deployment mode, and which metrics you actually
  observed rather than which ones should improve.

## Update Checklist

- Recheck Flink downloads for core, CDC, connector, and Kubernetes Operator versions.
- Update Helm/doc URLs when operator versions change.
