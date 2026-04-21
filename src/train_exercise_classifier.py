from __future__ import annotations

import argparse
import os
from typing import Dict

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression

from utils import (
    FEATURE_COLUMNS,
    compute_classification_metrics,
    ensure_dir,
    load_angle_csv,
    plot_confusion_matrix,
    plot_feature_importance,
    prepare_features,
    save_classification_report_text,
    save_json,
    save_model_bundle,
)


def build_model(model_name: str):
    model_name = model_name.lower()
    if model_name == "random_forest":
        return Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=300,
                        max_depth=None,
                        min_samples_split=2,
                        min_samples_leaf=1,
                        class_weight="balanced",
                        random_state=42,
                        n_jobs=-1,
                    ),
                ),
            ]
        )
    if model_name == "mlp":
        return Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    MLPClassifier(
                        hidden_layer_sizes=(128, 64),
                        activation="relu",
                        max_iter=300,
                        random_state=42,
                        early_stopping=True,
                    ),
                ),
            ]
        )
    if model_name == "logreg":
        return Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
            ]
        )
    raise ValueError(f"Unsupported model_name: {model_name}")



def main() -> None:
    parser = argparse.ArgumentParser(description="Train exercise classifier from angle-feature CSV")
    parser.add_argument("--csv", type=str, required=True, help="Path to exercise_angles_preprocessed.csv")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory to save outputs")
    parser.add_argument(
        "--model_name",
        type=str,
        default="random_forest",
        choices=["random_forest", "mlp", "logreg"],
        help="Model type",
    )
    parser.add_argument("--test_size", type=float, default=0.2)
    parser.add_argument("--val_size", type=float, default=0.1)
    args = parser.parse_args()

    ensure_dir(args.output_dir)

    df = load_angle_csv(args.csv)
    X, y = prepare_features(df)

    # Because the provided CSV has no subject_id or sequence_id, this split is row-based.
    # It is valid for a baseline, but weaker than subject-wise splitting for publication-grade work.
    X_trainval, X_test, y_trainval, y_test = train_test_split(
        X, y, test_size=args.test_size, stratify=y, random_state=42
    )

    val_adjusted = args.val_size / (1.0 - args.test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_trainval, y_trainval, test_size=val_adjusted, stratify=y_trainval, random_state=42
    )

    model = build_model(args.model_name)
    model.fit(X_train, y_train)

    y_val_pred = model.predict(X_val)
    y_test_pred = model.predict(X_test)

    labels = sorted(y.unique().tolist())
    val_metrics = compute_classification_metrics(y_val, y_val_pred)
    test_metrics = compute_classification_metrics(y_test, y_test_pred)

    bundle = {
        "model": model,
        "feature_columns": X.columns.tolist(),
        "labels": labels,
        "target_column": "Label",
        "notes": {
            "dataset_limitation": "Row-level split used because the CSV lacks subject or sequence identifiers.",
            "suitable_for": "Exercise-type classification baseline",
            "not_sufficient_for": "Correct-vs-incorrect form classification without additional labels",
        },
    }

    save_model_bundle(bundle, os.path.join(args.output_dir, "model.joblib"))
    X_test.assign(Label=y_test).to_csv(os.path.join(args.output_dir, "test_split.csv"), index=False)
    X_val.assign(Label=y_val).to_csv(os.path.join(args.output_dir, "val_split.csv"), index=False)
    X_train.assign(Label=y_train).to_csv(os.path.join(args.output_dir, "train_split.csv"), index=False)

    save_json(val_metrics, os.path.join(args.output_dir, "val_metrics.json"))
    save_json(test_metrics, os.path.join(args.output_dir, "test_metrics.json"))
    save_classification_report_text(y_val, y_val_pred, os.path.join(args.output_dir, "val_report.txt"))
    save_classification_report_text(y_test, y_test_pred, os.path.join(args.output_dir, "test_report.txt"))
    plot_confusion_matrix(y_test, y_test_pred, labels, os.path.join(args.output_dir, "test_confusion_matrix.png"))

    clf = model.named_steps["classifier"]
    plot_feature_importance(clf, X.columns.tolist(), os.path.join(args.output_dir, "feature_importance.png"))

    summary = {
        "rows": int(len(df)),
        "features_used": X.columns.tolist(),
        "labels": labels,
        "class_counts": df["Label"].value_counts().to_dict(),
        "model_name": args.model_name,
        "validation": {k: v for k, v in val_metrics.items() if k != "report"},
        "test": {k: v for k, v in test_metrics.items() if k != "report"},
    }
    save_json(summary, os.path.join(args.output_dir, "run_summary.json"))

    print("Training complete.")
    print(f"Saved outputs to: {args.output_dir}")
    print("Test metrics:")
    print({k: v for k, v in test_metrics.items() if k != "report"})


if __name__ == "__main__":
    main()
