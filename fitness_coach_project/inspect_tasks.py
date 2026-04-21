#!/usr/bin/env python
"""Inspect MediaPipe tasks structure."""

import mediapipe as mp
print("MediaPipe tasks attributes:")
tasks = mp.tasks
print(dir(tasks))
print()

print("Tasks submodules:")
import pkgutil
for importer, modname, ispkg in pkgutil.iter_modules(tasks.__path__):
    print(f"  - {modname} (package: {ispkg})")

print()

# Try to import vision
try:
    from mediapipe.tasks import vision
    print("✅ vision module imported")
    print("Vision subclasses:")
    print(dir(vision)[:20])
except ImportError as e:
    print(f"❌ Failed to import vision: {e}")

print()

# Check for PoseLandmarker
try:
    from mediapipe.tasks.python.vision import pose_landmarker
    print("✅ pose_landmarker module imported")
    print("Attributes:")
    print(dir(pose_landmarker))
except ImportError as e:
    print(f"❌ Failed to import pose_landmarker: {e}")
