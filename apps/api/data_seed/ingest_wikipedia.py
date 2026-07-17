"""Ingest a real KB: Wikipedia articles for every taxonomy skill + target role.

    python -m data_seed.ingest_wikipedia

Recreates the roadmap_kb collection with: the curated role roadmap blurbs +
a capped Wikipedia extract per skill and per role. Content is CC BY-SA 4.0;
each chunk keeps its article URL for citation/attribution.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select

from app.adapters.db import new_session
from app.adapters.models import Role, Skill
from app.core.config import get_settings
from app.rag.factory import build_dense_embedder, build_sparse_embedder, build_vector_store
from app.rag.ingest import ingest_documents
from app.rag.sources.wikipedia import fetch_best, fetch_extracts_batch
from data_seed.seed_rag import COLLECTION
from data_seed.seed_rag import DOCS as ROLE_DOCS

# Skills whose Wikipedia title differs from the display name.
SKILL_TITLE_OVERRIDES: dict[str, str] = {
    "go": "Go (programming language)",
    "r": "R (programming language)",
    "rust": "Rust (programming language)",
    "python": "Python (programming language)",
    "java": "Java (programming language)",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "cpp": "C++",
    "sql": "SQL",
    "react": "React (software)",
    "nextjs": "Next.js",
    "nodejs": "Node.js",
    "aws": "Amazon Web Services",
    "gcp": "Google Cloud Platform",
    "azure": "Microsoft Azure",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "nlp": "Natural language processing",
    "llm": "Large language model",
    "rag": "Retrieval-augmented generation",
    "mlops": "MLOps",
    "computer-vision": "Computer vision",
    "machine-learning": "Machine learning",
    "deep-learning": "Deep learning",
    "ci-cd": "CI/CD",
    "scikit-learn": "Scikit-learn",
    "pandas": "Pandas (software)",
    "numpy": "NumPy",
}

# Roles mapped to a relevant Wikipedia article.
ROLE_TITLES: dict[str, str] = {
    "ml-engineer": "Machine learning",
    "data-scientist": "Data science",
    "ai-engineer": "Artificial intelligence",
    "software-engineer": "Software engineering",
    "backend-developer": "Web development",
    "frontend-developer": "Front-end web development",
    "full-stack-developer": "Programmer",
    "data-engineer": "Data engineering",
}


def main() -> None:
    settings = get_settings()
    dense = build_dense_embedder(settings)
    sparse = build_sparse_embedder(settings)
    store = build_vector_store(settings, dense.dim)
    store.recreate_collection(COLLECTION)

    docs: list[dict[str, Any]] = list(ROLE_DOCS)  # keep curated role blurbs
    fetched = skipped = 0

    with new_session() as db:
        skills = list(db.scalars(select(Skill)))
        roles = list(db.scalars(select(Role)))

    # Batch-fetch full articles (few requests, no throttle), then search-resolve misses.
    skill_titles = {s.slug: SKILL_TITLE_OVERRIDES.get(s.slug, s.name) for s in skills}
    batch = fetch_extracts_batch(list(skill_titles.values()))

    for skill in skills:
        title = skill_titles[skill.slug]
        result = batch.get(title) or fetch_best(skill.name, SKILL_TITLE_OVERRIDES.get(skill.slug))
        if result is None:
            skipped += 1
            continue
        text, url = result
        docs.append(
            {
                "text": text,
                "payload": {
                    "title": skill.name,
                    "source": "wikipedia",
                    "url": url,
                    "skill_slug": skill.slug,
                    "category": skill.category.value,
                    "kind": "skill",
                },
            }
        )
        fetched += 1

    role_titles = {r.slug: ROLE_TITLES[r.slug] for r in roles if r.slug in ROLE_TITLES}
    role_batch = fetch_extracts_batch(list(role_titles.values()))
    for role in roles:
        title = ROLE_TITLES.get(role.slug)
        if not title:
            continue
        result = role_batch.get(title) or fetch_best(title)
        if result is None:
            skipped += 1
            continue
        text, url = result
        docs.append(
            {
                "text": text,
                "payload": {
                    "title": f"{role.name} (overview)",
                    "source": "wikipedia",
                    "url": url,
                    "role": role.slug,
                    "kind": "role_ref",
                },
            }
        )
        fetched += 1

    n = ingest_documents(store, dense, sparse, COLLECTION, docs)
    print(
        f"ingested {n} chunks into {settings.qdrant_collection_prefix}_{COLLECTION} "
        f"(wikipedia articles fetched={fetched}, skipped={skipped}, "
        f"curated role docs={len(ROLE_DOCS)})"
    )


if __name__ == "__main__":
    main()
