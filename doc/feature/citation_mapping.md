---
type: feature
title: Citation Mapping in Retrieval Results
description: Track and display document sources for search results and LLM answers across a 6-layer pipeline, enabling users to trace each cited claim to its original source.
resource: retrieval/search.py::SearchService._enrich_with_citations() + extract_citations_from_answer(); main.py::display_results()
tags: retrieval, citations, rag, metadata, grounding
status: stable
---

# Citation Mapping in Retrieval Results

## Purpose

Enable full traceability from LLM-generated answers back to source documents. Users see which result each LLM statement cites ([1], [2], etc.) and can instantly access the source document and document_id.

## Architecture (6 Layers)

**Layer 1: Metadata Extraction**
- `SearchService._enrich_with_citations()` extracts `source` and `document_id` from Qdrant payload metadata on each reranked result
- Wraps metadata in a `citation` dict for downstream layers: `{"source": "...", "document_id": "...", "rank": i}`

**Layer 2: Chunk-Level Citation Markers**
- `SearchService.answer()` appends source marker to each chunk before sending to LLM: `"[i] {chunk} [Source: {source}]"`
- LLM sees numbered chunks with explicit source attribution

**Layer 3: Result Struct Enrichment**
- Each result dict gains `citation_index` (1-indexed rank) and `citation` subdictionary
- Persists through to CLI display layer

**Layer 4: LLM Prompt Injection**
- `SearchService.answer()` includes explicit instruction: "When citing information, include the source number in brackets like [1], [2], etc."
- Encourages LLM to emit inline citations using chunk indices

**Layer 5: Citation Parsing**
- `SearchService.extract_citations_from_answer()` parses regex `\[(\d+)\]` from LLM answer
- Filters to valid 1-indexed range (1 ≤ idx ≤ num_results)
- Returns list of cited indices in order found

**Layer 6: CLI Citation Display**
- `main.py::main()` extracts cited indices from answer text, then prints each citation in a summary block:
  ```
  Citations found in answer: [1, 3]
     [1] {citation['source']} (doc_id: {citation['document_id']})
     [3] {citation['source']} (doc_id: {citation['document_id']})
  ```
- Results section also shows `[i] {source} (doc_id: {doc_id})` per result

## Data Flow

```
Reranked result dict
  ↓
_enrich_with_citations() — add citation dict (Layer 1)
  ↓
search() returns enriched results
  ↓
main() passes citations list to answer() (Layer 2)
  ↓
answer() injects source markers into chunks (Layer 2)
  ↓
LLM streams answer with inline [N] citations (Layer 4)
  ↓
extract_citations_from_answer() parses [N] (Layer 5)
  ↓
main() prints citation summary (Layer 6)
```

## Backward Compatibility

- `SearchService.answer()` accepts optional `citations` parameter; if None, no source markers are appended (graceful degrade)
- `extract_citations_from_answer()` is a static method, works on any answer text (no state dependency)
- Existing result dicts without `citation` key safely fallback to `result.get("citation", {})` (returns empty dict, `.get("source")` returns None)

## Testing

25 unit tests cover:
- Extraction with boundary filtering (out-of-range [0], [999] ignored)
- Metadata enrichment with None handling (missing source/doc_id default to "Unknown"/"N/A")
- Backward-compatible `answer()` signature (optional citations=None)
- End-to-end integration (parse realistic LLM answer with mixed [1], [2] patterns)

## Related

- [Search Service + Main REPL](search_service.md) — orchestrates the full citation pipeline
- [Hybrid Search Retrieval](hybrid_search_retrieval.md) — produces the reranked results that citation mapping enriches
- [Qdrant Infrastructure](qdrant_infrastructure.md) — stores source/document_id in payload metadata
