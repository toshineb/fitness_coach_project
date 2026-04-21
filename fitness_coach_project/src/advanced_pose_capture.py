"""
Advanced pose capture with data extraction and CSV logging.
Captures pose landmarks and extracts angles for exercise analysis.
"""

import cv2
import numpy as np
import os
import csv
import time
from datetime import datetime
from collections import deque

# Import MediaPipe with fallback approach for different versions
try:
    import mediapipe as mp
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
except (ImportError, AttributeError):
    from mediapipe.python.solutions import pose as mp_pose
    from mediapipe.python.solutions import drawing_utils as mp_drawing
    from mediapipe.python.solutions import drawing_styles as mp_drawing_styles

# Joint indices for angle calculations
LEFT_SIDE = {
    "shoulder": mp_pose.PoseLandmark.LEFT_SHOULDER,
    "elbow": mp_pose.PoseLandmark.LEFT_ELBOW,
    "wrist": mp_pose.PoseLandmark.LEFT_WRIST,
    "hip": mp_pose.PoseLandmark.LEFT_HIP,
    "knee": mp_pose.PoseLandmark.LEFT_KNEE,
    "ankle": mp_pose.PoseLandmark.LEFT_ANKLE,
}

RIGHT_SIDE = {
    "shoulder": mp_pose.PoseLandmark.RIGHT_SHOULDER,
    "elbow": mp_pose.PoseLandmark.RIGHT_ELBOW,
    "wrist": mp_pose.PoseLandmark.RIGHT_WRIST,
    "hip": mp_pose.PoseLandmark.RIGHT_HIP,
    "knee": mp_pose.PoseLandmark.RIGHT_KNEE,
    "ankle": mp_pose.PoseLandmark.RIGHT_ANKLE,
}


def get_xy(landmarks, landmark_enum) -> np.ndarray:
    """Extract x, y coordinates from a landmark."""
    lm = landmarks[landmark_enum.value]
    return np.array([lm.x, lm.y], dtype=np.float32)


def calculate_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Calculate angle between three points (a-b-c)."""
    ba = a - b
    bc = c - b
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    
    if denom == 0:
        return 0.0
    
    cosine = np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)
    angle = float(np.degrees(np.arccos(cosine)))
    return angle


def extract_pose_angles(landmarks, side_dict, side_name: str) -> dict:
    """Extract joint angles from pose landmarks."""
    shoulder = get_xy(landmarks, side_dict["shoulder"])
    elbow = get_xy(landmarks, side_dict["elbow"])
    wrist = get_xy(landmarks, side_dict["wrist"])
    hip = get_xy(landmarks, side_dict["hip"])
    knee = get_xy(landmarks, side_dict["knee"])
    ankle = get_xy(landmarks, side_dict["ankle"])
    
    angles = {
        f"{side_name}_shoulder_angle": calculate_angle(elbow, shoulder, hip),
        f"{side_name}_elbow_angle": calculate_angle(shoulder, elbow, wrist),
        f"{side_name}_hip_angle": calculate_angle(shoulder, hip, knee),
        f"{side_name}_knee_angle": calculate_angle(hip, knee, ankle),
        f"{side_name}_ankle_angle": calculate_angle(knee, ankle, ankle + np.array([0.1, 0.0])),
    }
    return angles


def get_dominant_side(landmarks) -> tuple:
    """Determine which side is more visible and return angles."""
    left_visibility = sum(landmarks[idx.value].visibility for idx in LEFT_SIDE.values())
    right_visibility = sum(landmarks[idx.value].visibility for idx in RIGHT_SIDE.values())
    
    if left_visibility >= right_visibility:
        return extract_pose_angles(landmarks, LEFT_SIDE, "left"), "left"
    else:
        return extract_pose_angles(landmarks, RIGHT_SIDE, "right"), "right"


class PoseCaptureRecorder:
    def __init__(self, output_dir="pose_data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.recording = False
        self.csv_file = None
        self.csv_writer = None
        
    def start_recording(self):
        """Start recording pose data to CSV."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"pose_session_{timestamp}.csv")
        
        self.csv_file = open(filename, "w", newline="", encoding="utf-8")
        
        # Define CSV headers
        headers = [
            "timestamp",
            "frame_number",
            "left_shoulder_angle",
            "left_elbow_angle",
            "left_hip_angle",
            "left_knee_angle",
            "left_ankle_angle",
            "right_shoulder_angle",
            "right_elbow_angle",
            "right_hip_angle",
            "right_knee_angle",
            "right_ankle_angle",
            "dominant_side",
            "person_detected"
        ]
        
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=headers)
        self.csv_writer.writeheader()
        self.recording = True
        print(f"Recording started: {filename}")
        return filename
    
    def log_frame(self, frame_number, angles_left, angles_right, dominant_side, detected):
        """Log frame data to CSV."""
        if not self.recording or self.csv_writer is None:
            return
        
        row = {
            "timestamp": time.time(),
            "frame_number": frame_number,
            "left_shoulder_angle": angles_left.get("left_shoulder_angle", ""),
            "left_elbow_angle": angles_left.get("left_elbow_angle", ""),
            "left_hip_angle": angles_left.get("left_hip_angle", ""),
            "left_knee_angle": angles_left.get("left_knee_angle", ""),
            "left_ankle_angle": angles_left.get("left_ankle_angle", ""),
            "right_shoulder_angle": angles_right.get("right_shoulder_angle", ""),
            "right_elbow_angle": angles_right.get("right_elbow_angle", ""),
            "right_hip_angle": angles_right.get("right_hip_angle", ""),
            "right_knee_angle": angles_right.get("right_knee_angle", ""),
            "right_ankle_angle": angles_right.get("right_ankle_angle", ""),
            "dominant_side": dominant_side,
            "person_detected": detected
        }
        self.csv_writer.writerow(row)
    
    def stop_recording(self):
        """Stop recording and close CSV file."""
        if self.csv_file:
            self.csv_file.close()
            self.recording = False
            print("Recording stopped")


