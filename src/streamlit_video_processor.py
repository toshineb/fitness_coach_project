"""
Video processing utilities for Streamlit application.
Handles video files, webcam input, and frame-by-frame analysis.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

import cv2
import numpy as np
from streamlit_pose_helper import PoseFrame, process_frame, StreamlitPoseCoach, safe_float


@dataclass
class VideoMetrics:
    """Metrics for video analysis."""
    total_frames: int = 0
    processed_frames: int = 0
    correct_frames: int = 0
    incorrect_frames: int = 0
    reps_completed: int = 0
    exercises_detected: Dict[str, int] = None
    feedback_list: List[str] = None
    accuracy: float = 0.0
    
    def __post_init__(self):
        if self.exercises_detected is None:
            self.exercises_detected = {}
        if self.feedback_list is None:
            self.feedback_list = []
    
    def calculate_accuracy(self):
        """Calculate overall accuracy."""
        if self.processed_frames > 0:
            self.accuracy = (self.correct_frames / self.processed_frames) * 100
        return self.accuracy
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_frames": self.total_frames,
            "processed_frames": self.processed_frames,
            "correct_frames": self.correct_frames,
            "incorrect_frames": self.incorrect_frames,
            "reps_completed": self.reps_completed,
            "exercises_detected": self.exercises_detected,
            "accuracy": self.calculate_accuracy(),
        }


class RepetitionCounter:
    """Track repetitions in exercise video."""
    
    def __init__(self, exercise_name: str):
        self.exercise_name = exercise_name.lower()
        self.reps = 0
        self.in_rep = False
        self.prev_state = None
        self.knee_angle_history = []
        self.hip_angle_history = []
        self.elbow_angle_history = []
        
    def get_movement_state(self, features: Dict[str, float]) -> str:
        """Determine if in 'up' or 'down' position."""
        knee = safe_float(features.get("Knee_Angle", 0))
        hip = safe_float(features.get("Hip_Angle", 0))
        elbow = safe_float(features.get("Elbow_Angle", 0))
        
        self.knee_angle_history.append(knee)
        self.hip_angle_history.append(hip)
        self.elbow_angle_history.append(elbow)
        
        # Keep only last 5 frames
        if len(self.knee_angle_history) > 5:
            self.knee_angle_history.pop(0)
            self.hip_angle_history.pop(0)
            self.elbow_angle_history.pop(0)
        
        if "squat" in self.exercise_name:
            return "down" if knee < 120 else "up"
        elif "push" in self.exercise_name:
            return "down" if elbow < 100 else "up"
        elif "lunge" in self.exercise_name:
            return "down" if knee < 100 else "up"
        elif "deadlift" in self.exercise_name:
            return "down" if hip < 100 else "up"
        elif "bicep" in self.exercise_name or "curl" in self.exercise_name:
            return "down" if elbow < 100 else "up"
        
        return "unknown"
    
    def update(self, features: Dict[str, float]) -> Tuple[int, bool]:
        """Update repetition count based on features."""
        state = self.get_movement_state(features)
        
        if self.prev_state is None:
            self.prev_state = state
            return self.reps, False
        
        # Completed a full rep when returning to up position
        if self.prev_state == "down" and state == "up":
            self.reps += 1
            self.prev_state = state
            return self.reps, True
        
        self.prev_state = state
        return self.reps, False


def process_video_file(
    video_path: str,
    coach: StreamlitPoseCoach,
    selected_exercise: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Tuple[List[np.ndarray], VideoMetrics, List[Dict[str, Any]]]:
    """Process entire video file and return analyzed frames."""
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    metrics = VideoMetrics(total_frames=total_frames)
    rep_counter = RepetitionCounter(selected_exercise)
    
    output_frames = []
    analysis_results = []
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Resize for processing
        frame = cv2.resize(frame, (640, 480))
        
        # Process frame
        pose_frame = process_frame(frame)
        analysis = coach.analyze_frame(pose_frame)
        
        metrics.processed_frames += 1
        
        # Track exercise
        exercise = analysis["exercise"]
        if exercise != "Unknown":
            metrics.exercises_detected[exercise] = metrics.exercises_detected.get(exercise, 0) + 1
        
        # Update rep counter if correct exercise
        if exercise.lower() in selected_exercise.lower():
            reps, is_new_rep = rep_counter.update(analysis["features"])
            metrics.reps_completed = reps
            
            if len(analysis["feedback"]) > 0:
                if "✅" in analysis["feedback"][0]:
                    metrics.correct_frames += 1
                else:
                    metrics.incorrect_frames += 1
        
        analysis_results.append(analysis)
        
        # Draw info on frame
        output_frame = pose_frame.frame.copy()
        y = 30
        
        cv2.putText(output_frame, f"Exercise: {exercise}", (20, y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        y += 35
        
        for feedback in analysis["feedback"][:2]:
            cv2.putText(output_frame, feedback, (20, y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y += 30
        
        cv2.putText(output_frame, f"Reps: {metrics.reps_completed}", (20, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        
        output_frames.append(output_frame)
        
        # Progress callback
        if progress_callback:
            progress_callback(frame_count, total_frames)
    
    cap.release()
    metrics.calculate_accuracy()
    
    return output_frames, metrics, analysis_results


def process_webcam_frame(
    frame: np.ndarray,
    coach: StreamlitPoseCoach,
    selected_exercise: str,
) -> Tuple[np.ndarray, Dict[str, Any], bool]:
    """Process a single webcam frame."""
    frame = cv2.resize(frame, (640, 480))
    pose_frame = process_frame(frame)
    analysis = coach.analyze_frame(pose_frame)
    
    # Draw on frame
    output_frame = pose_frame.frame.copy()
    y = 30
    
    exercise = analysis["exercise"]
    cv2.putText(output_frame, f"Exercise: {exercise}", (20, y),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    y += 35
    
    for feedback in analysis["feedback"][:2]:
        cv2.putText(output_frame, feedback, (20, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        y += 30
    
    is_correct = exercise.lower() in selected_exercise.lower()
    
    return output_frame, analysis, is_correct


def save_video_output(
    frames: List[np.ndarray],
    output_path: str,
    fps: float = 30.0,
) -> bool:
    """Save processed frames to video file."""
    if not frames:
        return False
    
    frame_height, frame_width = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    
    for frame in frames:
        out.write(frame)
    
    out.release()
    return True
