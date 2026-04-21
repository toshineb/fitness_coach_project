"""
OpenCV-based Pose Detection (Fallback when MediaPipe tasks API isn't available)
Uses pre-trained models for pose estimation.
"""

import cv2
import numpy as np
import os
from datetime import datetime
from collections import deque

# OpenPose model files
PROTO_FILE = "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/dnn/openpose/coco/pose_deploy_linevec.prototxt"
WEIGHTS_FILE = "http://posefs1.mediamatica.com/files/model/coco/pose_iter_440000.caffemodel"

# COCO body part indexes
BODY_PARTS = {
    "Head": 0, "Neck": 1, "RShoulder": 2, "RElbow": 3, "RWrist": 4,
    "LShoulder": 5, "LElbow": 6, "LWrist": 7, "RHip": 8, "RKnee": 9,
    "RAnkle": 10, "LHip": 11, "LKnee": 12, "LAnkle": 13, "Chest": 14,
    "Background": 15
}

POSE_PAIRS = [
    ("Neck", "RShoulder"), ("RShoulder", "RElbow"), ("RElbow", "RWrist"),
    ("Neck", "LShoulder"), ("LShoulder", "LElbow"), ("LElbow", "LWrist"),
    ("Neck", "Chest"), ("Chest", "RHip"), ("RHip", "RKnee"), ("RKnee", "RAnkle"),
    ("Chest", "LHip"), ("LHip", "LKnee"), ("LKnee", "LAnkle"),
]

def download_model():
    """Download OpenPose model files."""
    model_dir = "models"
    os.makedirs(model_dir, exist_ok=True)
    
    proto_file = os.path.join(model_dir, "pose_deploy_linevec.prototxt")
    weights_file = os.path.join(model_dir, "pose_iter_440000.caffemodel")
    
    if os.path.exists(proto_file) and os.path.exists(weights_file):
        return proto_file, weights_file
    
    print("Downloading OpenPose models (this may take a moment)...")
    try:
        import urllib.request
        if not os.path.exists(proto_file):
            print(f"Downloading {proto_file.split('/')[-1]}...")
            urllib.request.urlretrieve(PROTO_FILE, proto_file)
        if not os.path.exists(weights_file):
            print(f"Downloading {weights_file.split('/')[-1]}...")
            urllib.request.urlretrieve(WEIGHTS_FILE, weights_file)
        print("Models downloaded successfully!")
        return proto_file, weights_file
    except Exception as e:
        print(f"Error downloading models: {e}")
        print("You can manually download from:")
        print(f"  Proto: {PROTO_FILE}")
        print(f"  Weights: {WEIGHTS_FILE}")
        return None, None

def draw_pose(frame, detected_keypoints, width, height):
    """Draw pose keypoints and connections on frame."""
    for i, person_keypoints in enumerate(detected_keypoints):
        for j, (body_part, keypoint) in enumerate(person_keypoints.items()):
            if keypoint[2] > 0.1:  # Confidence threshold
                x = int(keypoint[0] * width)
                y = int(keypoint[1] * height)
                cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)
    
    # Draw connections
    for pair in POSE_PAIRS:
        part1, part2 = pair
        idx1, idx2 = BODY_PARTS[part1], BODY_PARTS[part2]
        
        for person_keypoints in detected_keypoints:
            try:
                if person_keypoints[part1][2] > 0.1 and person_keypoints[part2][2] > 0.1:
                    x1 = int(person_keypoints[part1][0] * width)
                    y1 = int(person_keypoints[part1][1] * height)
                    x2 = int(person_keypoints[part2][0] * width)
                    y2 = int(person_keypoints[part2][1] * height)
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            except:
                pass

def main():
    print("OpenCV-based Pose Capture")
    print("=" * 50)
    
    # Try to get models
    proto_file, weights_file = download_model()
    if not proto_file or not weights_file:
        print("ERROR: Could not locate model files.")
        print("Please manually download the models or ensure internet connection.")
        return
    
    # Load network
    print("Loading pose detection model...")
    try:
        net = cv2.dnn.readNetFromCaffe(proto_file, weights_file)
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Error loading model: {e}")
        return
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Cannot open camera")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    print(f"Camera resolution: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x{cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")
    print("\nControls:")
    print("  'q' - Quit")
    print("  's' - Save frame")
    print("  'p' - Toggle skeleton")
    print("=" * 50)
    
    fps_buffer = deque(maxlen=30)
    frame_count = 0
    import time
    start_time = time.time()
    
    draw_skeleton = True
    inHeight = 368
    inWidth = int((inHeight / cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) * cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        height, width, _ = frame.shape
        
        # Prepare input blob
        blob = cv2.dnn.blobFromImage(frame, 1.0 / 255, (inWidth, inHeight), 
                                     (0, 0, 0), swapRB=False, crop=False)
        
        # Get predictions
        net.setInput(blob)
        try:
            output = net.forward()
        except Exception as e:
            print(f"Inference error: {e}")
            break
        
        # Parse output
        detected_keypoints = []
        keypoint_id = 0
        detected_keypoints.append({})
        
        for i in range(len(BODY_PARTS)):
            probMap = output[0, i, :, :]
            probMap = cv2.resize(probMap, (width, height))
            
            _, prob, _, point = cv2.minMaxLoc(probMap)
            if prob > 0.1:
                if not detected_keypoints[-1]:
                    detected_keypoints[-1] = {}
                
                body_part_name = [k for k, v in BODY_PARTS.items() if v == i][0]
                detected_keypoints[-1][body_part_name] = (point[0] / width, point[1] / height, prob)
        
        # Draw pose
        if draw_skeleton and detected_keypoints[0]:
            draw_pose(frame, detected_keypoints, width, height)
        
        # Calculate FPS
        frame_count += 1
        elapsed = time.time() - start_time
        if elapsed > 0:
            fps_buffer.append(frame_count / elapsed)
            avg_fps = np.mean(fps_buffer) if fps_buffer else 0
        
        # Display info
        status = "✓ Pose Detected" if detected_keypoints[0] else "✗ No Pose"
        status_color = (0, 255, 0) if detected_keypoints[0] else (0, 0, 255)
        
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        cv2.putText(frame, f"FPS: {avg_fps:.1f}", (width - 200, 30),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Skeleton: {'ON' if draw_skeleton else 'OFF'}", (10, 60),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        cv2.putText(frame, "q:quit | s:save | p:toggle", (10, height - 10),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        cv2.imshow("OpenCV Pose Capture", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("\nQuitting...")
            break
        elif key == ord('s'):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs("pose_captures", exist_ok=True)
            filename = os.path.join("pose_captures", f"pose_{timestamp}.png")
            cv2.imwrite(filename, frame)
            print(f"✓ Saved: {filename}")
        elif key == ord('p'):
            draw_skeleton = not draw_skeleton
            print(f"Skeleton: {'ON' if draw_skeleton else 'OFF'}")
    
    cap.release()
    cv2.destroyAllWindows()
    print("Pose capture closed.")

if __name__ == "__main__":
    main()
