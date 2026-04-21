"""
Streamlit-compatible pose detection and analysis helper module.
Provides utilities for real-time pose detection without OpenCV windows.
"""

from __future__ import annotations

import io
import time
from collections import Counter, deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, List, Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
from PIL import Image

from utils import FPSCounter, safe_float

# Handle MediaPipe versions - prioritize 0.10+ tasks API
mp_pose = None
mp_drawing = None
POSE_CONNECTIONS = None
MEDIAPIPE_NEW_API = False

try:
    # Try MediaPipe 0.10+ with new tasks API
    from mediapipe.tasks.python.vision import pose_landmarker
    from mediapipe.tasks.python.vision.core import vision_task_running_mode
    from mediapipe import tasks as mp_tasks
    
    # For the new API, PoseLandmarker is the main class
    mp_pose = pose_landmarker
    MEDIAPIPE_NEW_API = True
    print("✅ Using MediaPipe 0.10+ tasks API")
except ImportError as e:
    try:
        # Fallback to mediapipe.python.solutions if available
        from mediapipe.python.solutions import pose as mp_pose_module
        from mediapipe.python.solutions import drawing_utils as mp_drawing_module
        from mediapipe.python.solutions.pose import POSE_CONNECTIONS
        
        mp_pose = mp_pose_module
        mp_drawing = mp_drawing_module
        MEDIAPIPE_NEW_API = False
        print("✅ Using mediapipe.python.solutions")
    except ImportError:
        try:
            # Try modern import (MediaPipe < 0.10 but not using python.solutions)
            from mediapipe import solutions
            mp_pose = solutions.pose
            mp_drawing = solutions.drawing_utils
            POSE_CONNECTIONS = mp_pose.POSE_CONNECTIONS
            MEDIAPIPE_NEW_API = False
            print("✅ Using mediapipe.solutions")
        except (ImportError, AttributeError):
            try:
                # Try legacy import
                mp_pose = mp.solutions.pose
                mp_drawing = mp.solutions.drawing_utils
                POSE_CONNECTIONS = mp_pose.POSE_CONNECTIONS
                MEDIAPIPE_NEW_API = False
                print("✅ Using mp.solutions (legacy)")
            except (ImportError, AttributeError) as final_e:
                print(f"⚠️  Warning: Could not import MediaPipe: {final_e}")
                mp_pose = None
                mp_drawing = None
                MEDIAPIPE_NEW_API = False

# Define landmarks using indices (works for all versions)
# MediaPipe pose landmarks follow a standard order (0-32)
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

EXERCISES = ["Squat", "Lunge", "Push-up", "Deadlift", "Bicep Curl"]


@dataclass
class PoseFrame:
    """Container for pose analysis results."""
    frame: np.ndarray
    landmarks: Optional[Any] = None
    features: Dict[str, float] = None
    success: bool = False
    
    def __post_init__(self):
        if self.features is None:
            self.features = {}


def xy(landmarks, idx) -> np.ndarray:
    """Extract x,y coordinates from landmark."""
    lm = landmarks[idx.value]
    return np.array([lm.x, lm.y], dtype=float)


def angle_3pt(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Calculate angle between three points."""
    ba = a - b
    bc = c - b
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom == 0:
        return np.nan
    cosine = np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))


def angle_to_vertical(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate angle to vertical."""
    vec = a - b
    vertical = np.array([0.0, -1.0], dtype=float)
    denom = np.linalg.norm(vec) * np.linalg.norm(vertical)
    if denom == 0:
        return np.nan
    cosine = np.clip(np.dot(vec, vertical) / denom, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))


def extract_side_angles(landmarks, side: Dict, side_is_left: int) -> Dict[str, float]:
    """Extract all angles from one side of the body."""
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
    """Choose the more visible side of the body."""
    left_vis = sum(landmarks[idx.value].visibility for idx in LEFT.values())
    right_vis = sum(landmarks[idx.value].visibility for idx in RIGHT.values())
    if left_vis >= right_vis:
        return LEFT, 1
    return RIGHT, 0


