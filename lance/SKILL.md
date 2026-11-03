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

Release guidance checked on **2026-11-03**. Recheck the linked sources before
selecting versions for a new deployment; preserve existing project pins.

- **Lance SDK:** v14.0.2 and `pylance` 14.0.2, released October 29, 2026. v15 betas and v14.0.3 release candidates are not stable releases. SDK versions are distinct from the on-disk format version.
- **LanceDB Python:** 0.41.0, released October 29, 2026; this release uses Lance 14.0.2.
- **The Lance repository moved** from `lancedb/lance` to `lance-format/lance`, with homepage `lance.org`. The old URL redirects.
- **Verify releases per package.** Historical LanceDB tags differ across languages; current `v0.41.0` notes also cover Python. Check PyPI for Python availability instead of inferring it from a tag prefix.
- **Python packages:** install `pylance` for the Lance format and `lancedb` for the embedded/vector database API. The bare `lance` name on PyPI is an unrelated package by a different author. `lancedb-compat` is a same-API wheel for pre-Haswell x86_64 hosts without AVX2.
- **Python support:** both packages declare `requires-python >=3.10`. The `cp39-abi3` wheel tag is an ABI compatibility marker, not an install gate, so 3.9 does not work despite what the filename suggests.
- **Vector index types:** `IVF_FLAT`, `IVF_SQ`, `IVF_PQ`, `IVF_HNSW_SQ`, `IVF_HNSW_PQ`, `IVF_HNSW_FLAT`, and `IVF_RQ`.
- **LanceDB 0.41 migration:** table metadata no longer implicitly authorizes remote-code embedding models or custom endpoints. Explicitly approve trusted models/revisions and endpoints through the embedding registry; do not bypass `UntrustedEmbeddingConfigError` indiscriminately. Local computed columns and materialized views require an experimental build feature absent from published Python and Node packages.

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
- Choose the index for the binding constraint: IVF_PQ for large
  memory-constrained datasets at some recall cost, IVF_HNSW_FLAT for higher
  recall at higher memory cost, IVF_RQ when memory reduction matters more than
  either.
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

- Lance `dataset.optimize.compact_files()` rewrites fragments and creates a
  new version; it preserves old versions and the files they reference.
- `cleanup_old_versions()` removes eligible historical versions and files,
  ending time travel to those versions. Check retention and active readers
  before cleanup. Do not enable `delete_unverified=True` while writers run.
- LanceDB `table.optimize()` can combine compaction, index maintenance, and
  version cleanup. Inspect that API's cleanup options for the installed version
  before running it; it is not equivalent to Lance's compaction-only call.
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
- Check retained versions separately from fragment counts. Compaction alone
  does not establish that historical storage was reclaimed.
- Report row count, index type and parameters, and measured latency and recall,
  rather than claiming an index should help.

## Update Checklist

- Confirm latest `lance-format/lance` release before changing SDK guidance.
- Confirm stable Python releases on PyPI and match their release notes; do not
  rely on tag naming conventions to identify the language package.

## Sources

- [Lance 14.0.2 release](https://github.com/lance-format/lance/releases/tag/v14.0.2)
- [LanceDB 0.41.0 release and migration notes](https://github.com/lancedb/lancedb/releases/tag/v0.41.0)
- [pylance package](https://pypi.org/project/pylance/) and [lancedb package](https://pypi.org/project/lancedb/)
- [Lance compaction and version cleanup](https://lance.org/guide/read_and_write/)
- [LanceDB Python maintenance API](https://lancedb.github.io/lancedb/python/python/)
