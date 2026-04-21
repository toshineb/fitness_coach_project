from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)

FEATURE_COLUMNS = [
    "Shoulder_Angle",
    "Elbow_Angle",
    "Hip_Angle",
    "Knee_Angle",
    "Ankle_Angle",
    "Shoulder_Ground_Angle",
    "Elbow_Ground_Angle",
    "Hip_Ground_Angle",
    "Knee_Ground_Angle",
    "Ankle_Ground_Angle",
    "Side_is_left",
]

OPTIONAL_COLUMNS = ["Side"]
TARGET_COLUMN = "Label"
TARGET_ID_COLUMN = "exercise_label"


def str2bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    value = value.strip().lower()
    if value in {"1", "true", "t", "yes", "y"}:
        return True
    if value in {"0", "false", "f", "no", "n"}:
        return False
    raise ValueError(f"Cannot parse boolean value from: {value}")



def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)



def load_angle_csv(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    missing = [c for c in FEATURE_COLUMNS + [TARGET_COLUMN] if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")
    return df



def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    X = df[FEATURE_COLUMNS].copy()
    if "Side" in df.columns:
        X["Side_is_left"] = (df["Side"].astype(str).str.lower() == "left").astype(int)
    y = df[TARGET_COLUMN].astype(str)
    return X, y



def save_json(data: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)



def compute_classification_metrics(y_true: Sequence[str], y_pred: Sequence[str]) -> dict:
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted")),
        "report": classification_report(y_true, y_pred, output_dict=True, zero_division=0),
    }
    return metrics



def save_classification_report_text(y_true: Sequence[str], y_pred: Sequence[str], path: str) -> None:
    report_text = classification_report(y_true, y_pred, zero_division=0)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report_text)



def plot_confusion_matrix(y_true: Sequence[str], y_pred: Sequence[str], labels: List[str], out_path: str) -> None:
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(cm)
    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("True label")
    ax.set_title("Confusion Matrix")

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center")

    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)



def plot_feature_importance(model, feature_names: List[str], out_path: str) -> None:
    if not hasattr(model, "feature_importances_"):
        return
    importance = model.feature_importances_
    order = np.argsort(importance)[::-1]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(np.array(feature_names)[order], importance[order])
    ax.set_title("Feature Importance")
    ax.set_ylabel("Importance")
    ax.set_xlabel("Feature")
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)



def save_model_bundle(bundle: dict, path: str) -> None:
    joblib.dump(bundle, path)



def load_model_bundle(path: str) -> dict:
    return joblib.load(path)



def landmark_to_xy(landmark) -> np.ndarray:
    return np.array([landmark.x, landmark.y], dtype=float)



def calculate_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    ba = a - b
    bc = c - b
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom == 0:
        return float("nan")
    cosine = np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))



def calculate_vertical_angle(a: np.ndarray, b: np.ndarray) -> float:
    vec = a - b
    vertical = np.array([0.0, -1.0], dtype=float)
    denom = np.linalg.norm(vec) * np.linalg.norm(vertical)
    if denom == 0:
        return float("nan")
    cosine = np.clip(np.dot(vec, vertical) / denom, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))


@dataclass
class FPSCounter:
    buffer_size: int = 30

    def __post_init__(self) -> None:
        self.timestamps: List[float] = []

    def update(self) -> float:
        now = time.time()
        self.timestamps.append(now)
        self.timestamps = self.timestamps[-self.buffer_size:]
        if len(self.timestamps) < 2:
            return 0.0
        dt = self.timestamps[-1] - self.timestamps[0]
        if dt <= 0:
            return 0.0
        return (len(self.timestamps) - 1) / dt



def safe_float(value: float, default: float = 0.0) -> float:
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return default
    return float(value)