def features_to_frame(features: Dict[str, float]) -> pd.DataFrame:
    """Convert features dict to DataFrame for model prediction."""
    values = {k: [safe_float(features.get(k, np.nan))] for k in FEATURE_COLUMNS}
    return pd.DataFrame(values)


def process_frame(frame: np.ndarray, pose_detector) -> PoseFrame:
    """Process a single frame for pose detection."""
    pose_frame = PoseFrame(frame=frame.copy())
    
    if pose_detector is None or mp_pose is None:
        return pose_frame
    
    try:
        if MEDIAPIPE_NEW_API:
            # MediaPipe 0.10+ API
            from mediapipe import Image as MPImage
            import mediapipe.tasks.python as mp_python
            
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = MPImage(
                image_format=mp_python.vision.ImageFormat.SRGB,
                data=rgb
            )
            results = pose_detector.detect(mp_image)
            
            if results.pose_landmarks and len(results.pose_landmarks) > 0:
                # Convert new API results to old API format for compatibility
                landmarks = results.pose_landmarks[0]
                pose_frame.landmarks = landmarks
                
                side, side_is_left = choose_visible_side(landmarks)
                pose_frame.features = extract_side_angles(landmarks, side, side_is_left)
                pose_frame.success = True
                
                # Try to draw landmarks if possible
                frame_copy = frame.copy()
                if hasattr(results, 'pose_landmarks_connections'):
                    try:
                        # Draw landmarks manually
                        h, w = frame.shape[:2]
                        for landmark in landmarks:
                            if landmark.presence > 0.5:  # confidence threshold
                                x = int(landmark.x * w)
                                y = int(landmark.y * h)
                                cv2.circle(frame_copy, (x, y), 5, (0, 255, 0), -1)
                    except Exception as e:
                        print(f"Warning: Could not draw landmarks: {e}")
                pose_frame.frame = frame_copy
        else:
            # Old MediaPipe API
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose_detector.process(rgb)
            
            if results.pose_landmarks:
                pose_frame.landmarks = results.pose_landmarks.landmark
                side, side_is_left = choose_visible_side(pose_frame.landmarks)
                pose_frame.features = extract_side_angles(pose_frame.landmarks, side, side_is_left)
                pose_frame.success = True
                
                # Draw pose on frame
                frame_copy = frame.copy()
                if mp_drawing is not None and POSE_CONNECTIONS is not None:
                    try:
                        mp_drawing.draw_landmarks(frame_copy, results.pose_landmarks, POSE_CONNECTIONS)
                    except Exception as e:
                        print(f"Warning: Could not draw landmarks: {e}")
                pose_frame.frame = frame_copy
        
        return pose_frame
    except Exception as e:
        print(f"Error processing frame: {e}")
        import traceback
        traceback.print_exc()
        return pose_frame


def process_image(image_path: str, pose_detector) -> PoseFrame:
    """Process an image file."""
    image = cv2.imread(image_path)
    if image is None:
        return PoseFrame(frame=None, success=False)
    
    image = cv2.resize(image, (640, 480))
    return process_frame(image, pose_detector)


def process_uploaded_image(uploaded_file, pose_detector) -> PoseFrame:
    """Process an uploaded image from Streamlit."""
    image = Image.open(uploaded_file)
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    image_cv = cv2.resize(image_cv, (640, 480))
    return process_frame(image_cv, pose_detector)


def process_video_frame(frame: np.ndarray, pose_detector) -> PoseFrame:
    """Process a video frame."""
    return process_frame(frame, pose_detector)


