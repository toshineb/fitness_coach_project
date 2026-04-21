"""
Streamlit-compatible pose detection using YOLOv8.
Provides utilities for real-time pose detection with automatic model downloading.
"""

from __future__ import annotations

import io
import time
from collections import Counter, deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, List, Optional, Tuple

import cv2
import numpy as np
import pandas as pd
from PIL import Image
from ultralytics import YOLO

from utils import FPSCounter, safe_float

# Initialize YOLOv8 pose model (auto-downloads on first use)
print("⏳ Loading YOLOv8 pose detection model...")
try:
    MODEL = YOLO("yolov8n-pose.pt")
    print("✅ YOLOv8 pose model loaded successfully")
    POSE_DETECTION_AVAILABLE = True
except Exception as e:
    print(f"❌ Failed to load YOLOv8 model: {e}")
    MODEL = None
    POSE_DETECTION_AVAILABLE = False

# MediaPipe landmarks mapping (compatible with original code)
# YOLOv8 uses 17 keypoints (COCO format), we'll map them to MediaPipe's 33-point format
LEFT = {
    "shoulder": 11,
    "elbow": 13,
    "wrist": 15,
    "hip": 23,
    "knee": 25,
    "ankle": 27,
}

RIGHT = {
    "shoulder": 12,
    "elbow": 14,
    "wrist": 16,
    "hip": 24,
    "knee": 26,
    "ankle": 28,
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

EXERCISES = [
    "Squat",
    "Push-up",
    "Deadlift",
    "Bench Press",
    "Pull-up",
    "Shoulder Press",
]


@dataclass
class Landmark:
    """Simple landmark class compatible with original code."""
    x: float
    y: float
    z: float = 0.0
    presence: float = 1.0
    visibility: float = 1.0


@dataclass
class PoseFrame:
    """A single frame with pose data."""
    frame: Optional[np.ndarray] = None
    landmarks: List[Landmark] | None = None
    features: Dict[str, float] | None = None
    success: bool = False


def yolo_to_mediapipe_landmarks(yolo_keypoints: np.ndarray) -> List[Landmark]:
    """
    Convert YOLOv8 keypoints (17 COCO points) to MediaPipe-compatible landmarks.
    
    YOLOv8 COCO keypoints (17 points):
    0: Nose, 1-2: Eyes, 3-4: Ears, 5-10: Arms (shoulders, elbows, wrists),
    11-16: Legs (hips, knees, ankles)
    
    MediaPipe Pose (33 points) - we focus on the main 11 we use:
    11: Left Shoulder, 12: Right Shoulder, 13: Left Elbow, 14: Right Elbow,
    15: Left Wrist, 16: Right Wrist, 23: Left Hip, 24: Right Hip,
    25: Left Knee, 26: Right Knee, 27: Left Ankle, 28: Right Ankle
    """
    # Initialize with empty landmarks
    landmarks = [Landmark(x=0, y=0, z=0, presence=0) for _ in range(33)]
    
    # Map YOLOv8 points to MediaPipe indices
    # YOLOv8 -> MediaPipe mapping
    mapping = {
        0: 0,    # Nose -> Nose
        1: 2,    # Left Eye -> Left Eye
        2: 5,    # Right Eye -> Right Eye
        3: 1,    # Left Ear -> Left Ear Inner
        4: 4,    # Right Ear -> Right Ear Inner
        5: 11,   # Left Shoulder
        6: 12,   # Right Shoulder
        7: 13,   # Left Elbow
        8: 14,   # Right Elbow
        9: 15,   # Left Wrist
        10: 16,  # Right Wrist
        11: 23,  # Left Hip
        12: 24,  # Right Hip
        13: 25,  # Left Knee
        14: 26,  # Right Knee
        15: 27,  # Left Ankle
        16: 28,  # Right Ankle
    }
    
    if yolo_keypoints is not None and len(yolo_keypoints) > 0:
        for yolo_idx, mediapipe_idx in mapping.items():
            if yolo_idx < len(yolo_keypoints):
                kp = yolo_keypoints[yolo_idx]
                # YOLOv8 format: [x, y, confidence]
                x = float(kp[0]) if kp[0] >= 0 else 0
                y = float(kp[1]) if kp[1] >= 0 else 0
                conf = float(kp[2]) if len(kp) > 2 and kp[2] >= 0 else 0.5
                
                landmarks[mediapipe_idx] = Landmark(
                    x=x, y=y, z=0,
                    presence=min(1.0, conf),
                    visibility=min(1.0, conf)
                )
    
    return landmarks


def choose_visible_side(landmarks: List[Landmark]) -> Tuple[str, bool]:
    """Choose which side of the body is most visible."""
    left_confidence = sum(
        landmarks[i].presence for i in [11, 13, 15, 23, 25, 27]
        if i < len(landmarks)
    )
    right_confidence = sum(
        landmarks[i].presence for i in [12, 14, 16, 24, 26, 28]
        if i < len(landmarks)
    )
    
    if left_confidence > right_confidence:
        return "left", True
    else:
        return "right", False


def angle_between_points(p1: Landmark, p2: Landmark, p3: Landmark) -> float:
    """Calculate angle (in degrees) between three points."""
    if not all([p1.presence > 0.3, p2.presence > 0.3, p3.presence > 0.3]):
        return np.nan
    
    # Convert to coordinates
    v1 = np.array([p1.x - p2.x, p1.y - p2.y])
    v2 = np.array([p3.x - p2.x, p3.y - p2.y])
    
    v1_len = np.linalg.norm(v1)
    v2_len = np.linalg.norm(v2)
    
    if v1_len < 1e-6 or v2_len < 1e-6:
        return np.nan
    
    cos_angle = np.dot(v1, v2) / (v1_len * v2_len)
    cos_angle = np.clip(cos_angle, -1, 1)
    
    angle = np.arccos(cos_angle) * 180 / np.pi
    return float(angle)


def extract_side_angles(
    landmarks: List[Landmark], side: str, side_is_left: bool
) -> Dict[str, float]:
    """Extract joint angles from landmarks."""
    if side_is_left:
        shoulder_idx = LEFT["shoulder"]
        elbow_idx = LEFT["elbow"]
        wrist_idx = LEFT["wrist"]
        hip_idx = LEFT["hip"]
        knee_idx = LEFT["knee"]
        ankle_idx = LEFT["ankle"]
    else:
        shoulder_idx = RIGHT["shoulder"]
        elbow_idx = RIGHT["elbow"]
        wrist_idx = RIGHT["wrist"]
        hip_idx = RIGHT["hip"]
        knee_idx = RIGHT["knee"]
        ankle_idx = RIGHT["ankle"]
    
    features = {}
    
    # Shoulder angle
    if len(landmarks) > elbow_idx and len(landmarks) > wrist_idx:
        features["Shoulder_Angle"] = angle_between_points(
            landmarks[wrist_idx], landmarks[elbow_idx], landmarks[shoulder_idx]
        )
    
    # Elbow angle
    if len(landmarks) > wrist_idx:
        features["Elbow_Angle"] = angle_between_points(
            landmarks[wrist_idx], landmarks[elbow_idx], landmarks[shoulder_idx]
        )
    
    # Hip angle
    if len(landmarks) > knee_idx:
        features["Hip_Angle"] = angle_between_points(
            landmarks[shoulder_idx], landmarks[hip_idx], landmarks[knee_idx]
        )
    
    # Knee angle
    if len(landmarks) > ankle_idx:
        features["Knee_Angle"] = angle_between_points(
            landmarks[hip_idx], landmarks[knee_idx], landmarks[ankle_idx]
        )
    
    # Ankle angle (simplified)
    if len(landmarks) > ankle_idx:
        features["Ankle_Angle"] = angle_between_points(
            landmarks[knee_idx], landmarks[ankle_idx], landmarks[ankle_idx]
        )
    
    # Ground angles (with respect to horizontal)
    nose_idx = 0
    if len(landmarks) > shoulder_idx and len(landmarks) > nose_idx:
        features["Shoulder_Ground_Angle"] = angle_between_points(
            landmarks[shoulder_idx], landmarks[nose_idx],
            Landmark(x=landmarks[shoulder_idx].x + 1, y=landmarks[shoulder_idx].y)
        )
    
    if len(landmarks) > elbow_idx:
        features["Elbow_Ground_Angle"] = angle_between_points(
            landmarks[elbow_idx], landmarks[shoulder_idx],
            Landmark(x=landmarks[elbow_idx].x + 1, y=landmarks[elbow_idx].y)
        )
    
    if len(landmarks) > hip_idx:
        features["Hip_Ground_Angle"] = angle_between_points(
            landmarks[hip_idx], landmarks[knee_idx],
            Landmark(x=landmarks[hip_idx].x + 1, y=landmarks[hip_idx].y)
        )
    
    if len(landmarks) > knee_idx:
        features["Knee_Ground_Angle"] = angle_between_points(
            landmarks[knee_idx], landmarks[ankle_idx],
            Landmark(x=landmarks[knee_idx].x + 1, y=landmarks[knee_idx].y)
        )
    
    if len(landmarks) > ankle_idx:
        features["Ankle_Ground_Angle"] = angle_between_points(
            landmarks[ankle_idx], Landmark(x=landmarks[ankle_idx].x, y=landmarks[ankle_idx].y),
            Landmark(x=landmarks[ankle_idx].x + 1, y=landmarks[ankle_idx].y)
        )
    
    # Add side indicator (1 for left, 0 for right)
    features["Side_is_left"] = 1.0 if side_is_left else 0.0
    
    # Fill NaNs with 0
    for key in features:
        if np.isnan(features.get(key, 0)):
            features[key] = 0.0
    
    return features


def process_frame(frame: np.ndarray) -> PoseFrame:
    """Process a single frame for pose detection using YOLOv8."""
    pose_frame = PoseFrame(frame=frame.copy())
    
    if not POSE_DETECTION_AVAILABLE or MODEL is None:
        return pose_frame
    
    try:
        # Run YOLOv8 pose detection
        results = MODEL(frame, verbose=False, conf=0.5)
        
        if results and len(results) > 0:
            result = results[0]
            
            if result.keypoints is not None and len(result.keypoints) > 0:
                # Get first person's keypoints
                keypoints = result.keypoints.xy[0].cpu().numpy()
                
                # Convert to MediaPipe-compatible format
                landmarks = yolo_to_mediapipe_landmarks(keypoints)
                pose_frame.landmarks = landmarks
                
                side, side_is_left = choose_visible_side(landmarks)
                pose_frame.features = extract_side_angles(landmarks, side, side_is_left)
                pose_frame.success = True
                
                # Draw pose on frame
                frame_copy = frame.copy()
                
                # Draw keypoints
                if result.keypoints is not None:
                    for keypoint in result.keypoints.xy[0]:
                        x, y = int(keypoint[0]), int(keypoint[1])
                        if 0 <= x < frame.shape[1] and 0 <= y < frame.shape[0]:
                            cv2.circle(frame_copy, (x, y), 5, (0, 255, 0), -1)
                
                # Draw skeleton connections
                skeleton = [
                    [16, 14], [14, 12], [17, 15], [15, 13], [12, 13],
                    [6, 12], [7, 14], [6, 7], [6, 8], [7, 9], [8, 10], [9, 11], [2, 3], [1, 2], [1, 3], [2, 4], [3, 5], [4, 6], [5, 7]
                ]
                
                keypoints_xy = result.keypoints.xy[0].cpu().numpy() if result.keypoints is not None else np.array([])
                for connection in skeleton:
                    if len(keypoints_xy) > max(connection):
                        pt1 = keypoints_xy[connection[0] - 1]
                        pt2 = keypoints_xy[connection[1] - 1]
                        
                        if all(pt1 > 0) and all(pt2 > 0):
                            cv2.line(frame_copy, tuple(pt1.astype(int)), tuple(pt2.astype(int)), (0, 255, 0), 2)
                
                pose_frame.frame = frame_copy
        
        return pose_frame
    except Exception as e:
        print(f"Error processing frame: {e}")
        return pose_frame


def process_image(image_path: str) -> PoseFrame:
    """Process an image file."""
    image = cv2.imread(image_path)
    if image is None:
        return PoseFrame(frame=None, success=False)
    
    image = cv2.resize(image, (640, 480))
    return process_frame(image)


def process_uploaded_image(uploaded_file) -> PoseFrame:
    """Process an uploaded image from Streamlit."""
    image = Image.open(uploaded_file)
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    image_cv = cv2.resize(image_cv, (640, 480))
    return process_frame(image_cv)


def features_to_frame(features: Dict[str, float]) -> pd.DataFrame:
    """Convert features dict to DataFrame for model prediction."""
    values = {k: [safe_float(features.get(k, np.nan))] for k in FEATURE_COLUMNS}
    return pd.DataFrame(values)


class StreamlitPoseCoach:
    """Main pose coach for Streamlit application using YOLOv8."""
    
    def __init__(self, model_bundle: Optional[Dict] = None):
        self.model_bundle = model_bundle
        self.pose = "yolov8"  # Simple flag to indicate pose detection is available
        self.pred_history: Deque[str] = deque(maxlen=10)
        self.fps_counter = FPSCounter(buffer_size=30)
        
        if not POSE_DETECTION_AVAILABLE:
            self.pose = None
            print("❌ Pose detection not available")
        else:
            print("✅ Pose coach initialized with YOLOv8")
    
    def predict_exercise(self, features: Dict[str, float]) -> Tuple[str, float]:
        """Predict exercise type from features."""
        if self.model_bundle is None:
            return self.heuristic_exercise_guess(features), 0.0
        
        X = features_to_frame(features)
        model = self.model_bundle["model"]
        pred = model.predict(X)[0]
        confidence = 0.0
        
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X)[0]
            confidence = float(np.max(probs))
        
        return str(pred), confidence
    
    @staticmethod
    def heuristic_exercise_guess(features: Dict[str, float]) -> str:
        """Guess exercise type from features if no model available."""
        hip = safe_float(features.get("Hip_Angle", np.nan))
        knee = safe_float(features.get("Knee_Angle", np.nan))
        elbow = safe_float(features.get("Elbow_Angle", np.nan))
        trunk = safe_float(features.get("Hip_Ground_Angle", np.nan))

        if trunk < 35 and 70 < elbow < 170:
            return "Push-up"
        if knee < 120 and trunk < 40:
            return "Squat"
        if trunk > 70 and elbow > 140 and knee > 150:
            return "No Exercise"
        return "Unknown"
    
    def analyze_frame(self, pose_frame: PoseFrame) -> Dict[str, Any]:
        """Analyze a frame and return metrics."""
        result = {
            "success": pose_frame.success,
            "exercise": "Unknown",
            "confidence": 0.0,
            "feedback": [],
            "features": {},
        }
        
        if pose_frame.success:
            exercise, confidence = self.predict_exercise(pose_frame.features)
            self.pred_history.append(exercise)
            
            # Use majority vote
            exercise = Counter(self.pred_history).most_common(1)[0][0]
            
            result["exercise"] = exercise
            result["confidence"] = confidence
            result["features"] = pose_frame.features
            result["feedback"] = self.get_feedback(exercise, pose_frame.features)
        
        return result
    
    @staticmethod
    def get_feedback(exercise_name: str, features: Dict[str, float]) -> List[str]:
        """Generate feedback based on exercise and features."""
        feedback: List[str] = []
        shoulder = safe_float(features.get("Shoulder_Angle", np.nan))
        elbow = safe_float(features.get("Elbow_Angle", np.nan))
        hip = safe_float(features.get("Hip_Angle", np.nan))
        knee = safe_float(features.get("Knee_Angle", np.nan))
        trunk = safe_float(features.get("Hip_Ground_Angle", np.nan))

        name = exercise_name.lower()

        if "squat" in name:
            if knee > 145:
                feedback.append("📍 Go deeper to reach stronger squat depth.")
            elif trunk > 40:
                feedback.append("📍 Keep your chest more upright during the squat.")
            elif hip < 55:
                feedback.append("📍 Avoid collapsing too low at the hips; control the bottom position.")
            
            if not feedback:
                feedback.append("✅ Perfect squat form!")
        
        elif "push-up" in name or "pushup" in name:
            if elbow < 60:
                feedback.append("📍 Lower your body more for a full range of motion.")
            elif elbow > 100:
                feedback.append("📍 Don't lock out your elbows at the top.")
            
            if trunk > 20:
                feedback.append("📍 Keep your body straight; don't sag at the hips.")
            
            if not feedback:
                feedback.append("✅ Excellent push-up form!")
        
        elif "deadlift" in name:
            if trunk > 50:
                feedback.append("📍 Keep your back straighter; hinge at the hips, not the back.")
            elif knee < 30:
                feedback.append("📍 Increase your knee bend slightly at the start.")
            
            if not feedback:
                feedback.append("✅ Great deadlift form!")
        
        else:
            feedback.append("📍 Keep your form controlled and avoid jerking movements.")
        
        return feedback
