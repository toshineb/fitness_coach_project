#!/usr/bin/env python
"""Try to download and setup MediaPipe pose model."""

import sys
import os

# Try the MediaPipe model downloader
try:
    from mediapipe import tasks
    print("Checking MediaPipe tasks module...")
    print(f"Tasks attributes: {[x for x in dir(tasks) if not x.startswith('_')]}")
except Exception as e:
    print(f"Error: {e}")

# Check for download utilities
try:
    import mediapipe as mp
    if hasattr(mp, 'solutions'):
        print("✅ MediaPipe solutions available")
    else:
        print("❌ No solutions module")
except Exception as e:
    print(f"Error: {e}")

# Try creating a model from blob/bytes
try:
    from mediapipe.tasks.python.core import base_options as base_options_module
    from mediapipe.tasks.python.vision import pose_landmarker
    
    # Check what parameters BaseOptions accepts
    import inspect
    sig = inspect.signature(base_options_module.BaseOptions)
    print("\nBaseOptions parameters:")
    for param_name, param in sig.parameters.items():
        print(f"  {param_name}: {param.annotation if param.annotation != inspect.Parameter.empty else 'Any'}")
        
except Exception as e:
    print(f"Error inspecting BaseOptions: {e}")
