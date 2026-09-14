"""
ml/generate_dataset.py — Generate a realistic labeled training dataset for gap classification.

Produces: skill_gap_dataset.csv with columns matching the ML training schema.

Label logic (deterministic):
    gap_pct = max(0, required - current) / required * 100
    LOW    if gap_pct <= 20
    MEDIUM if gap_pct <= 50
    HIGH   if gap_pct >  50

Usage:
    python ml/generate_dataset.py --output ml/skill_gap_dataset.csv --rows 2000
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
    {"name": "Software Developer", "required_avg": 75, "importance_avg": 1.0},
    {"name": "Data Scientist",     "required_avg": 70, "importance_avg": 0.9},
    {"name": "Web Developer",      "required_avg": 68, "importance_avg": 0.85},
    {"name": "Database Admin",     "required_avg": 72, "importance_avg": 0.95},
    {"name": "DevOps Engineer",    "required_avg": 70, "importance_avg": 0.9},
    {"name": "System Analyst",     "required_avg": 65, "importance_avg": 0.8},
]


def _classify(current, required):
    if required <= 0:
        return "LOW"
    gap_pct = max(0, required - current) / required * 100
    if gap_pct <= 20:
        return "LOW"
    if gap_pct <= 50:
        return "MEDIUM"
    return "HIGH"


def generate(n_rows: int = 2000, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    np.random.seed(seed)

    records = []
    for _ in range(n_rows):
        role = random.choice(ROLES)
        category = random.choice(SKILL_CATEGORIES)

        required = np.clip(np.random.normal(role["required_avg"], 10), 40, 100)
        # Bias current proficiency below required for realistic distribution
        current = np.clip(np.random.normal(required * 0.7, 20), 0, 100)

        # Assessment score is correlated with current proficiency
        assessment_score = np.clip(current + np.random.normal(0, 10), 0, 100)

        project_count = max(0, int(np.random.poisson(2)))
        cert_count = max(0, int(np.random.poisson(1)))
        importance = np.clip(
            np.random.normal(role["importance_avg"], 0.15), 0.5, 1.0
        )

        label = _classify(current, required)

        records.append({
            "assessment_score":      round(assessment_score, 2),
            "current_proficiency":   round(current, 2),
            "required_proficiency":  round(required, 2),
            "project_count":         project_count,
            "certification_count":   cert_count,
            "role_importance":       round(importance, 3),
            "skill_category":        category,
            "gap_level":             label,
        })

    df = pd.DataFrame(records)

    # Show label distribution
    print("Label distribution:")
    print(df["gap_level"].value_counts())
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate ML training dataset for gap classification")
    ap.add_argument("--output", default="ml/skill_gap_dataset.csv")
    ap.add_argument("--rows", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    df = generate(n_rows=args.rows, seed=args.seed)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"Dataset saved → {args.output} ({len(df)} rows)")
