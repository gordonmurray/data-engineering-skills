---
name: lance
description: Lance columnar data format and LanceDB expertise for ML/AI workloads, vector search, embeddings, multimodal datasets, and .lance files. Use when the user mentions Lance, LanceDB, pylance, vector indexes, ANN search, IVF_PQ, IVF_HNSW_FLAT, HNSW, full-text search, dataset versioning, or migrating ML data from Parquet.
---

# Lance Data Format Expert

Use this skill to design, debug, and optimize Lance and LanceDB systems for ML-native data, embeddings, vector retrieval, and multimodal storage.

## Current Facts

- **Lance SDK / file-format project:** v7.0.0 stable, released May 27, 2026.
- **LanceDB Python:** v0.33.0 stable, released May 28, 2026. v0.33.1-beta.0 exists; do not treat beta as the default stable recommendation.
- **Python packages:** install `pylance` for the Lance format and `lancedb` for the embedded/vector database API.
- **Python support:** LanceDB wheels target CPython 3.9+; confirm package metadata before pinning in production.
- **Recent additions:** MemWAL/LSM write paths, materialized view API, formal catalog/namespace/table/index specs, branch/tag metadata maps, segmented BTree indices, distributed bitmap index build, FTS segment merging, serializable scalar-index caches, and nested blob export fixes.
- **LanceDB recent additions:** `IVF_HNSW_FLAT` vector index type, model-backed FTS tokenizers, and sync `create_index` API alignment with async.

## How To Use

1. Identify whether the user is asking about **Lance format** (`pylance`, `.lance`, dataset versioning, storage layout) or **LanceDB** (`lancedb`, tables, search, indexes, reranking).
2. Prefer current stable versions unless the user explicitly asks about beta features.
3. For API examples, keep snippets small and verify names against installed docs/source when working inside a project.
4. For deeper examples and operational patterns, consult [full-reference.md](references/full-reference.md). Treat its older version notes as historical if they conflict with this file.

## Common Guidance

- Batch writes; avoid single-row insert loops unless latency is more important than fragment count.
- Build vector indexes after enough data exists; small datasets often do not need ANN indexes.
- Use scalar indexes for frequent filters and combine filters with vector search to reduce candidate sets.
- Use full-text or hybrid search when natural language relevance matters, not only nearest-neighbor distance.
- Use `list_tables()` rather than deprecated `table_names()`.
- Use session-level cache configuration rather than deprecated per-table `index_cache_size`.
- On object storage, account for serial request chains; latency is often bounded by metadata, index, and data-page round trips.

## Update Checklist

- Confirm latest `lance-format/lance` release before changing SDK guidance.
- Confirm latest stable `lancedb` release on PyPI before changing Python guidance.
- Keep this `SKILL.md` concise; move long examples to `references/`.
