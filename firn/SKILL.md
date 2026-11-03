---
name: firn
description: Design, deploy, use, and troubleshoot Firn, the object-storage-backed multi-tenant vector and full-text search engine. Use for Firn REST API or embedded Python work, LanceDB-backed vector, BM25, hybrid, or multivector search, S3/GCS/MinIO storage, RAM/NVMe/object-storage caching, ingestion and index-build workflows, namespace isolation, auth, metrics, latency, or cache correctness.
license: Apache-2.0
---

# Firn Search Expert

## Scope

Firn architecture, REST service operations, embedded Python usage, object-storage
deployment, vector/BM25/hybrid retrieval, multivector search, caching, ingestion,
indexing, observability, and operational troubleshooting.

Firn has two distinct interfaces:

- **Server mode:** the Rust `firnflow-api` Axum service, configured with
  `FIRNFLOW_*` environment variables and accessed through HTTP.
- **Embedded mode:** the `firn` Python extension, imported in-process with
  `firn.connect()`. It does not connect to a running Firn server.

For the underlying Lance/LanceDB format or generic object-storage design, use the
`lance` skill as well. Keep Firn-specific namespace, cache, API, and operational
semantics here.

## Current Facts

Release guidance checked on **2026-11-03**. Recheck the linked sources before
selecting versions for a new deployment; preserve existing project pins.

- **Published releases:** server `v0.9.7` and Python `firn` 0.2.3, both
  published September 3, 2026. They version independently. Use the tagged
  repository and release notes when website or README version labels differ.
- **New query controls:** `exact: true` bypasses the vector index and result
  caches for a single-vector ground-truth query. `refine_factor` retrieves
  extra ANN candidates and reranks them using full-precision vectors; it trades
  extra reads for recall and cannot be combined with `exact: true`.
- **Typed attributes:** `/attributes` declares scalar `string`, `int`, `float`,
  or `bool` columns; writes supply values through `attributes`. Declaration is
  additive, and redeclaring a column with a different type fails. Check the
  release's API before treating arbitrary JSON metadata as supported.
- Firn stores each namespace below a configured `s3://` or `gs://` root. Supported
  deployments include AWS S3, MinIO, Cloudflare R2, Tigris, DigitalOcean Spaces,
  native GCS, and local filesystem storage for embedded use.
- **Multi-writer safety depends on object-store compare-and-swap, and not every
  S3-compatible store qualifies.** Backblaze B2 fails: its S3 gateway returns
  HTTP 501 on `If-None-Match: *`. R2, Tigris, and DigitalOcean Spaces need
  path-style addressing. Before 0.9.1, region resolution ignored `AWS_REGION`
  and defaulted to `us-east-1`.
- **Without an IVF_PQ index, uncached vector searches scan the data.** Index
  building is manual and post-hoc. Benchmark novel queries separately from
  cached repeats; published latency numbers describe a specific corpus and
  storage setup, not a service guarantee.
- Firn is a single-node service. The cache is in-process, there is no horizontal
  scaling, and cross-namespace or federated queries return 400. There are no
  official server SDKs and no CLI, so the server is HTTP only.
- The service cache path is result cache in RAM/NVMe, then Lance/object storage;
  the optional object cache is a separate local byte-range cache below Lance and
  is disabled by default. Object storage remains the source of truth.
- Vector search is brute-force without an index. The service can build an
  asynchronous `IVF_PQ` index; BM25 uses an asynchronous FTS index. A scalar
  BTree index can accelerate `id` merge-insert lookups or `_ingested_at` listing.
- A namespace fixes its vector kind on its first write: single vector (`vector`)
  or multivector (`vectors`). It also fixes the corresponding dimension. Create a
  new namespace to change kind; do not assume a migration exists.
- `/upsert` is idempotent latest-write-wins by `id`. `/import` is a binary Arrow
  IPC bulk-load path, insert-only, and asynchronous; repeated ids create another
  row rather than updating an existing one.
- The Python API performs vector, BM25, and hybrid search in-process. Python
  `tenant=` selects a physically separate namespace; the Python v0.2 surface is
  embedded-only and does not expose the server's REST API.

## Inspect First

Establish before recommending code or changing a deployment:

1. Which interface is in use: HTTP service or embedded Python. Do not mix
   `FIRNFLOW_*` server configuration with the Python API without checking the
   package's storage options.
2. The exact Firn, LanceDB, and Python versions from the checkout or installed
   environment, plus the storage URI scheme and any fixed prefix.
3. Namespace state: vector kind, dimension, row count, fragments, table version,
   and existing vector, FTS, and scalar indexes. `GET /ns/{ns}` exposes service
   metadata; inspect the table directly for embedded use.
4. Ingestion shape and intent. Use `/upsert` for retry-safe updates; use Arrow
   `/import` for large insert-only first loads. Identify whether compaction and
   index builds have completed by polling `GET /operations/{id}`.
5. For latency or cost issues, separate exact result-cache hits, semantic-cache
   hits, object-cache hits, and genuinely cold Lance queries. Check the
   `firnflow_*` metrics and measure a cold/warm pair instead of inferring from a
   single request.
6. For auth or tenant-isolation questions, determine whether a gateway maps
   authenticated tenants to namespaces. Firn's bearer keys authorize the
   process, not individual namespaces.

## Decision Rules

- Build `IVF_PQ` after the bulk of the data is loaded and compacted when cold
  object-storage search matters. It improves novel-query latency; it does not
  make a novel query an exact result-cache hit.
