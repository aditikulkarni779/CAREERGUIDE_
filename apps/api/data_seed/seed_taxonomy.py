"""Seed the skill taxonomy + target roles + role skill requirements.

Idempotent (upsert by slug). Run against the configured database:

    python -m data_seed.seed_taxonomy
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.db import get_engine
from app.adapters.models import Role, RoleSkillRequirement, Skill, SkillCategory

# (slug, name, category, aliases)
SKILLS: list[tuple[str, str, SkillCategory, list[str]]] = [
    # languages
    ("python", "Python", SkillCategory.language, ["py"]),
    ("java", "Java", SkillCategory.language, []),
    ("javascript", "JavaScript", SkillCategory.language, ["js"]),
    ("typescript", "TypeScript", SkillCategory.language, ["ts"]),
    ("cpp", "C++", SkillCategory.language, ["c++", "cplusplus"]),
    ("go", "Go", SkillCategory.language, ["golang"]),
    ("rust", "Rust", SkillCategory.language, []),
    ("sql", "SQL", SkillCategory.language, []),
    ("r", "R", SkillCategory.language, []),
    # frameworks
    ("react", "React", SkillCategory.framework, ["reactjs"]),
    ("nextjs", "Next.js", SkillCategory.framework, ["next"]),
    ("nodejs", "Node.js", SkillCategory.framework, ["node"]),
    ("django", "Django", SkillCategory.framework, []),
    ("fastapi", "FastAPI", SkillCategory.framework, []),
    ("flask", "Flask", SkillCategory.framework, []),
    ("spring-boot", "Spring Boot", SkillCategory.framework, ["spring"]),
    ("tensorflow", "TensorFlow", SkillCategory.framework, ["tf"]),
    ("pytorch", "PyTorch", SkillCategory.framework, ["torch"]),
    ("scikit-learn", "scikit-learn", SkillCategory.framework, ["sklearn"]),
    # libraries
    ("pandas", "pandas", SkillCategory.library, []),
    ("numpy", "NumPy", SkillCategory.library, []),
    ("langchain", "LangChain", SkillCategory.library, []),
    # databases
    ("postgresql", "PostgreSQL", SkillCategory.db, ["postgres"]),
    ("mysql", "MySQL", SkillCategory.db, []),
    ("mongodb", "MongoDB", SkillCategory.db, ["mongo"]),
    ("redis", "Redis", SkillCategory.db, []),
    ("neo4j", "Neo4j", SkillCategory.db, []),
    ("qdrant", "Qdrant", SkillCategory.db, []),
    # tools
    ("git", "Git", SkillCategory.tool, []),
    ("docker", "Docker", SkillCategory.tool, []),
    ("kubernetes", "Kubernetes", SkillCategory.tool, ["k8s"]),
    ("linux", "Linux", SkillCategory.tool, []),
    ("ci-cd", "CI/CD", SkillCategory.tool, ["cicd"]),
    # cloud
    ("aws", "AWS", SkillCategory.cloud, ["amazon-web-services"]),
    ("gcp", "GCP", SkillCategory.cloud, ["google-cloud"]),
    ("azure", "Azure", SkillCategory.cloud, []),
    # ai
    ("machine-learning", "Machine Learning", SkillCategory.ai, ["ml"]),
    ("deep-learning", "Deep Learning", SkillCategory.ai, ["dl"]),
    ("nlp", "NLP", SkillCategory.ai, ["natural-language-processing"]),
    ("llm", "LLMs", SkillCategory.ai, ["large-language-models"]),
    ("rag", "RAG", SkillCategory.ai, ["retrieval-augmented-generation"]),
    ("mlops", "MLOps", SkillCategory.ai, []),
    ("computer-vision", "Computer Vision", SkillCategory.ai, ["cv"]),
    # soft
    ("communication", "Communication", SkillCategory.soft, []),
    ("problem-solving", "Problem Solving", SkillCategory.soft, []),
    ("teamwork", "Teamwork", SkillCategory.soft, []),
]

# role slug -> display name
ROLES: dict[str, str] = {
    "ml-engineer": "ML Engineer",
    "data-scientist": "Data Scientist",
    "ai-engineer": "AI Engineer",
    "software-engineer": "Software Engineer",
    "backend-developer": "Backend Developer",
    "frontend-developer": "Frontend Developer",
    "full-stack-developer": "Full Stack Developer",
    "data-engineer": "Data Engineer",
}

# role slug -> list of (skill slug, importance, typical_proficiency, difficulty)
REQUIREMENTS: dict[str, list[tuple[str, int, int, int]]] = {
    "ml-engineer": [
        ("python", 95, 80, 40), ("machine-learning", 95, 80, 70),
        ("deep-learning", 85, 70, 75), ("pytorch", 80, 65, 65),
        ("scikit-learn", 75, 70, 45), ("sql", 70, 65, 35),
        ("mlops", 70, 55, 65), ("docker", 65, 60, 45), ("aws", 60, 55, 55),
    ],
    "data-scientist": [
        ("python", 95, 80, 40), ("sql", 85, 75, 35), ("pandas", 85, 75, 40),
        ("numpy", 80, 70, 40), ("machine-learning", 90, 75, 70),
        ("r", 50, 50, 45), ("communication", 70, 65, 40),
    ],
    "ai-engineer": [
        ("python", 95, 80, 40), ("llm", 90, 70, 65), ("rag", 85, 65, 60),
        ("langchain", 75, 60, 50), ("machine-learning", 80, 70, 70),
        ("fastapi", 70, 60, 40), ("docker", 65, 60, 45), ("aws", 60, 55, 55),
    ],
    "software-engineer": [
        ("java", 70, 70, 45), ("python", 70, 70, 40), ("git", 85, 75, 25),
        ("sql", 70, 65, 35), ("problem-solving", 85, 75, 55),
        ("docker", 60, 55, 45), ("ci-cd", 60, 55, 45),
    ],
    "backend-developer": [
        ("python", 80, 75, 40), ("fastapi", 70, 65, 40), ("sql", 85, 75, 35),
        ("postgresql", 75, 65, 45), ("redis", 55, 50, 40), ("docker", 70, 60, 45),
        ("git", 80, 75, 25), ("ci-cd", 60, 55, 45),
    ],
    "frontend-developer": [
        ("javascript", 90, 80, 40), ("typescript", 80, 70, 45),
        ("react", 90, 80, 50), ("nextjs", 70, 60, 50), ("git", 80, 75, 25),
        ("communication", 60, 60, 40),
    ],
    "full-stack-developer": [
        ("javascript", 85, 75, 40), ("typescript", 75, 65, 45),
        ("react", 80, 70, 50), ("nodejs", 75, 65, 45), ("sql", 75, 65, 35),
        ("postgresql", 65, 55, 45), ("docker", 60, 55, 45), ("git", 80, 75, 25),
    ],
    "data-engineer": [
        ("python", 85, 75, 40), ("sql", 95, 85, 35), ("postgresql", 75, 65, 45),
        ("docker", 65, 60, 45), ("aws", 70, 60, 55), ("mlops", 50, 45, 60),
        ("linux", 60, 55, 40),
    ],
}


def _upsert_skill(
    db: Session, slug: str, name: str, cat: SkillCategory, aliases: list[str]
) -> Skill:
    skill = db.scalar(select(Skill).where(Skill.slug == slug))
    if skill is None:
        skill = Skill(slug=slug, name=name, category=cat, aliases=aliases)
        db.add(skill)
    else:
        skill.name, skill.category, skill.aliases = name, cat, aliases
    return skill


def seed() -> None:
    from sqlalchemy.orm import sessionmaker

    engine = get_engine()
    with sessionmaker(bind=engine)() as db:
        skills: dict[str, Skill] = {}
        for slug, name, cat, aliases in SKILLS:
            skills[slug] = _upsert_skill(db, slug, name, cat, aliases)
        db.flush()

        roles: dict[str, Role] = {}
        for slug, name in ROLES.items():
            role = db.scalar(select(Role).where(Role.slug == slug))
            if role is None:
                role = Role(slug=slug, name=name)
                db.add(role)
            else:
                role.name = name
            roles[slug] = role
        db.flush()

        for role_slug, reqs in REQUIREMENTS.items():
            role = roles[role_slug]
            for skill_slug, imp, typ, diff in reqs:
                skill = skills[skill_slug]
                existing = db.scalar(
                    select(RoleSkillRequirement).where(
                        RoleSkillRequirement.role_id == role.id,
                        RoleSkillRequirement.skill_id == skill.id,
                    )
                )
                if existing is None:
                    db.add(
                        RoleSkillRequirement(
                            role_id=role.id, skill_id=skill.id,
                            importance=imp, typical_proficiency=typ, difficulty=diff,
                        )
                    )
                else:
                    existing.importance, existing.typical_proficiency, existing.difficulty = (
                        imp, typ, diff,
                    )
        db.commit()
        print(f"seeded {len(SKILLS)} skills, {len(ROLES)} roles, "
              f"{sum(len(v) for v in REQUIREMENTS.values())} requirements")


if __name__ == "__main__":
    seed()
