from __future__ import annotations

import argparse
import os

from utils import (
    compute_classification_metrics,
    ensure_dir,
    load_model_bundle,
    plot_confusion_matrix,
    save_classification_report_text,
    save_json,
)
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a saved exercise classifier")
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--test_path", type=str, required=True)
    parser.add_argument("--output_dir", type=str, required=True)
    args = parser.parse_args()

    ensure_dir(args.output_dir)

    bundle = load_model_bundle(args.model_path)
    model = bundle["model"]
    feature_columns = bundle["feature_columns"]
    labels = bundle["labels"]

    df = pd.read_csv(args.test_path)
    X_test = df[feature_columns]
    y_test = df["Label"]

    y_pred = model.predict(X_test)
    metrics = compute_classification_metrics(y_test, y_pred)

    save_json(metrics, os.path.join(args.output_dir, "metrics.json"))
    save_classification_report_text(y_test, y_pred, os.path.join(args.output_dir, "report.txt"))
    plot_confusion_matrix(y_test, y_pred, labels, os.path.join(args.output_dir, "confusion_matrix.png"))

    print("Evaluation complete.")
    print({k: v for k, v in metrics.items() if k != "report"})


if __name__ == "__main__":
    main()
