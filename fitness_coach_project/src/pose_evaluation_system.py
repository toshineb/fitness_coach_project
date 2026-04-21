"""
Comprehensive Pose Evaluation System
Captures poses, evaluates exercise accuracy, and provides form feedback.
Integrates with the trained Random Forest classifier.
"""

import cv2
import numpy as np
import os
import csv
import time
import joblib
from datetime import datetime
from collections import deque, Counter
from pathlib import Path

# Feature columns matching the trained model
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

# Exercise definitions with acceptable angle ranges (reference values from training data)
EXERCISE_STANDARDS = {
    "Push Ups": {
        "description": "Push-ups - bodyweight exercise",
        "angle_thresholds": {
            "Elbow_Angle": (75, 120),  # Bent at bottom, extended at top
            "Shoulder_Angle": (90, 180),
            "Hip_Ground_Angle": (170, 180),  # Keep body straight
        },
        "good_form_signs": [
            "Elbows bend 75-120 degrees",
            "Body stays straight (hip angle 170-180°)",
            "Consistent arm angles"
        ],
        "common_mistakes": [
            "Elbows flaring too wide",
            "Hips sagging (hip angle < 170°)",
            "Incomplete range of motion"
        ]
    },
    "Squats": {
        "description": "Squats - lower body exercise",
        "angle_thresholds": {
            "Knee_Angle": (60, 130),  # Varies from deep to shallow
            "Hip_Angle": (80, 140),
            "Hip_Ground_Angle": (70, 90),  # Torso leans forward slightly
        },
        "good_form_signs": [
            "Knees bend 60-130 degrees",
            "Hip angle 80-140 degrees",
            "Torso leans forward 70-90°"
        ],
        "common_mistakes": [
            "Knees caving inward",
            "Excessive forward lean",
            "Insufficient depth"
        ]
    },
    "Pull ups": {
        "description": "Pull-ups - upper body pulling exercise",
        "angle_thresholds": {
            "Elbow_Angle": (30, 140),  # Full range from extended to bent
            "Shoulder_Angle": (60, 180),
        },
        "good_form_signs": [
            "Full range of motion",
            "Consistent elbow bending",
            "Controlled movement"
        ],
        "common_mistakes": [
            "Incomplete range of motion",
            "Jerky movements",
            "Using momentum instead of strength"
        ]
    },
    "Jumping Jacks": {
        "description": "Jumping jacks - cardio exercise",
        "angle_thresholds": {
            "Shoulder_Angle": (10, 120),  # Arms going up and down
            "Hip_Angle": (160, 180),  # Legs together and apart
        },
        "good_form_signs": [
            "Synchronized arm and leg movements",
            "Full arm elevation",
            "Consistent rhythm"
        ],
        "common_mistakes": [
            "Uncoordinated movements",
            "Incomplete arm elevation",
            "Inconsistent tempo"
        ]
    },
    "Russian twists": {
        "description": "Russian twists - core exercise",
        "angle_thresholds": {
            "Shoulder_Angle": (80, 150),
            "Hip_Angle": (100, 160),
        },
        "good_form_signs": [
            "Controlled rotation",
            "Core engagement",
            "Balanced movement"
        ],
        "common_mistakes": [
            "Swinging too fast",
            "Incomplete rotation",
            "Loss of balance"
        ]
    },
    "No Exercise": {
        "description": "No exercise being performed",
        "angle_thresholds": {},
        "good_form_signs": [],
        "common_mistakes": []
    }
}


def extract_pose_angles(landmarks, side) -> dict:
    """Extract angles from pose landmarks."""
    def xy(landmark_idx):
        lm = landmarks[landmark_idx]
        return np.array([lm.x, lm.y], dtype=float)
    
    def angle_3pt(a, b, c):
        ba = a - b
        bc = c - b
        denom = np.linalg.norm(ba) * np.linalg.norm(bc)
        if denom == 0:
            return np.nan
        cosine = np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)
        return float(np.degrees(np.arccos(cosine)))
    
    def angle_to_vertical(a, b):
        vec = a - b
        vertical = np.array([0.0, -1.0])
        denom = np.linalg.norm(vec) * np.linalg.norm(vertical)
        if denom == 0:
            return np.nan
        cosine = np.clip(np.dot(vec, vertical) / denom, -1.0, 1.0)
        return float(np.degrees(np.arccos(cosine)))
    
    # Define landmark indices (MediaPipe)
    LANDMARKS = {
        "left": {
            "shoulder": 11, "elbow": 13, "wrist": 15,
            "hip": 23, "knee": 25, "ankle": 27
        },
        "right": {
            "shoulder": 12, "elbow": 14, "wrist": 16,
            "hip": 24, "knee": 26, "ankle": 28
        }
    }
    
    lm_indices = LANDMARKS[side]
    
    shoulder = xy(lm_indices["shoulder"])
    elbow = xy(lm_indices["elbow"])
    wrist = xy(lm_indices["wrist"])
    hip = xy(lm_indices["hip"])
    knee = xy(lm_indices["knee"])
    ankle = xy(lm_indices["ankle"])
    
    return {
        "Shoulder_Angle": angle_3pt(elbow, shoulder, hip),
        "Elbow_Angle": angle_3pt(shoulder, elbow, wrist),
        "Hip_Angle": angle_3pt(shoulder, hip, knee),
        "Knee_Angle": angle_3pt(hip, knee, ankle),
        "Ankle_Angle": angle_3pt(knee, ankle, ankle + np.array([0.1, 0.0])),
        "Shoulder_Ground_Angle": angle_to_vertical(elbow, shoulder),
        "Elbow_Ground_Angle": angle_to_vertical(wrist, elbow),
        "Hip_Ground_Angle": angle_to_vertical(shoulder, hip),
        "Knee_Ground_Angle": angle_to_vertical(knee, hip),
        "Ankle_Ground_Angle": angle_to_vertical(ankle, knee),
    }