- Measure single-vector ANN recall against `exact: true` on the same sample,
  filters, and dataset state. Tune `nprobes` and `refine_factor` against the
  latency budget; do not combine either with exact mode. Exact mode rejects
  text, hybrid, and multivector query shapes.
- Batch JSON upserts toward `FIRNFLOW_MAX_BODY_BYTES`. For very large first loads,
  prefer Arrow IPC `/import`, then compact and build the needed indexes.
- Build the BM25 index before text-only or hybrid queries when the namespace has
  meaningful text. Vector-only search does not require the FTS index.
- Use multivectors for late-interaction encoders such as ColBERT, ColPali, or
  ColQwen2. Expect roughly 250x the per-row storage, around 2 KB for a single
  CLIP vector against around 500 KB for ColPali. The vector shape is fixed per
  namespace, and multivector search is cosine-only while single-vector uses L2.
- Treat the exact result cache as an exact-repeat optimization: the query,
  namespace generation, and relevant options must match. Writes, deletes,
  compaction, and index commits make old-generation results unreachable.
- Enable the semantic cache only when approximate reuse is acceptable. It is
  single-vector only, bounded and in-memory per process, and similarity is not a
  guarantee that the fresh top-k would be identical.
- Put the object cache on fast local NVMe when unique queries repeatedly touch
  the same immutable Lance data or index bytes. Tune its byte budget and entry
  cap independently from the result cache.
- Use IAM roles or platform secret injection for S3 credentials. For native GCS,
  use the native `gs://` path and Google application credentials; do not silently
  substitute the GCS S3-interop endpoint when conditional-write correctness is
  required.

## Safety

- Set `FIRNFLOW_API_KEY` in production. If `FIRNFLOW_ADMIN_API_KEY` is also set,
  keep it distinct: delete, compaction, and index-build routes are destructive or
  maintenance operations. With no keys, the local-dev default is open and the
  server logs a warning.
- Service auth is not tenant auth. A valid read/write key can access every
  namespace, so enforce tenant-to-namespace authorization at an upstream gateway.
- Do not delete a namespace, compact, rebuild indexes, or change storage roots
  without confirming the target namespace and having a recovery/source-of-truth
  plan. Object-cache files are disposable; object-storage data is not.
- Do not treat a `202 Accepted` as completion. Poll its opaque operation id and
  surface a failed operation's error before declaring the load or index usable.
- Do not use `/import` for retries or updates unless duplicate rows are intended.
  Use `/upsert` for idempotent latest-write-wins behavior.
- **On 0.9.3 and earlier, a `now()`-style predicate in a query filter serves
  stale results.** Filters were cached by predicate text, so `_ingested_at <
  now()` stays byte-identical while the cutoff it describes moves, replaying the
  first result set until the next write. Fixed in 0.9.4. On any version, passing
  a client-computed literal microsecond bound is both correct and cacheable.
- **`/upsert` was an unconditional append before 0.9.0.** Namespaces first
  written by an older version can hold duplicate `id`s, and merge-insert into a
  target containing duplicates is undefined behavior in Lance. Upgrading does
  not retroactively dedupe; check for duplicate ids before trusting upsert
  semantics on an old namespace, and re-ingest if any exist.
- Do not enable semantic-cache reuse silently for accuracy-sensitive retrieval.
  Report approximate-hit behavior and monitor hit, miss, and rejection metrics.
- Keep API keys, AWS secrets, GCS service-account JSON, and signed storage URLs
  out of code, logs, committed config, and query payloads.

## Verify

- Start with `GET /health`, then verify storage with a small write and read in a
  dedicated namespace. Check `GET /ns/{ns}` for row count, fragments, indexes,
  and table version.
- After `/import`, `/warmup`, `/index`, `/fts-index`, `/scalar-index`, or
  `/compact`, poll `GET /operations/{id}` until `succeeded` or `failed`.
- Test vector-only, text-only, and hybrid queries separately. For multivector
  namespaces, test the `vectors` wire shape and verify that a single-vector
  payload is rejected rather than coerced. A text or hybrid query against a
  populated namespace without an FTS index returns 400 naming the missing
  index. Build it before retrying; an empty namespace returning no hits does
  not validate FTS readiness.
- Confirm cache claims with repeated and novel queries plus Prometheus metrics;
  compare backend request counts and latency. A warm exact hit is not evidence
  that a new query is fast.
- For production readiness, verify bearer-token enforcement, admin separation,
  rate limits, `/metrics` protection, health probes, durable object storage, and
  a fast cache volume. Report which checks were actually run.

## Update Checklist

- Recheck the Firn repository, release tags, server API, and Python package
  metadata before changing version guidance.
- Recheck Lance/LanceDB compatibility and index API details before recommending
  new index types or tuning parameters.
- Recheck supported storage backends and conditional-write behavior before adding
  a deployment recipe.
- Recheck configuration names, defaults, authentication tiers, async operation
  semantics, and metrics when the server API changes.

## Sources

- [Firn v0.9.7 release and refinement](https://github.com/gordonmurray/firnflow/releases/tag/v0.9.7)
- [Firn v0.9.6 exact queries and attributes](https://github.com/gordonmurray/firnflow/releases/tag/v0.9.6)
- [Tagged server architecture and operational reference](https://github.com/gordonmurray/firnflow/blob/v0.9.7/README.md)
- [Published Python package](https://pypi.org/project/firn/)
- [REST API and authentication](https://firnflow.io/api.html)
