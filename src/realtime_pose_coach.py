from __future__ import annotations

import argparse
import csv
import os
import time
from collections import Counter, deque
from typing import Deque, Dict, List, Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np
import pandas as pd

from utils import FPSCounter, ensure_dir, load_model_bundle, safe_float, str2bool

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils


LEFT = {
    "shoulder": mp_pose.PoseLandmark.LEFT_SHOULDER,
    "elbow": mp_pose.PoseLandmark.LEFT_ELBOW,
    "wrist": mp_pose.PoseLandmark.LEFT_WRIST,
    "hip": mp_pose.PoseLandmark.LEFT_HIP,
    "knee": mp_pose.PoseLandmark.LEFT_KNEE,
    "ankle": mp_pose.PoseLandmark.LEFT_ANKLE,
}

RIGHT = {
    "shoulder": mp_pose.PoseLandmark.RIGHT_SHOULDER,
    "elbow": mp_pose.PoseLandmark.RIGHT_ELBOW,
    "wrist": mp_pose.PoseLandmark.RIGHT_WRIST,
    "hip": mp_pose.PoseLandmark.RIGHT_HIP,
    "knee": mp_pose.PoseLandmark.RIGHT_KNEE,
    "ankle": mp_pose.PoseLandmark.RIGHT_ANKLE,
}


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



def xy(landmarks, idx) -> np.ndarray:
    lm = landmarks[idx.value]
    return np.array([lm.x, lm.y], dtype=float)



def angle_3pt(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    ba = a - b
    bc = c - b
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom == 0:
        return np.nan
    cosine = np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))



def angle_to_vertical(a: np.ndarray, b: np.ndarray) -> float:
    vec = a - b
    vertical = np.array([0.0, -1.0], dtype=float)
    denom = np.linalg.norm(vec) * np.linalg.norm(vertical)
    if denom == 0:
        return np.nan
    cosine = np.clip(np.dot(vec, vertical) / denom, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))



def extract_side_angles(landmarks, side: Dict, side_is_left: int) -> Dict[str, float]:
    shoulder = xy(landmarks, side["shoulder"])
    elbow = xy(landmarks, side["elbow"])
    wrist = xy(landmarks, side["wrist"])
    hip = xy(landmarks, side["hip"])
    knee = xy(landmarks, side["knee"])
    ankle = xy(landmarks, side["ankle"])

    features = {
        "Shoulder_Angle": angle_3pt(elbow, shoulder, hip),
        "Elbow_Angle": angle_3pt(shoulder, elbow, wrist),
        "Hip_Angle": angle_3pt(shoulder, hip, knee),
        "Knee_Angle": angle_3pt(hip, knee, ankle),
        "Ankle_Angle": angle_3pt(knee, ankle, ankle + np.array([0.1, 0.0], dtype=float)),
        "Shoulder_Ground_Angle": angle_to_vertical(elbow, shoulder),
        "Elbow_Ground_Angle": angle_to_vertical(wrist, elbow),
        "Hip_Ground_Angle": angle_to_vertical(shoulder, hip),
        "Knee_Ground_Angle": angle_to_vertical(hip, knee),
        "Ankle_Ground_Angle": angle_to_vertical(knee, ankle),
        "Side_is_left": int(side_is_left),
    }
    return features



def choose_visible_side(landmarks) -> Tuple[Dict, int]:
    left_vis = sum(landmarks[idx.value].visibility for idx in LEFT.values())
    right_vis = sum(landmarks[idx.value].visibility for idx in RIGHT.values())
    if left_vis >= right_vis:
        return LEFT, 1
    return RIGHT, 0



def features_to_frame(features: Dict[str, float]) -> pd.DataFrame:
    values = {k: [safe_float(features.get(k, np.nan))] for k in FEATURE_COLUMNS}
    return pd.DataFrame(values)



def predict_exercise(model_bundle: Optional[dict], features: Dict[str, float]) -> Tuple[str, float]:
    if model_bundle is None:
        return heuristic_exercise_guess(features), 0.0
    X = features_to_frame(features)
    model = model_bundle["model"]
    pred = model.predict(X)[0]
    confidence = 0.0
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)[0]
        confidence = float(np.max(probs))
    return str(pred), confidence



def heuristic_exercise_guess(features: Dict[str, float]) -> str:
    hip = features["Hip_Angle"]
    knee = features["Knee_Angle"]
    elbow = features["Elbow_Angle"]
    trunk = features["Hip_Ground_Angle"]

    if trunk < 35 and 70 < elbow < 170:
        return "Push Ups"
    if knee < 120 and trunk < 40:
        return "Squats"
    if trunk > 70 and elbow > 140 and knee > 150:
        return "No Exercise"
    return "Unknown"



