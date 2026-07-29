---
name: lance
description: Design, index, query, and tune Lance datasets and LanceDB tables for ML and AI workloads. Use for vector index selection such as IVF_PQ or IVF_HNSW_FLAT, ANN recall and latency tuning, full-text and hybrid search, scalar indexes and prefiltering, dataset versioning and compaction, embedding and multimodal storage, slow vector search on object storage, or migrating ML data from Parquet. Covers both the pylance format and the lancedb API.
license: MIT
---

# Lance Data Format Expert

## Scope

Design, debugging, and optimization of Lance and LanceDB systems for ML-native
data, embeddings, vector retrieval, and multimodal storage.

Covers the Lance format and LanceDB specifically. For general lakehouse table
formats use the `iceberg` or `paimon` skills.

## Current Facts

- **Lance SDK / file-format project:** v7.0.0 stable, released May 27, 2026.
- **LanceDB Python:** v0.33.0 stable, released May 28, 2026. v0.33.1-beta.0 exists; do not treat beta as the default stable recommendation.
- **Python packages:** install `pylance` for the Lance format and `lancedb` for the embedded/vector database API.
- **Python support:** LanceDB wheels target CPython 3.9+; confirm package metadata before pinning in production.
- **Recent additions:** MemWAL/LSM write paths, materialized view API, formal catalog/namespace/table/index specs, branch/tag metadata maps, segmented BTree indices, distributed bitmap index build, FTS segment merging, serializable scalar-index caches, and nested blob export fixes.
- **LanceDB recent additions:** `IVF_HNSW_FLAT` vector index type, model-backed FTS tokenizers, and sync `create_index` API alignment with async.

## Inspect First

Establish before recommending or changing anything:

1. Whether this is a **Lance format** question (`pylance`, `.lance`, dataset
   versioning, storage layout) or a **LanceDB** question (`lancedb`, tables,
   search, indexes, reranking). The APIs differ.
2. Installed versions of both packages, and verify API names against the
   installed version before writing detailed code.
3. Row count, vector dimensionality, and fragment count. Whether an index is
   needed at all depends on these.
4. Storage location. Object storage changes the latency model completely.
5. For search-quality complaints, the current index type and parameters and the
   measured recall, before changing anything.

## Decision Rules

- Build a vector index only once the dataset is large enough to need one.
  Brute-force search on a small dataset is often faster and always exact.
- Choose the index for the constraint: IVF_PQ for large memory-constrained
  datasets at some recall cost, IVF_HNSW_FLAT for higher recall at higher
  memory cost.
- Add scalar indexes on frequently filtered columns and combine filtering with
  vector search to shrink the candidate set.
- Use full-text or hybrid search when relevance depends on language rather than
  on vector distance alone.
- Batch writes. Each write creates a fragment, and fragment count drives read
  amplification.
- On object storage, expect latency bounded by serial metadata, index, and
  data-page round trips rather than by bandwidth.
- Prefer `list_tables()` over the deprecated `table_names()`, and session-level
  cache configuration over the deprecated per-table `index_cache_size`.

## Safety

- Compaction and version cleanup permanently drop older dataset versions and
  the ability to time travel to them. Confirm nothing pins an old version
  first.
- Overwrite mode replaces the table rather than appending. Confirm the intended
  write mode against an existing table.
- Rebuilding an index on a large dataset is expensive in time and memory. State
  the expected cost before starting one.
- Keep object storage credentials out of code and notebooks; use environment
  variables or platform secrets.

## Verify

- After building an index, confirm it exists and that query latency actually
  changed. Do not assume the index is being used.
- Measure recall against a brute-force baseline on a sample before accepting an
  ANN configuration. Report the measured number.
- After compaction, compare fragment count and query latency before and after.
- Report row count, index type and parameters, and measured latency and recall,
  rather than claiming an index should help.

## Update Checklist

- Confirm latest `lance-format/lance` release before changing SDK guidance.
- Confirm latest stable `lancedb` release on PyPI before changing Python guidance.
