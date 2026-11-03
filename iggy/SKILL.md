---
name: iggy
description: Deploy, configure, and build clients against Apache Iggy, a Rust-native message streaming platform. Use for Iggy Docker, Compose, or Kubernetes deployments, stream and topic design, retention and consumer groups, QUIC, TCP, HTTP, or WebSocket transport, apache-iggy Python clients, MCP and connectors, 0.8 to 0.9 migration, or container connectivity and persistence problems.
license: MIT
---

# Apache Iggy Streaming Expert

## Scope

Iggy deployment, stream and topic design, producer and consumer patterns,
Docker Compose, SDK usage, and MCP-oriented AI workflows.

For general Compose file structure use the `docker-compose` skill; this skill
covers the Iggy-specific settings inside it.

## Current Facts

Release guidance checked on **2026-11-03**. Recheck the linked sources before
selecting versions for a new deployment; preserve existing project pins.

- **Current server release:** 0.9.0, released September 18, 2026, following graduation from the Incubator. Older 0.8.0 and 0.7.0 artifacts retain `-incubating`.
- **Server image:** `apache/iggy:0.9.0`. Web UI, MCP, and Connect have separate image/version streams; verify their tags independently. `edge` builds are development snapshots.
- **SDK compatibility for server 0.9:** Rust `iggy` 0.11.0, CLI 0.14.0, Python `apache-iggy` 0.9.0 (Python 3.10+), Java 0.9.0, Node 0.10.0, Go/C# 0.9.0. Match the compatibility matrix, not just version-number equality.
- **Ports:** HTTP 3000, QUIC UDP 8080, TCP 8090, WebSocket 8092.
- **0.9 upgrade boundary:** on-disk data, wire protocol, and configuration changed. A 0.9 server cannot read a 0.8 data directory, and there is no in-place migration. Clients and server must cut over together.

## Inspect First

Establish before recommending or changing anything:

1. Server and data-directory versions. Determine whether this is a fresh 0.9
   deployment or a migration with data that must be exported and replayed.
2. Deployment target: local binary, Docker, Compose, Kubernetes/Helm, or
   SDK-only client work.
3. The installed SDK package version, separately from the server version. For
   Python, check the installed `apache-iggy` methods and server compatibility
   before writing detailed code.
4. For connection failures, which transport and port are in use, and whether
   the server is bound to `0.0.0.0` rather than loopback inside the container.

## Decision Rules

- Choose transport by requirement: TCP for throughput, QUIC for latency, HTTP
  for REST and admin, WebSocket for browser-compatible clients.
- Set wildcard listeners for transports exposed from a container, together
  with `IGGY_NODE_ADVERTISED_ADDRESS` reachable by the clients. In 0.9 a
  wildcard bind without an advertised address prevents startup.
- Persist `/app/local_data` for the published 0.9 image, or explicitly set
  `IGGY_PATH` and mount that path. The repository-built image uses
  `/local_data`; do not assume those image layouts are interchangeable.
- Account for io_uring and thread-affinity requirements. Compose examples often
  need `SYS_NICE`, `seccomp:unconfined`, and memlock ulimits.
- Pin exact version tags in production rather than `latest`, and pin server and
  SDK versions independently.
- For 0.8 to 0.9, replace moved configuration keys, including
  `IGGY_SYSTEM_PATH` with `IGGY_PATH`. Review per-topic durability settings;
  the old `enforce_fsync` switches no longer apply.

## Safety

- Supply `IGGY_ROOT_USERNAME` and `IGGY_ROOT_PASSWORD` through environment or
  secret files, never hardcoded in a committed Compose file, and change the
  defaults before exposing any port beyond localhost.
- Before a 0.8 to 0.9 cutover, preserve the old volume and a compatible server
  for rollback, export required data, and validate replay into a separate empty
  directory. A backup of 0.8 files is not directly readable by 0.9.
- Never use `--fresh` as a repair step on valuable data: it wipes the local
  replica directory. Bootstrap credentials do not replace recovered credentials.
- Do not publish QUIC, TCP, or HTTP ports on a public interface without
  authentication configured.
- Deleting a stream or topic removes its persisted segments. Confirm the exact
  target name before running any delete.

## Verify

- Confirm the server answers on the intended transport, not merely that the
  container is running: an HTTP request to the server or a CLI ping.
- List streams and topics back after creating them.
- Send and consume one test message end to end before calling a pipeline
  working.
- After an upgrade, confirm the client SDK version actually negotiates with the
  server version.
- For container deployments, verify the mounted path matches `IGGY_PATH` and
  that clients can reach the advertised address returned by the server.
- Report server version, SDK version, transport, and exactly what you
  exercised.

## Update Checklist

- Recheck Iggy downloads and the version-specific migration guide.
- Recheck SDK package versions separately; server, Rust, Python, Java, Go, C#, and Web UI versions may differ.

## Sources

- [Iggy releases](https://iggy.apache.org/downloads/)
- [0.8 to 0.9 upgrade requirements](https://iggy.apache.org/docs/server/upgrading/)
- [SDK compatibility matrix](https://iggy.apache.org/docs/sdk/introduction/)
- [Published image paths and networking](https://iggy.apache.org/docs/server/docker/)
- [Python package](https://pypi.org/project/apache-iggy/)
