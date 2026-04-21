#!/usr/bin/env python
"""Check PoseLandmarkerOptions parameters."""

import sys
sys.path.insert(0, '.')

from mediapipe.tasks.python.vision import pose_landmarker

# Check available parameters
print("PoseLandmarkerOptions signature:")
import inspect
sig = inspect.signature(pose_landmarker.PoseLandmarkerOptions)
print(sig)
print()

print("Available parameters:")
for param_name, param in sig.parameters.items():
    print(f"  - {param_name}: {param.annotation if param.annotation != inspect.Parameter.empty else 'Any'}")
