"""
Modern MediaPipe Pose Capture using Tasks API (MediaPipe 0.10.33)
Real-time pose detection and visualization using camera feed.
"""

import cv2
import numpy as np
import os
from datetime import datetime
from collections import deque
import sys

try:
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    from mediapipe.framework.formats import landmark_pb2
except ImportError as e:
    print(f"Error importing MediaPipe tasks: {e}")
    print("Trying alternative import...")
    try:
        import mediapipe as mp
        print(f"MediaPipe available modules: {dir(mp)}")
    except:
        pass
    sys.exit(1)

# Model file path
MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "models",
    "pose_landmarker.task"
)

def download_pose_model():
    """Download the pose landmarker model if not present."""
    model_url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker/float16/1/pose_landmarker.task"
    
    if os.path.exists(MODEL_PATH):
        return MODEL_PATH
    
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    
    print(f"Downloading pose model to {MODEL_PATH}...")
    try:
        import urllib.request
        urllib.request.urlretrieve(model_url, MODEL_PATH)
        print("Model downloaded successfully!")
        return MODEL_PATH
    except Exception as e:
        print(f"Error downloading model: {e}")
        return None

def calculate_angle(p1, p2, p3):
    """Calculate angle between three points."""
    a = np.array([p1.x, p1.y])
    b = np.array([p2.x, p2.y])
    c = np.array([p3.x, p3.y])
    
    ba = a - b
    bc = c - b
    
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom == 0:
        return 0
    
    cosine = np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)
    angle = float(np.degrees(np.arccos(cosine)))
    return angle

def main():
    print("MediaPipe Pose Capture (Modern API)")
    
    # Try to get or download the model
    model_path = MODEL_PATH
    if not os.path.exists(model_path):
        model_path = download_pose_model()
        if not model_path:
            print("Could not locate pose model. Creating basic fallback visualization...")
            return
    
    # Create pose landmarker
    try:
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            output_segmentation_masks=False
        )
        detector = vision.PoseLandmarker.create_from_options(options)
    except Exception as e:
        print(f"Error creating pose detector: {e}")
        return
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open camera")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    print("Camera opened successfully!")
    print("Controls: 'q' to quit, 's' to save frame, 'p' to toggle skeleton")
    
    fps_buffer = deque(maxlen=30)
    frame_count = 0
    import time
    start_time = time.time()
    
    draw_skeleton = True
    
    while True:
        success, frame = cap.read()
        if not success:
            break
        
        frame = cv2.flip(frame, 1)
        h, w, c = frame.shape
        
        # Convert to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = vision.Image(image_format=vision.ImageFormat.SRGB, data=frame_rgb)
        
        # Detect pose
        try:
            detection_result = detector.detect(mp_image)
            poses = detection_result.pose_landmarks
            
            if poses and draw_skeleton:
                for pose in poses:
                    # Draw landmarks
                    for landmark in pose:
                        x = int(landmark.x * w)
                        y = int(landmark.y * h)
                        cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)
                    
                    # Draw connections (simplified version)
                    connections = [
                        (11, 13), (13, 15),  # Right arm
                        (12, 14), (14, 16),  # Left arm
                        (11, 12),             # Shoulders
                        (11, 23), (12, 24),  # Torso
                        (23, 25), (25, 27),  # Right leg
                        (24, 26), (26, 28),  # Left leg
                    ]
                    
                    for start_idx, end_idx in connections:
                        if start_idx < len(pose) and end_idx < len(pose):
                            start = pose[start_idx]
                            end = pose[end_idx]
                            x1, y1 = int(start.x * w), int(start.y * h)
                            x2, y2 = int(end.x * w), int(end.y * h)
                            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Calculate and display some angles if we have landmarks
                if len(poses[0]) >= 16:
                    try:
                        shoulder_angle = calculate_angle(poses[0][11], poses[0][13], poses[0][15])
                        cv2.putText(frame, f"Right Shoulder: {shoulder_angle:.1f}°", (10, 50),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    except:
                        pass
        
        except Exception as e:
            pass
        
        # Calculate FPS
        frame_count += 1
        elapsed = time.time() - start_time
        if elapsed > 0:
            fps_buffer.append(frame_count / elapsed)
            avg_fps = np.mean(fps_buffer) if fps_buffer else 0
        
        # Display info
        cv2.putText(frame, f"FPS: {avg_fps:.1f}", (w - 150, 30),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Skeleton: {'ON' if draw_skeleton else 'OFF'}", (10, 30),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "q:quit | s:save | p:toggle skeleton", (10, h - 10),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        cv2.imshow("MediaPipe Pose Capture", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs("pose_captures", exist_ok=True)
            filename = os.path.join("pose_captures", f"pose_{timestamp}.png")
            cv2.imwrite(filename, frame)
            print(f"Saved: {filename}")
        elif key == ord('p'):
            draw_skeleton = not draw_skeleton
    
    cap.release()
    cv2.destroyAllWindows()
    print("Closed.")

if __name__ == "__main__":
    main()