def rule_based_feedback(exercise_name: str, features: Dict[str, float]) -> List[str]:
    feedback: List[str] = []
    shoulder = features["Shoulder_Angle"]
    elbow = features["Elbow_Angle"]
    hip = features["Hip_Angle"]
    knee = features["Knee_Angle"]
    trunk = features["Hip_Ground_Angle"]

    name = exercise_name.lower()

    if "squat" in name:
        if knee > 145:
            feedback.append("Go deeper to reach stronger squat depth.")
        if trunk > 40:
            feedback.append("Keep your chest more upright during the squat.")
        if hip < 55:
            feedback.append("Avoid collapsing too low at the hips; control the bottom position.")

    elif "push" in name:
        if hip < 150:
            feedback.append("Keep your core braced and maintain a straighter body line.")
        if elbow > 120:
            feedback.append("Lower further for a fuller push-up range of motion.")
        if shoulder < 20:
            feedback.append("Do not shrug your shoulders; keep them stable.")

    elif "lunge" in name:
        if knee > 120:
            feedback.append("Bend the lead knee more to reach proper lunge depth.")
        if trunk > 30:
            feedback.append("Keep your torso more upright during the lunge.")

    elif "shoulder" in name or "press" in name:
        if elbow < 150:
            feedback.append("Extend your elbows fully at the top of the press.")
        if trunk > 20:
            feedback.append("Avoid leaning back; brace your core during the press.")

    elif "plank" in name:
        if hip < 160:
            feedback.append("Lift your hips slightly to form a straighter plank line.")
        if trunk > 25:
            feedback.append("Keep your shoulders stacked and reduce torso tilt.")

    elif "unknown" in name:
        feedback.append("Exercise not confidently recognised. Adjust camera angle or lighting.")

    else:
        feedback.append("Rule set not defined for this exercise label in the current dataset.")

    return feedback[:2]



def draw_overlay(frame, exercise_name: str, confidence: float, feedback: List[str], fps: float, latency_ms: float) -> None:
    y = 30
    lines = [
        f"Exercise: {exercise_name}",
        f"Confidence: {confidence:.2f}",
        f"FPS: {fps:.1f}",
        f"Latency: {latency_ms:.1f} ms",
    ] + feedback
    for line in lines:
        cv2.putText(frame, line, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        y += 30



def main() -> None:
    parser = argparse.ArgumentParser(description="Real-time MediaPipe fitness coach")
    parser.add_argument("--model_path", type=str, default="", help="Optional saved classifier path")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--save_session", type=str, default="true")
    parser.add_argument("--output_dir", type=str, default="results/realtime_session")
    parser.add_argument("--min_detection_confidence", type=float, default=0.5)
    parser.add_argument("--min_tracking_confidence", type=float, default=0.5)
    args = parser.parse_args()

    save_session = str2bool(args.save_session)
    ensure_dir(args.output_dir)
    model_bundle = load_model_bundle(args.model_path) if args.model_path else None

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera index {args.camera}")

    session_csv = None
    csv_writer = None
    if save_session:
        session_csv = open(os.path.join(args.output_dir, "session_log.csv"), "w", newline="", encoding="utf-8")
        csv_writer = csv.writer(session_csv)
        csv_writer.writerow([
            "timestamp",
            *FEATURE_COLUMNS,
            "predicted_exercise",
            "confidence",
            "fps",
            "latency_ms",
            "feedback_1",
            "feedback_2",
        ])

    fps_counter = FPSCounter(buffer_size=30)
    pred_history: Deque[str] = deque(maxlen=10)

    with mp_pose.Pose(
        min_detection_confidence=args.min_detection_confidence,
        min_tracking_confidence=args.min_tracking_confidence,
    ) as pose:
        while True:
            frame_start = time.time()
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)

            exercise_name = "No person detected"
            confidence = 0.0
            feedback: List[str] = []
            features = {k: np.nan for k in FEATURE_COLUMNS}

            if results.pose_landmarks:
                mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                landmarks = results.pose_landmarks.landmark
                side, side_is_left = choose_visible_side(landmarks)
                features = extract_side_angles(landmarks, side, side_is_left)
                pred, confidence = predict_exercise(model_bundle, features)
                pred_history.append(pred)
                exercise_name = Counter(pred_history).most_common(1)[0][0]
                feedback = rule_based_feedback(exercise_name, features)

            fps = fps_counter.update()
            latency_ms = (time.time() - frame_start) * 1000.0
            draw_overlay(frame, exercise_name, confidence, feedback, fps, latency_ms)
            cv2.imshow("Real-Time Fitness Coach", frame)

            if csv_writer is not None:
                row = [
                    time.time(),
                    *[safe_float(features.get(col, np.nan)) for col in FEATURE_COLUMNS],
                    exercise_name,
                    confidence,
                    fps,
                    latency_ms,
                    feedback[0] if len(feedback) > 0 else "",
                    feedback[1] if len(feedback) > 1 else "",
                ]
                csv_writer.writerow(row)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()
    if session_csv is not None:
        session_csv.close()


if __name__ == "__main__":
    main()