def evaluate_form_accuracy(exercise: str, angles: dict) -> dict:
    """Evaluate how well the pose matches the exercise standards."""
    standards = EXERCISE_STANDARDS.get(exercise, {})
    thresholds = standards.get("angle_thresholds", {})
    
    accuracy_score = 100.0
    feedback = []
    
    for angle_name, (min_val, max_val) in thresholds.items():
        if angle_name in angles and not np.isnan(angles[angle_name]):
            current_val = angles[angle_name]
            
            if min_val <= current_val <= max_val:
                # Perfect form for this angle
                accuracy_score += 0
            else:
                # Penalize deviation
                deviation = min(abs(current_val - min_val), abs(current_val - max_val))
                penalty = min(deviation / max_val * 10, 15)  # Max 15% penalty per angle
                accuracy_score -= penalty
    
    accuracy_score = max(0, min(100, accuracy_score))
    
    return {
        "accuracy": accuracy_score,
        "feedback": feedback,
        "good_signs": standards.get("good_form_signs", []),
        "mistakes": standards.get("common_mistakes", [])
    }


class PoseEvaluator:
    def __init__(self, model_path: str = None):
        """Initialize the pose evaluator with trained model."""
        self.model = None
        self.label_mapping = {}
        
        if model_path and os.path.exists(model_path):
            self.model = joblib.load(model_path)
            # Create reverse mapping for exercise labels
            self.label_mapping = {i: label for i, label in enumerate(EXERCISE_STANDARDS.keys())}
            print(f"✓ Loaded model from {model_path}")
        else:
            print("⚠ No model loaded - classification disabled")
    
    def predict_exercise(self, angles: dict, confidence_threshold: float = 0.3) -> tuple:
        """Predict exercise and confidence."""
        if self.model is None:
            return "Unknown", 0.0
        
        try:
            # Prepare features
            features = []
            for col in FEATURE_COLUMNS:
                if col in angles:
                    val = angles[col]
                    features.append(0 if np.isnan(val) else val)
                else:
                    features.append(0)
            
            features = np.array(features).reshape(1, -1)
            
            # Predict
            prediction = self.model.predict(features)[0]
            
            # Get confidence
            if hasattr(self.model, 'predict_proba'):
                probas = self.model.predict_proba(features)[0]
                confidence = float(np.max(probas))
            else:
                confidence = 0.5
            
            return str(prediction), confidence
        except Exception as e:
            print(f"Prediction error: {e}")
            return "Error", 0.0


def create_evaluation_report(exercise: str, angles: dict, confidence: float) -> str:
    """Create a detailed evaluation report."""
    standards = EXERCISE_STANDARDS.get(exercise, {})
    form_eval = evaluate_form_accuracy(exercise, angles)
    
    report = f"""
╔══════════════════════════════════════════════════════════╗
║ POSE EVALUATION REPORT                                   ║
╚══════════════════════════════════════════════════════════╝

Exercise: {exercise}
Description: {standards.get('description', 'N/A')}
Model Confidence: {confidence*100:.1f}%
Form Accuracy: {form_eval['accuracy']:.1f}%

Angle Measurements:
{'-' * 55}
"""
    
    for angle_name, value in sorted(angles.items()):
        if not np.isnan(value):
            report += f"{angle_name:20s}: {value:7.1f}°\n"
    
    report += f"""
{'-' * 55}
Good Form Indicators:
{'-' * 55}
"""
    
    for sign in standards.get("good_form_signs", [])[:3]:
        report += f"✓ {sign}\n"
    
    report += f"""
{'-' * 55}
Common Mistakes to Avoid:
{'-' * 55}
"""
    
    for mistake in standards.get("common_mistakes", [])[:3]:
        report += f"✗ {mistake}\n"
    
    report += f"""
{'-' * 55}
Overall Assessment: {'GOOD FORM' if form_eval['accuracy'] > 70 else 'NEEDS IMPROVEMENT'}
{'-' * 55}
"""
    
    return report


