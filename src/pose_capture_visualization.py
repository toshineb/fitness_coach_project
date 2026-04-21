"""
Simple real-time pose capture and visualization using MediaPipe.
Press 'q' to quit, 's' to save a frame screenshot.
"""

import cv2
import numpy as np
import os
from datetime import datetime

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

# Initialize video capture (0 is default camera)
cap = cv2.VideoCapture(0)

# Set camera properties for better performance
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    print("Error: Cannot open camera")
    exit()

# Create output directory for screenshots
output_dir = "pose_captures"
os.makedirs(output_dir, exist_ok=True)

# FPS calculation variables
frame_count = 0
fps = 0
start_time = cv2.getTickCount()

print("Starting pose capture visualization...")
print("Controls:")
print("  'q' - Quit")
print("  's' - Save frame")
print("  'p' - Toggle pose drawing on/off")
print("  'c' - Toggle confidence visualization")

draw_pose = True
show_confidence = True

# Create pose detector with specified confidence thresholds
with mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,  # 0=light, 1=full, 2=heavy
    smooth_landmarks=True,
    enable_segmentation=False,
    smooth_segmentation=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
) as pose:
    
    while True:
        success, frame = cap.read()
        
        if not success:
            print("Failed to read frame")
            break
        
        # Flip the frame horizontally for a selfie-view display
        frame = cv2.flip(frame, 1)
        h, w, c = frame.shape
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame to detect pose
        results = pose.process(frame_rgb)
        
        # Draw pose landmarks and connections
        if results.pose_landmarks and draw_pose:
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
            )
        
        # Display confidence scores if enabled
        if show_confidence and results.pose_landmarks:
            y_offset = 30
            for idx, landmark in enumerate(results.pose_landmarks.landmark):
                # Only show confidence for selected joints (to avoid clutter)
                joints_to_show = [
                    mp_pose.PoseLandmark.NOSE,
                    mp_pose.PoseLandmark.LEFT_SHOULDER,
                    mp_pose.PoseLandmark.RIGHT_SHOULDER,
                    mp_pose.PoseLandmark.LEFT_HIP,
                    mp_pose.PoseLandmark.RIGHT_HIP,
                    mp_pose.PoseLandmark.LEFT_KNEE,
                    mp_pose.PoseLandmark.RIGHT_KNEE,
                    mp_pose.PoseLandmark.LEFT_ANKLE,
                    mp_pose.PoseLandmark.RIGHT_ANKLE,
                ]
                
                if idx in [jnt.value for jnt in joints_to_show]:
                    cv2.putText(
                        frame,
                        f"{landmark.visibility:.2f}",
                        (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.4,
                        (0, 255, 0),
                        1
                    )
                    y_offset += 20
        
        # Calculate and display FPS
        frame_count += 1
        if frame_count % 30 == 0:
            end_time = cv2.getTickCount()
            time_elapsed = (end_time - start_time) / cv2.getTickFrequency()
            fps = 30 / time_elapsed
            start_time = cv2.getTickCount()
        
        # Display info text
        info_text = f"FPS: {fps:.1f}"
        if draw_pose:
            info_text += " | Pose: ON"
        else:
            info_text += " | Pose: OFF"
        
        if show_confidence:
            info_text += " | Conf: ON"
        else:
            info_text += " | Conf: OFF"
        
        cv2.putText(
            frame,
            info_text,
            (w - 300, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )
        
        # Display detection status
        if results.pose_landmarks:
            status_text = "✓ Pose Detected"
            status_color = (0, 255, 0)
        else:
            status_text = "✗ No Pose Detected"
            status_color = (0, 0, 255)
        
        cv2.putText(
            frame,
            status_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            status_color,
            2
        )
        
        # Display controls hint
        cv2.putText(
            frame,
            "Press 'q' to quit | 's' to save | 'p' pose toggle | 'c' confidence toggle",
            (10, h - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1
        )
        
        # Show the frame
        cv2.imshow("MediaPipe Pose Capture", frame)
        
        # Handle keyboard input
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("Quitting...")
            break
        elif key == ord('s'):
            # Save screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(output_dir, f"pose_capture_{timestamp}.png")
            cv2.imwrite(filename, frame)
            print(f"Frame saved: {filename}")
        elif key == ord('p'):
            # Toggle pose drawing
            draw_pose = not draw_pose
            status = "ON" if draw_pose else "OFF"
            print(f"Pose drawing: {status}")
        elif key == ord('c'):
            # Toggle confidence visualization
            show_confidence = not show_confidence
            status = "ON" if show_confidence else "OFF"
            print(f"Confidence display: {status}")

# Release resources
cap.release()
cv2.destroyAllWindows()
print("Pose capture closed.")
