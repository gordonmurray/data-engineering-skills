---
name: iggy
description: Apache Iggy Incubating Rust-native message streaming platform expertise. Use when the user mentions Iggy, event streaming, Kafka/NATS alternatives, Iggy CLI or SDKs, Python apache-iggy, Docker apache/iggy images, Iggy MCP, QUIC/TCP/HTTP/WebSocket transports, streams, topics, partitions, retention, or consumer groups.
---

# Apache Iggy Streaming Expert

Use this skill for Iggy deployment, stream/topic design, producer and consumer patterns, Docker Compose, SDK usage, and MCP-oriented AI workflows.

## Current Facts

- **Current server release:** 0.8.0-incubating, released April 22, 2026.
- **Previous release:** 0.7.0-incubating, released February 24, 2026.
- **Status:** Apache Incubating since February 4, 2025. Incubating releases are not yet official ASF products.
- **Images:** `apache/iggy`, `apache/iggy-web-ui`, `apache/iggy-mcp`, `apache/iggy-connect`.
- **Ports:** HTTP 3000, QUIC UDP 8080, TCP 8090, WebSocket 8092.
- **0.8 highlights:** complete wire protocol rewrite, persistent WAL journal, shard/VSR clustering groundwork, `iggy-server-ng`, A2A protocol support, user header encryption breaking change, Java async pooling, Go TCP/TLS, revived C++ SDK, connector hot reload, Web UI 0.3.0, and security hardening.

## How To Use

1. Determine deployment mode: local binary, Docker, Compose, Kubernetes/Helm, or SDK-only client work.
2. Determine transport: TCP for throughput, QUIC for latency, HTTP for REST/admin, WebSocket for browser-compatible clients.
3. For Python, verify the installed `apache-iggy` package API before writing detailed code; async-only API details changed quickly across 0.7/0.8.
4. For deeper examples and known gotchas, consult [full-reference.md](references/full-reference.md). Treat older version values there as historical if they conflict with this file.

## Deployment Rules

- Set `IGGY_HTTP_ADDRESS=0.0.0.0:3000` and `IGGY_TCP_ADDRESS=0.0.0.0:8090` in containers when exposing services outside the container.
- Set `IGGY_ROOT_USERNAME` and `IGGY_ROOT_PASSWORD` explicitly for first startup.
- Persist `/local_data`.
- Keep io_uring and thread-affinity requirements in mind; Compose examples often need `SYS_NICE`, `seccomp:unconfined`, and memlock ulimits.
- Use fixed version tags in production rather than `latest`.

## Update Checklist

- Recheck Iggy downloads for latest incubating source release.
- Recheck SDK package versions separately; server, Rust, Python, Java, Go, C#, and Web UI versions may differ.
- Keep this `SKILL.md` concise; move long SDK examples to `references/`.
