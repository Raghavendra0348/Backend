"""
ml/train.py — Train and evaluate ML gap classification models.

Models trained:
  - Logistic Regression (interpretable baseline)
  - Decision Tree
  - Random Forest

Evaluation: Accuracy, Precision, Recall, F1 (macro & weighted), Confusion Matrix.
Best model by weighted F1 is saved as skill_gap_model.joblib.
Metrics saved as ml/metrics_report.json.

Usage:
    python ml/train.py --input ml/skill_gap_dataset.csv --output ml/models/skill_gap_model.joblib
"""
import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, f1_score
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

NUMERIC_FEATURES = [
    "assessment_score",
    "current_proficiency",
    "required_proficiency",
    "project_count",
    "certification_count",
    "role_importance",
]
CATEGORICAL_FEATURES = ["skill_category"]
TARGET = "gap_level"
CLASSES = ["LOW", "MEDIUM", "HIGH"]


def build_pipeline(clf) -> Pipeline:
    """Build an sklearn Pipeline with preprocessing + classifier."""
    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
    ])
    cat_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot",  OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    preprocessor = ColumnTransformer([
        ("num", numeric_pipe, NUMERIC_FEATURES),
        ("cat", cat_pipe,     CATEGORICAL_FEATURES),
    ])
    return Pipeline([
        ("preprocess",  preprocessor),
        ("classifier",  clf),
    ])


def evaluate(name: str, pipeline: Pipeline, X_te, y_te) -> dict:
    """Run evaluation on held-out test set. Returns metrics dict."""
    y_pred = pipeline.predict(X_te)
    acc = accuracy_score(y_te, y_pred)
    report = classification_report(y_te, y_pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_te, y_pred, labels=CLASSES).tolist()
    f1_w = f1_score(y_te, y_pred, average="weighted", zero_division=0)

    print(f"\n{'='*55}")
    print(f"  {name}")
    print(f"{'='*55}")
    print(f"  Accuracy:          {acc:.4f}")
    print(f"  F1 (weighted):     {f1_w:.4f}")
    print(f"\nClassification Report:")
    print(classification_report(y_te, y_pred, labels=CLASSES, zero_division=0))
    print("Confusion Matrix (rows=actual, cols=predicted):")
    print(f"  Labels: {CLASSES}")
    for row in cm:
        print(f"  {row}")

    return {
        "model": name,
        "accuracy": round(acc, 4),
        "f1_weighted": round(f1_w, 4),
        "classification_report": report,
        "confusion_matrix": {"labels": CLASSES, "matrix": cm},
    }


def main():
    ap = argparse.ArgumentParser(description="Train ML skill gap classifiers")
    ap.add_argument("--input",  required=True,  help="Path to training CSV")
    ap.add_argument("--output", default="ml/models/skill_gap_model.joblib",
                    help="Output path for best model (.joblib)")
    ap.add_argument("--test-size", type=float, default=0.2)
    ap.add_argument("--seed",  type=int, default=42)
    args = ap.parse_args()

    # ── Load data ──────────────────────────────────────────────────────────
    print(f"Loading dataset: {args.input}")
    df = pd.read_csv(args.input)

    missing = [c for c in NUMERIC_FEATURES + CATEGORICAL_FEATURES + [TARGET]
               if c not in df.columns]
    if missing:
        print(f"ERROR: Missing columns: {missing}")
        sys.exit(1)

    print(f"Dataset: {len(df)} rows, label distribution:")
    print(df[TARGET].value_counts())

    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df[TARGET]

    # ── Train/test split ───────────────────────────────────────────────────
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=args.test_size, random_state=args.seed, stratify=y
    )
    print(f"\nTrain: {len(X_tr)} rows | Test: {len(X_te)} rows")

    # ── Candidate models ───────────────────────────────────────────────────
    candidates = {
        "Logistic Regression": build_pipeline(
            LogisticRegression(max_iter=1000, class_weight="balanced",
                               random_state=args.seed)
        ),
        "Decision Tree": build_pipeline(
            DecisionTreeClassifier(max_depth=8, class_weight="balanced",
                                   random_state=args.seed)
        ),
        "Random Forest": build_pipeline(
            RandomForestClassifier(n_estimators=200, max_depth=12,
                                   class_weight="balanced", n_jobs=-1,
                                   random_state=args.seed)
        ),
    }

    # ── Train and evaluate all models ──────────────────────────────────────
    metrics_all = []
    trained_pipelines = {}

    for name, pipeline in candidates.items():
        print(f"\nTraining {name}...")
        pipeline.fit(X_tr, y_tr)
        trained_pipelines[name] = pipeline

        # 5-fold CV for robustness check
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=args.seed)
        cv_scores = cross_val_score(pipeline, X_tr, y_tr, cv=cv,
                                    scoring="f1_weighted")
        print(f"  5-Fold CV F1 (weighted): {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

        m = evaluate(name, pipeline, X_te, y_te)
        m["cv_f1_mean"] = round(float(cv_scores.mean()), 4)
        m["cv_f1_std"]  = round(float(cv_scores.std()),  4)
        metrics_all.append(m)

    # ── Select best model ──────────────────────────────────────────────────
    best = max(metrics_all, key=lambda x: x["f1_weighted"])
    best_pipeline = trained_pipelines[best["model"]]
    print(f"\n✓ Best model: {best['model']} (F1 weighted = {best['f1_weighted']:.4f})")

    # ── Save model ─────────────────────────────────────────────────────────
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_pipeline, str(out_path))
    print(f"✓ Model saved → {out_path}")

    # ── Save metrics report ─────────────────────────────────────────────────
    metrics_path = out_path.parent / "metrics_report.json"
    report = {
        "dataset": args.input,
        "n_train": len(X_tr),
        "n_test":  len(X_te),
        "best_model": best["model"],
        "models": metrics_all,
    }
    with open(str(metrics_path), "w") as mf:
        json.dump(report, mf, indent=2)
    print(f"✓ Metrics report → {metrics_path}")


if __name__ == "__main__":
    main()