# Initialize camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    print("Error: Cannot open camera")
    exit()

# Initialize recorder
recorder = PoseCaptureRecorder("pose_data")

# FPS tracking
fps_buffer = deque(maxlen=30)
frame_count = 0
start_time = time.time()

print("Advanced Pose Capture Started")
print("Controls:")
print("  'q' - Quit")
print("  'r' - Start/Stop recording")
print("  's' - Save frame")
print("  'p' - Toggle pose drawing")
print("  'a' - Toggle angle display")

draw_pose = True
show_angles = True

with mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    smooth_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
) as pose:
    
    while True:
        success, frame = cap.read()
        if not success:
            break
        
        frame = cv2.flip(frame, 1)
        h, w, c = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        results = pose.process(frame_rgb)
        
        # Extract and display pose data
        angles_left = {}
        angles_right = {}
        dominant_side = ""
        person_detected = False
        
        if results.pose_landmarks:
            person_detected = True
            
            # Draw pose skeleton
            if draw_pose:
                mp_drawing.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
                )
            
            # Extract all angles
            angles_left = extract_pose_angles(results.pose_landmarks.landmark, LEFT_SIDE, "left")
            angles_right = extract_pose_angles(results.pose_landmarks.landmark, RIGHT_SIDE, "right")
            
            # Get dominant side info
            dominant_angles, dominant_side = get_dominant_side(results.pose_landmarks.landmark)
            
            # Display angles if enabled
            if show_angles:
                y_offset = 50
                cv2.putText(frame, "Angles (degrees):", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                y_offset += 25
                
                for key, value in dominant_angles.items():
                    text = f"{key.replace('_', ' ').title()}: {value:.1f}°"
                    cv2.putText(frame, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    y_offset += 20
            
            # Log data if recording
            if recorder.recording:
                recorder.log_frame(frame_count, angles_left, angles_right, dominant_side, True)
        
        # Calculate and display FPS
        frame_count += 1
        elapsed = time.time() - start_time
        if elapsed > 0:
            current_fps = frame_count / elapsed
            fps_buffer.append(current_fps)
            avg_fps = np.mean(fps_buffer) if fps_buffer else 0
        
        # Display status
        status_text = "✓ Pose Detected" if person_detected else "✗ No Pose"
        status_color = (0, 255, 0) if person_detected else (0, 0, 255)
        
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        recording_text = "REC" if recorder.recording else "---"
        recording_color = (0, 0, 255) if recorder.recording else (100, 100, 100)
        cv2.putText(frame, recording_text, (w - 60, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, recording_color, 3)
        
        cv2.putText(frame, f"FPS: {avg_fps:.1f}", (w - 200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Display controls hint
        cv2.putText(
            frame,
            "q:quit | r:record | s:save | p:pose | a:angles",
            (10, h - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1
        )
        
        cv2.imshow("Advanced Pose Capture", frame)
        
        # Handle input
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            if recorder.recording:
                recorder.stop_recording()
            break
        elif key == ord('r'):
            if recorder.recording:
                recorder.stop_recording()
            else:
                recorder.start_recording()
        elif key == ord('s'):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join("pose_captures", f"pose_frame_{timestamp}.png")
            os.makedirs("pose_captures", exist_ok=True)
            cv2.imwrite(filename, frame)
            print(f"Frame saved: {filename}")
        elif key == ord('p'):
            draw_pose = not draw_pose
        elif key == ord('a'):
            show_angles = not show_angles

cap.release()
cv2.destroyAllWindows()
print("Advanced pose capture closed")
