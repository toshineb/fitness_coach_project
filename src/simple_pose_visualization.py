"""
Simple Pose Visualization using Background Subtraction and Contours.
"""

import cv2
import numpy as np
import os
from datetime import datetime
from collections import deque

def main():
    print("Simple Pose Visualization")
    print("=" * 60)
    print("This creates a silhouette-based pose visualization")
    print("=" * 60)
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Cannot open camera")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Camera resolution: {width}x{height}")
    print("\nControls:")
    print("  'q' - Quit")
    print("  's' - Save frame")
    print("  'e' - Edge detection mode")
    print("  'c' - Contour mode")
    print("  'b' - Background subtraction mode")
    print("=" * 60)
    
    # Background subtractor
    fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows=False)
    
    fps_buffer = deque(maxlen=30)
    frame_count = 0
    import time
    start_time = time.time()
    
    mode = "contour"  # contour, edge, background
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(frame, (21, 21), 0)
        
        # Convert to grayscale
        gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
        
        # Process based on mode
        if mode == "edge":
            # Canny edge detection
            edges = cv2.Canny(gray, 100, 200)
            display = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            display_copy = frame.copy()
            cv2.drawContours(display_copy, cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0], -1, (0, 255, 0), 2)
            
        elif mode == "background":
            # Background subtraction
            fgmask = fgbg.apply(frame)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_CLOSE, kernel)
            
            display = frame.copy()
            contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # Filter out small contours
                    cv2.drawContours(display, [contour], 0, (0, 255, 0), 2)
                    
                    # Draw bounding box
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(display, (x, y), (x + w, y + h), (255, 0, 0), 2)
            
            display_copy = display
        
        else:  # contour mode (default)
            # Binary threshold
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            display_copy = frame.copy()
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # Filter small contours
                    # Draw filled contour (person silhouette)
                    cv2.drawContours(display_copy, [contour], 0, (0, 255, 0), 2)
                    
                    # Find hull for skeleton-like representation
                    hull = cv2.convexHull(contour)
                    cv2.drawContours(display_copy, [hull], 0, (255, 0, 0), 1)
                    
                    # Get approx polygon for simplified shape
                    epsilon = 0.02 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)
                    
                    # Draw circles at key points
                    for point in approx:
                        cv2.circle(display_copy, tuple(point[0]), 5, (0, 0, 255), -1)
        
        # Calculate FPS
        frame_count += 1
        elapsed = time.time() - start_time
        if elapsed > 0:
            fps_buffer.append(frame_count / elapsed)
            avg_fps = np.mean(fps_buffer) if fps_buffer else 0
        
        # Display info
        mode_text = f"Mode: {mode.upper()}"
        cv2.putText(display_copy, mode_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display_copy, f"FPS: {avg_fps:.1f}", (width - 200, 30),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display_copy, "e:edge | c:contour | b:background | q:quit | s:save", (10, height - 10),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        cv2.imshow("Pose Visualization", display_copy)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("\nQuitting...")
            break
        elif key == ord('s'):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs("pose_captures", exist_ok=True)
            filename = os.path.join("pose_captures", f"pose_{timestamp}.png")
            cv2.imwrite(filename, display_copy)
            print(f"✓ Saved: {filename}")
        elif key == ord('e'):
            mode = "edge"
            print("Mode: EDGE DETECTION")
        elif key == ord('c'):
            mode = "contour"
            print("Mode: CONTOUR")
        elif key == ord('b'):
            mode = "background"
            print("Mode: BACKGROUND SUBTRACTION")
    
    cap.release()
    cv2.destroyAllWindows()
    print("\n✓ Pose visualization closed.")

if __name__ == "__main__":
    main()