def main():
    print("=" * 60)
    print("POSE EVALUATION SYSTEM")
    print("=" * 60)
    print("\nCapture your exercise poses and get instant form feedback!")
    print("\nControls:")
    print("  'c' - Capture and evaluate pose")
    print("  'r' - Start/stop recording session")
    print("  's' - Save current frame")
    print("  'q' - Quit")
    print("=" * 60)
    
    # Load model
    model_path = "results/baseline_run/model.joblib"
    evaluator = PoseEvaluator(model_path)
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("✗ Error: Cannot open camera")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # Create output directories
    os.makedirs("pose_captures", exist_ok=True)
    os.makedirs("evaluation_reports", exist_ok=True)
    os.makedirs("pose_data", exist_ok=True)
    
    # Try to import MediaPipe for pose detection
    try:
        import mediapipe as mp
        mp_pose = mp.solutions.pose
        HAS_MEDIAPIPE = True
        print("✓ MediaPipe imported successfully")
    except (ImportError, AttributeError):
        HAS_MEDIAPIPE = False
        print("⚠ MediaPipe not available - silhouette mode only")
    
    fps_buffer = deque(maxlen=30)
    frame_count = 0
    start_time = time.time()
    recording = False
    csv_file = None
    csv_writer = None
    
    pose_processor = None
    if HAS_MEDIAPIPE:
        pose_processor = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        
        exercise_detected = "Analyzing..."
        confidence = 0.0
        form_accuracy = 0.0
        angles = {}
        
        # Process with MediaPipe if available
        if HAS_MEDIAPIPE and pose_processor:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose_processor.process(frame_rgb)
            
            if results.pose_landmarks:
                # Determine visible side
                left_vis = sum(results.pose_landmarks.landmark[i].visibility 
                             for i in [11, 13, 15, 23, 25, 27])
                right_vis = sum(results.pose_landmarks.landmark[i].visibility 
                              for i in [12, 14, 16, 24, 26, 28])
                side = "left" if left_vis >= right_vis else "right"
                
                # Extract angles
                angles = extract_pose_angles(results.pose_landmarks.landmark, side)
                angles["Side_is_left"] = 1 if side == "left" else 0
                
                # Predict exercise
                exercise_detected, confidence = evaluator.predict_exercise(angles)
                
                # Evaluate form
                form_eval = evaluate_form_accuracy(exercise_detected, angles)
                form_accuracy = form_eval['accuracy']
                
                # Draw skeleton on frame
                from mediapipe.framework.formats import landmark_pb2
                from mediapipe.python.solutions import drawing_utils as mp_drawing
                from mediapipe.python.solutions import drawing_styles
                
                try:
                    mp_drawing.draw_landmarks(
                        frame,
                        results.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec=drawing_styles.get_default_pose_landmarks_style()
                    )
                except:
                    pass
                
                # Log if recording
                if recording and csv_writer:
                    row = [
                        time.time(),
                        exercise_detected,
                        confidence,
                        form_accuracy,
                    ] + [angles.get(col, np.nan) for col in FEATURE_COLUMNS]
                    csv_writer.writerow(row)
        
        # Calculate FPS
        frame_count += 1
        if frame_count % 30 == 0:
            elapsed = time.time() - start_time
            if elapsed > 0:
                fps_buffer.append(30 / elapsed)
            start_time = time.time()
        
        avg_fps = np.mean(fps_buffer) if fps_buffer else 0
        
        # Display info
        status_color = (0, 255, 0) if confidence > 0.5 else (0, 165, 255)
        
        cv2.putText(frame, f"Exercise: {exercise_detected}", (10, 30),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, f"Confidence: {confidence*100:.1f}%", (10, 65),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        cv2.putText(frame, f"Form Accuracy: {form_accuracy:.1f}%", (10, 100),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        cv2.putText(frame, f"FPS: {avg_fps:.1f}", (w - 150, 30),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        rec_text = "● REC" if recording else "○ REC"
        rec_color = (0, 0, 255) if recording else (100, 100, 100)
        cv2.putText(frame, rec_text, (w - 150, 65),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, rec_color, 2)
        
        cv2.putText(frame, "c:capture | r:record | s:save | q:quit",
                  (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        cv2.imshow("Pose Evaluation System", frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            if recording:
                csv_file.close()
                recording = False
            print("\n✓ Evaluation system closed.")
            break
        
        elif key == ord('c'):
            if angles:
                report = create_evaluation_report(exercise_detected, angles, confidence)
                print(report)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_path = os.path.join("evaluation_reports", f"report_{timestamp}.txt")
                with open(report_path, "w") as f:
                    f.write(report)
                print(f"✓ Report saved: {report_path}")
        
        elif key == ord('s'):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join("pose_captures", f"pose_{timestamp}.png")
            cv2.imwrite(filename, frame)
            print(f"✓ Frame saved: {filename}")
        
        elif key == ord('r'):
            if not recording:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_path = os.path.join("pose_data", f"session_{timestamp}.csv")
                csv_file = open(csv_path, "w", newline="")
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(["timestamp", "exercise", "confidence", "form_accuracy"] + FEATURE_COLUMNS)
                recording = True
                print(f"✓ Recording started: {csv_path}")
            else:
                csv_file.close()
                recording = False
                print("✓ Recording stopped")
    
    cap.release()
    cv2.destroyAllWindows()
    if pose_processor:
        pose_processor.close()


if __name__ == "__main__":
    main()
