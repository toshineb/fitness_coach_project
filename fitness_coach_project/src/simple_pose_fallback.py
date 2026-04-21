#!/usr/bin/env python
"""
Lightweight pose detection fallback using computer vision heuristics.
When MediaPipe is unavailable, this provides basic pose landmark detection.
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SimpleLandmark:
    """Simple landmark representation."""
    x: float
    y: float
    z: float = 0.0
    visibility: float = 1.0
    presence: float = 1.0


class SimplePoseDetector:
    """
    Very simple pose detection using contour analysis and skin detection.
    This is a fallback when MediaPipe isn't available.
    """
    
    def __init__(self):
        self.landmarks = []
    
    def detect(self, image: np.ndarray) -> List[SimpleLandmark]:
        """
        Detect pose using heuristics.
        Returns 33 landmarks in MediaPipe format (or best approximation).
        """
        landmarks = []
        h, w = image.shape[:2]
        
        # Convert to HSV for skin detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Define skin color range
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        # Also try other skin tone ranges
        lower_skin2 = np.array([0, 10, 60], dtype=np.uint8)
        upper_skin2 = np.array([180, 255, 255], dtype=np.uint8)
        mask2 = cv2.inRange(hsv, lower_skin2, upper_skin2)
        
        mask = cv2.bitwise_or(mask, mask2)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) == 0:
            # No skin detected - return default empty landmarks
            for i in range(33):
                landmarks.append(SimpleLandmark(0.5, 0.5, 0, 0, 0))
            return landmarks
        
        # Find the largest contour (likely the body)
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, width, height = cv2.boundingRect(largest_contour)
        
        # Estimate body parts based on bounding box
        # This is very approximate!
        
        # Normalize coordinates to 0-1 range
        body_x = (x + width / 2) / w
        body_y = (y + height / 2) / h
        
        # Create 33 landmarks (MediaPipe pose format)
        # Most will be zero confidence, but some key points based on bounding box
        
        # Head area (landmarks 0)
        landmarks.append(SimpleLandmark(body_x, y / h, 0, 0.3, 0.3))  # Nose
        
        # Shoulders
        shoulder_y = (y + height * 0.3) / h
        landmarks.append(SimpleLandmark(body_x - 0.15, shoulder_y, 0, 0.2, 0.2))  # Left shoulder
        landmarks.append(SimpleLandmark(body_x + 0.15, shoulder_y, 0, 0.2, 0.2))  # Right shoulder
        
        # Fill remaining landmarks with low confidence
        for i in range(3, 33):
            landmarks.append(SimpleLandmark(body_x + np.random.normal(0, 0.1),
                                           body_y + np.random.normal(0, 0.1),
                                           0, 0.05, 0.05))
        
        return landmarks