class StreamlitPoseCoach:
    """Main pose coach for Streamlit application."""
    
    def __init__(self, model_bundle: Optional[Dict] = None):
        self.model_bundle = model_bundle
        self.pose = None
        
        # Initialize pose detector with error handling
        if mp_pose is not None:
            try:
                if MEDIAPIPE_NEW_API:
                    # MediaPipe 0.10+ API - try to use with a bundled or cached model
                    from mediapipe.tasks import python as mp_python
                    from pathlib import Path
                    import urllib.request
                    
                    # Path to store the model
                    model_dir = Path(__file__).parent.parent / "models"
                    model_dir.mkdir(exist_ok=True)
                    model_path = model_dir / "pose_landmarker.task"
                    
                    # Try to download model if not present
                    if not model_path.exists():
                        print("⏳ Downloading pose detection model (first time only)...")
                        model_url = "https://www.gstatic.com/mediapipe-solutions/pose_landmarker/pose_landmarker.task"
                        try:
                            urllib.request.urlretrieve(model_url, str(model_path), 
                                                      reporthook=lambda b, bs, s: print(f"  Downloaded {b*bs}/{s} bytes", end='\r'))
                            print("\n✅ Model downloaded successfully")
                        except Exception as dl_e:
                            print(f"\n⚠️  Could not download model: {dl_e}")
                            print("   Trying alternative URLs...")
                            # Try alternative URL
                            alt_url = "https://www.gstatic.com/mediapipe-solutions/pose_landmarker/lite/latest/pose_landmarker.tflite"
                            try:
                                urllib.request.urlretrieve(alt_url, str(model_path))
                                print("✅ Alternative model downloaded")
                            except:
                                model_path = None  # Will use fallback
                    
                    if model_path and model_path.exists():
                        base_options = mp_python.BaseOptions(model_asset_path=str(model_path))
                        options = pose_landmarker.PoseLandmarkerOptions(
                            base_options=base_options,
                            min_pose_detection_confidence=0.5,
                            min_pose_presence_confidence=0.5,
                            min_tracking_confidence=0.5,
                            output_segmentation_masks=False
                        )
                        self.pose = pose_landmarker.PoseLandmarker.create_from_options(options)
                        print("✅ PoseLandmarker initialized (MediaPipe 0.10+)")
                    else:
                        print("⚠️  Model file not available, pose detection disabled")
                        self.pose = None
                else:
                    # Old MediaPipe API
                    self.pose = mp_pose.Pose(
                        min_detection_confidence=0.5,
                        min_tracking_confidence=0.5,
                    )
                    print("✅ Pose detector initialized (old API)")
            except Exception as e:
                print(f"❌ Error initializing MediaPipe Pose: {e}")
                self.pose = None
        
        self.pred_history: Deque[str] = deque(maxlen=10)
        self.fps_counter = FPSCounter(buffer_size=30)
        
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

        elif "push" in name or "pushup" in name or "push-up" in name:
            if hip < 150:
                feedback.append("📍 Keep your core braced and maintain a straighter body line.")
            elif elbow > 120:
                feedback.append("📍 Lower further for a fuller push-up range of motion.")
            elif shoulder < 20:
                feedback.append("📍 Do not shrug your shoulders; keep them stable.")
            
            if not feedback:
                feedback.append("✅ Perfect push-up form!")

        elif "lunge" in name:
            if knee > 120:
                feedback.append("📍 Bend the lead knee more to reach proper lunge depth.")
            elif trunk > 30:
                feedback.append("📍 Keep your torso more upright during the lunge.")
            
            if not feedback:
                feedback.append("✅ Perfect lunge form!")

        elif "deadlift" in name:
            if trunk > 50:
                feedback.append("📍 Keep your back straighter; maintain neutral spine.")
            elif knee > 140:
                feedback.append("📍 Extend your legs more fully.")
            
            if not feedback:
                feedback.append("✅ Perfect deadlift form!")

        elif "bicep" in name or "curl" in name:
            if elbow < 60:
                feedback.append("📍 Bring the weight higher to complete the curl range.")
            elif shoulder > 40:
                feedback.append("📍 Keep your shoulders stable; minimize swinging.")
            
            if not feedback:
                feedback.append("✅ Perfect curl form!")

        elif "no exercise" in name:
            feedback.append("❌ No exercise detected. Position yourself in the frame.")

        elif "unknown" in name:
            feedback.append("⚠️ Exercise not recognized. Ensure full body is visible.")

        else:
            feedback.append("ℹ️ Position detected, continue with proper form.")

        return feedback[:3]  # Return max 3 feedback items
    
    def close(self):
        """Close the pose detector."""
        if self.pose:
            self.pose.close()
