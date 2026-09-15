"""
ml/generate_dataset.py — Generate a realistic labeled training dataset for gap classification.

Produces: skill_gap_dataset.csv with columns matching the ML training schema.

Label logic (deterministic — matches gap_engine.py thresholds):
    gap_pct = max(0, required - current) / required * 100
    LOW    if gap_pct <= 20
    MEDIUM if gap_pct <= 50
    HIGH   if gap_pct >  50

New in v2:
  - gap_percent added as an explicit feature (most predictive signal)
  - Default rows increased to 5,000
  - More realistic class distribution (HIGH-skewed for students)
  - Edge case sampling (boundary students, zero-gap experts)

Usage:
    python ml/generate_dataset.py --output ml/skill_gap_dataset.csv --rows 5000
"""
import argparse
import random
from pathlib import Path

import pandas as pd
import numpy as np

SKILL_CATEGORIES = [
    "Programming", "Database", "DevOps", "Backend", "Testing",
    "Software Engineering", "Artificial Intelligence", "Data Science",
    "Security", "General",
]

ROLES = [
    {"name": "Software Developer",  "required_avg": 75, "importance_avg": 1.0},
    {"name": "Data Scientist",       "required_avg": 70, "importance_avg": 0.9},
    {"name": "Web Developer",        "required_avg": 68, "importance_avg": 0.85},
    {"name": "Database Admin",       "required_avg": 72, "importance_avg": 0.95},
    {"name": "DevOps Engineer",      "required_avg": 70, "importance_avg": 0.9},
    {"name": "System Analyst",       "required_avg": 65, "importance_avg": 0.8},
    {"name": "ML Engineer",          "required_avg": 78, "importance_avg": 1.0},
    {"name": "Cloud Architect",      "required_avg": 80, "importance_avg": 1.0},
]

# Student archetypes for realistic distribution
ARCHETYPES = [
    # (name, current_bias, weight)
    ("beginner",      0.30, 0.30),   # 30% of students — low skills, large gaps (HIGH)
    ("intermediate",  0.60, 0.40),   # 40% — moderate skills (MEDIUM/HIGH)
    ("advanced",      0.85, 0.20),   # 20% — near-expert (LOW/MEDIUM)
    ("expert",        1.00, 0.10),   # 10% — meets or exceeds requirement (LOW/no gap)
]


def _classify(current: float, required: float) -> str:
    if required <= 0:
        return "LOW"
    gap_pct = max(0.0, required - current) / required * 100.0
    if gap_pct <= 20.0:
        return "LOW"
    if gap_pct <= 50.0:
        return "MEDIUM"
    return "HIGH"


def generate(n_rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    np.random.seed(seed)

    records = []
    archetype_names   = [a[0] for a in ARCHETYPES]
    archetype_weights = np.array([a[2] for a in ARCHETYPES])
    archetype_weights /= archetype_weights.sum()

    for _ in range(n_rows):
        role     = random.choice(ROLES)
        category = random.choice(SKILL_CATEGORIES)

        # Pick archetype
        arch_idx = np.random.choice(len(ARCHETYPES), p=archetype_weights)
        bias     = ARCHETYPES[arch_idx][1]

        required = np.clip(
            np.random.normal(role["required_avg"], 8), 40, 100
        )

        # Current proficiency based on archetype bias relative to required
        current = np.clip(
            np.random.normal(required * bias, 12), 0, 100
        )

        # Add boundary-hugging samples for better threshold learning
        if random.random() < 0.05:
            # Sample near the LOW/MEDIUM boundary (gap_pct ≈ 20%)
            current = required * 0.80 + np.random.normal(0, 3)
        elif random.random() < 0.05:
            # Sample near the MEDIUM/HIGH boundary (gap_pct ≈ 50%)
            current = required * 0.50 + np.random.normal(0, 3)

        current = float(np.clip(current, 0, 100))
        required = float(np.clip(required, 40, 100))

        # Compute gap_percent explicitly (key feature)
        gap_pct = max(0.0, required - current) / required * 100.0 if required > 0 else 0.0

        # Assessment score: correlated with current proficiency + noise
        assessment_score = float(np.clip(
            current + np.random.normal(0, 8), 0, 100
        ))

        project_count  = max(0, int(np.random.poisson(2.0 * bias)))
        cert_count     = max(0, int(np.random.poisson(1.0 * bias)))
        importance     = float(np.clip(
            np.random.normal(role["importance_avg"], 0.12), 0.5, 1.0
        ))

        label = _classify(current, required)

        records.append({
            "assessment_score":     round(assessment_score, 2),
            "current_proficiency":  round(current, 2),
            "required_proficiency": round(required, 2),
            "gap_percent":          round(gap_pct, 2),          # NEW explicit feature
            "project_count":        project_count,
            "certification_count":  cert_count,
            "role_importance":      round(importance, 3),
            "skill_category":       category,
            "gap_level":            label,
        })

    df = pd.DataFrame(records)
    print(f"Generated {len(df)} rows.")
    print("Label distribution:")
    print(df["gap_level"].value_counts())
    print(f"\nGap percent stats:\n{df['gap_percent'].describe().round(2)}")
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Generate ML training dataset for gap classification (v2)"
    )
    ap.add_argument("--output", default="ml/skill_gap_dataset.csv")
    ap.add_argument("--rows",   type=int, default=5000)
    ap.add_argument("--seed",   type=int, default=42)
    args = ap.parse_args()

    df = generate(n_rows=args.rows, seed=args.seed)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"\nDataset saved → {args.output} ({len(df)} rows)")
