#!/usr/bin/env python
"""Download MediaPipe pose landmarker model."""

import urllib.request
import os

# Try different model URLs
model_urls = [
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker/float16/latest/pose_landmarker.task",
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker/float16/pose_landmarker.task",
    "https://storage.googleapis.com/mediapipe-models/latest/pose_landmarker.task",
]

model_path = "pose_landmarker.task"

for model_url in model_urls:
    print(f"Trying: {model_url}")
    try:
        urllib.request.urlretrieve(model_url, model_path)
        file_size = os.path.getsize(model_path)
        print(f"✅ Download successful! File size: {file_size / 1024 / 1024:.2f} MB")
        break
    except urllib.error.HTTPError as e:
        print(f"  ❌ HTTP {e.code}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
else:
    print("\n⚠️  Could not download model. Trying alternative approach...")
    
    # List available models online
    print("\nChecking for available models...")
    try:
        # Create the model automatically if possible
        from mediapipe.tasks.python.vision import pose_landmarker
        from mediapipe.tasks import python as mp_python
        
        # Check if we can find the bundled model
        import mediapipe
        mp_dir = os.path.dirname(mediapipe.__file__)
        print(f"MediaPipe installation directory: {mp_dir}")
        
        # Search for .task files
        for root, dirs, files in os.walk(mp_dir):
            for file in files:
                if file.endswith('.task'):
                    print(f"Found model: {os.path.join(root, file)}")
    except Exception as e:
        print(f"Could not search for bundled models: {e}")
