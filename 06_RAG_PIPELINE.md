# 06 — RAG Pipeline

Project: **AI Career Copilot** · Draft v1.0

---

## 1. Goal
Ground every answer/recommendation in retrievable, citable knowledge — never hallucinate careers advice. Hybrid retrieval + reranking + metadata filtering over curated career knowledge and live market data.

---

## 2. Pipeline Stages

```
Source docs ─▶ Load ─▶ Clean/Normalize ─▶ Chunk ─▶ Embed (dense+sparse)
   ─▶ Upsert Qdrant (+payload) ─▶ [query time] Hybrid search ─▶ Filter
   ─▶ Rerank ─▶ Assemble context ─▶ LLM answer ─▶ Citation ─▶ Verify
```

### 2.1 Ingestion (offline / scheduled)
- **Loaders** per source (course CSV/JSON, arXiv metadata, roadmaps.sh, docs, blogs, job postings).
- **Normalize**: strip boilerplate, language-detect, dedup (minhash/simhash), attach canonical skill tags via Skill Extraction.
- **Chunking**: recursive, ~500–800 tokens, 10–15% overlap; keep structural headers as metadata; one chunk never spans two documents.
- **Embeddings**: Voyage `voyage-3` (dense) + BM25/SPLADE sparse vector. Batched, cached by content hash.
- **Upsert**: Qdrant point = `{id, dense, sparse, payload}`; payload = `{source, type, skills[], difficulty, url, title, date}`; mirror `embedding_ref` into Postgres.

### 2.2 Retrieval (query time)
1. **Query understanding**: rewrite/expand user query (HyDE optional for sparse topics), extract filters (role, skill, difficulty).
2. **Hybrid search**: Qdrant fusion of dense + sparse (RRF), `top_k=40`.
3. **Metadata pre-filter**: restrict by skill/type/recency (e.g., jobs `posted_at > 90d`).
4. **Rerank**: Voyage/bge reranker → `top_n=6–8`.
5. **Context assembly**: dedup, order by relevance, budget to token cap, attach source ids for citation.

---

## 3. Knowledge Sources → Collections
| Source | Collection | Refresh |
|--------|-----------|---------|
| Coursera/Udemy/edX catalogs | `resources` | weekly |
| Roadmaps.sh, career guides | `roadmap_kb` | monthly |
| arXiv / Semantic Scholar | `docs_kb` | weekly |
| Blogs / docs / books | `docs_kb` | monthly |
| Interview question banks | `interview_kb` | monthly |
| Job postings (live) | `jobs` | nightly |
| Per-user long-term memory | `user_memory` | on write |

---

## 4. Citation & Grounding
- Retrieved chunks carry stable `source_id` + `url`.
- Citation agent maps answer claims → chunk ids; output includes `citations:[{title,url,snippet}]`.
- Verification agent flags any claim without supporting chunk → forces regenerate or hedge.

---

## 5. Long-Term Conversational Memory
- Summarize completed conversations → embed → `user_memory` (filtered by `user_id`).
- On new chat, retrieve top user-memory + Twin snapshot → personalized grounding.
- Short-term memory = last N turns in state; long-term = retrieved.

---

## 6. Evaluation (RAG quality)
- **Ragas / DeepEval** metrics: context precision, context recall, faithfulness, answer relevancy.
- Golden Q/A set per domain (ML eng, SWE, data eng…) run in CI on retrieval changes.
- Track hallucination rate + citation coverage as release gates.

---

## 7. Performance & Cost
- Cache: embedding cache (content hash), retrieval cache (query+filter hash), semantic answer cache.
- Batch embeds; async retrieval; prefilter before rerank to cut reranker load.
- Prompt caching on stable system/context prefixes.

---

## 8. Interfaces (ports)
```python
class Embedder(Protocol):        def embed(texts) -> list[Vector]
class VectorStore(Protocol):     def hybrid_search(q, filters, k) -> list[Chunk]
                                 def upsert(points) -> None
class Reranker(Protocol):        def rerank(query, chunks, n) -> list[Chunk]
class Retriever:                 # orchestrates the above; only class agents call
```
Vendor SDKs live in adapters; domain depends on protocols only (swap Voyage↔BGE, Qdrant↔alt).
