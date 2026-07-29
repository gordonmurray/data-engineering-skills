---
name: iggy
description: Deploy, configure, and build clients against Apache Iggy (Incubating), a Rust-native message streaming platform. Use for Iggy server deployment via Docker, Compose, or Kubernetes, stream, topic, and partition design, retention and consumer group setup, transport choice across QUIC, TCP, HTTP, and WebSocket, SDK usage including the Python apache-iggy package, Iggy MCP and connectors, connection failures against an Iggy container, or evaluating Iggy against Kafka and NATS.
license: MIT
---

# Apache Iggy Streaming Expert

## Scope

Iggy deployment, stream and topic design, producer and consumer patterns,
Docker Compose, SDK usage, and MCP-oriented AI workflows.

For general Compose file structure use the `docker-compose` skill; this skill
covers the Iggy-specific settings inside it.

## Current Facts

- **Current server release:** 0.8.0-incubating, released April 22, 2026.
- **Previous release:** 0.7.0-incubating, released February 24, 2026.
- **Status:** Apache Incubating since February 4, 2025. Incubating releases are not yet official ASF products.
- **Images:** `apache/iggy`, `apache/iggy-web-ui`, `apache/iggy-mcp`, `apache/iggy-connect`.
- **Ports:** HTTP 3000, QUIC UDP 8080, TCP 8090, WebSocket 8092.
- **0.8 highlights:** complete wire protocol rewrite, persistent WAL journal, shard/VSR clustering groundwork, `iggy-server-ng`, A2A protocol support, user header encryption breaking change, Java async pooling, Go TCP/TLS, revived C++ SDK, connector hot reload, Web UI 0.3.0, and security hardening.

## Inspect First

Establish before recommending or changing anything:

1. Server version. The 0.8 wire protocol rewrite and the user header encryption
   change mean 0.7 and 0.8 guidance is not interchangeable.
2. Deployment target: local binary, Docker, Compose, Kubernetes/Helm, or
   SDK-only client work.
3. The installed SDK package version, separately from the server version. For
   Python, check the installed `apache-iggy` API before writing detailed code;
   the async-only API changed quickly across 0.7 and 0.8.
4. For connection failures, which transport and port are in use, and whether
   the server is bound to `0.0.0.0` rather than loopback inside the container.

## Decision Rules

- Choose transport by requirement: TCP for throughput, QUIC for latency, HTTP
  for REST and admin, WebSocket for browser-compatible clients.
- Set `IGGY_HTTP_ADDRESS=0.0.0.0:3000` and `IGGY_TCP_ADDRESS=0.0.0.0:8090` when
  exposing services outside the container. Default loopback binding is the
  usual cause of connection-refused from the host.
- Persist `/local_data`. Without it, streams, topics, and messages are lost
  when the container is recreated.
- Account for io_uring and thread-affinity requirements. Compose examples often
  need `SYS_NICE`, `seccomp:unconfined`, and memlock ulimits.
- Pin exact version tags in production rather than `latest`, and pin server and
  SDK versions independently.
- Upgrade client and server together across the 0.8 boundary. Mixed-version
  pairs are not safe after the wire protocol rewrite.

## Safety

- Supply `IGGY_ROOT_USERNAME` and `IGGY_ROOT_PASSWORD` through environment or
  secret files, never hardcoded in a committed Compose file, and change the
  defaults before exposing any port beyond localhost.
- The 0.8 user header encryption change is breaking. Back up `/local_data` and
  confirm the upgrade path before upgrading an existing deployment.
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
- Report server version, SDK version, transport, and exactly what you
  exercised.

## Update Checklist

- Recheck Iggy downloads for latest incubating source release.
- Recheck SDK package versions separately; server, Rust, Python, Java, Go, C#, and Web UI versions may differ.
