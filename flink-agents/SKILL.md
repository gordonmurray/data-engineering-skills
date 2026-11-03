---
name: flink-agents
description: Design, integrate, upgrade, and troubleshoot Apache Flink Agents applications in streaming pipelines. Use for Flink Agents Actions, Events, Resources, ReAct agents, Java/Python/YAML definitions, runtime Skills and MCP, durable calls, Kafka or Fluss Action State Stores, agent memory, or 0.3 to 0.4 migrations. Not for ordinary Flink SQL jobs or general coding-agent skill authoring.
license: MIT
---

# Apache Flink Agents

## Scope

Flink Agents application design, integration, recovery, and deployment. Use the
`flink` skill, if installed, for core cluster and checkpoint operations, and
`fluss` for the storage service itself.

Apache also maintains [flink-agents-dev](https://nightlies.apache.org/flink/flink-agents-docs-release-0.4/docs/development/coding-agent-skill/)
with authoring references and YAML schemas. Consult the version matching the
application for scaffolding and detailed syntax. This guide covers operational
decisions and does not require that companion skill to be installed. A coding
skill installed in Claude Code is separate from Skills loaded by a running job.

## Current Facts

Release guidance checked on **2026-11-03**. Recheck the linked sources before
selecting versions for a new deployment; preserve existing project pins.

- **Current release:** 0.4.0, published October 29 and announced October 30,
  2026. It remains a preview; 1.0 API compatibility is not yet promised.
- Java distributions cover Flink 1.20 and 2.0–2.3. Use a supported patch
  release; the setup guide requires at least Flink 1.20.3. Python components
  require Python 3.10–3.12; Python 3.12 also requires Flink 2.1 or newer.
- Java jobs need the matching distribution JAR. PyFlink registers bundled
  JARs through `AgentsExecutionEnvironment`; do not blindly copy another copy
  into the cluster. Mixed-language jobs need both runtime dependency sets.
- The 0.4 Python standalone `from_list()`/`to_list()` execution path is gone.
  Use a Flink execution environment with DataStream or Table inputs/outputs,
  including for local development.
- 0.4 adds sub-agents, Decision Models, conditional Action triggers, and
  `ctx.chat`. Model routing is currently Java-programmatic only; do not assume
  feature parity across Java, Python, and YAML.

## Inspect First

1. Read dependency files and record Flink Agents, Flink, Python, JDK, and
   connector versions. Identify the job entry point and Agent-definition API;
   YAML is loaded by a Java or PyFlink job, not submitted as a separate runtime.
2. Trace input keys, Events, Action triggers, Resources, and outputs. Establish
   which business entity owns state and whether multiple tenants share keys.
3. Identify model calls, tools, MCP servers, and runtime Skill sources. Record
   which calls mutate external systems and how retries are handled.
4. Inspect checkpoint settings and any Action State Store, including its
   Kafka topic or Fluss table, retention, and the oldest required restore point.
5. For upgrades, check pending Actions and saved execution history as well as
   Flink operator state. For latency, inspect queueing, model/tool latency,
   retries, concurrency, and provider limits separately.

## Decision Rules

- Use Flink Agents when continuous keyed events, state, and recovery are part
  of the workload. A one-off model call alone does not justify a Flink cluster.
- Start with explicit Actions and Event dependencies for fixed business flows;
  use ReAct when model-selected tool sequences are actually needed. Set bounds
  on retries, concurrent requests, and tool loops against cost and latency goals.
- Checkpointing protects job state and compatible outputs; external calls can
  repeat. Add a Kafka or Fluss Action State Store when saved Action completions
  and durable call outcomes must be reused. Give each logical Agent operator
  its own topic or table, and retain records for every required recovery point.
- Keep durable call identities, arguments, and sequence stable across recovery.
  Mutate short-term memory and emit Events in the Action body, outside durable
  functions. Use explicit Events to order Actions sharing mutable memory.
- Long-term memory uses Mem0 with chat-model, embedding-model, and vector-store
  resources. Obtain its handles inside each Action; do not cache them globally.
- Package runtime Skills where every TaskManager can access them. Remote
  sources are loaded at initialization, not automatically refreshed during a
  running job. Pin trusted archives when reproducibility matters.

## Safety

- An external write and its saved Action outcome are not one transaction.
  Use stable idempotency keys or a reconciler to handle failure between them;
  do not promise exactly-once external effects from checkpointing alone.
- 0.3 Action State Store records are incompatible with 0.4. Plan a cutover
  without reusing that history, retain rollback resources, and test restoration
  with pending Actions. This does not mean every Flink savepoint is incompatible.
- Runtime Skill command allowlists are not an OS sandbox. Review scripts and
  interpreter permissions; a permitted interpreter can execute more than one
  bundled script. Do not treat model-generated tool arguments as authorization.
- Keep provider keys and sensitive event payloads out of committed definitions
  and unrestricted traces. Protect Action State Store contents as application
  data, including saved model/tool results.

## Verify

- Validate YAML against the target release's schema, resolve Resources and
  Action references, and run imports or compilation in the job's environment.
- In an isolated job, process representative keyed inputs and check outputs,
  per-key memory isolation, and a completed checkpoint. Use model/tool stubs
  first when testing deterministic business behavior.
- Exercise recovery around an external call and check both output duplication
  and repeated external effects. A successful checkpoint is not that test.
- For 0.4 migration, replace rejected Event Log keys with Trace Log settings
  and verify the resulting traces. Check model-call failures and backlog too.
- Report schema/build checks, local execution, live-provider checks, and
  recovery tests separately; identify any that could not run.

## Update Checklist

- Check the release announcement for API, state, and configuration migrations.
- Recheck setup requirements and feature support per language before emitting
  code. Use release documentation and schemas rather than `main` examples.
- Recheck the upstream development skill before duplicating authoring helpers.

## Sources

- [0.4.0 release and breaking changes](https://flink.apache.org/2026/10/30/apache-flink-agents-0.4.0-release-announcement/)
- [Runtime setup and packaging](https://nightlies.apache.org/flink/flink-agents-docs-release-0.4/docs/get-started/setup/)
- [Actions and durable execution](https://nightlies.apache.org/flink/flink-agents-docs-release-0.4/docs/development/create-agent/actions/)
- [Consistency and recovery limits](https://nightlies.apache.org/flink/flink-agents-docs-release-0.4/docs/operations/consistency/)
- [Long-term memory](https://nightlies.apache.org/flink/flink-agents-docs-release-0.4/docs/development/memory/long_term_memory/)
- [Runtime Skills and command permissions](https://nightlies.apache.org/flink/flink-agents-docs-release-0.4/docs/development/calling-llms/skills/)
