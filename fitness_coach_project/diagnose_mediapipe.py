#!/usr/bin/env python
"""Diagnose MediaPipe installation and imports."""

import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print()

# Test MediaPipe imports
print("=" * 60)
print("Testing MediaPipe imports...")
print("=" * 60)

try:
    import mediapipe as mp
    print(f"✅ mediapipe version: {mp.__version__ if hasattr(mp, '__version__') else 'unknown'}")
except ImportError as e:
    print(f"❌ Cannot import mediapipe: {e}")
    sys.exit(1)

# Test direct import
print("\n--- Testing direct import ---")
try:
    from mediapipe.python.solutions import pose as mp_pose
    from mediapipe.python.solutions import drawing_utils as mp_drawing
    print(f"✅ Direct import successful")
    print(f"   mp_pose type: {type(mp_pose)}")
    print(f"   mp_pose attributes: {dir(mp_pose)[:5]}...")
    
    # Test Pose class
    if hasattr(mp_pose, 'Pose'):
        print(f"✅ mp_pose.Pose exists")
        try:
            pose_detector = mp_pose.Pose(
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            print(f"✅ Pose detector initialized successfully")
            print(f"   Type: {type(pose_detector)}")
        except Exception as e:
            print(f"❌ Failed to initialize Pose: {e}")
    else:
        print(f"❌ mp_pose.Pose does not exist")
        
    # Test POSE_CONNECTIONS
    if hasattr(mp_pose, 'POSE_CONNECTIONS'):
        print(f"✅ POSE_CONNECTIONS exists")
    else:
        print(f"❌ POSE_CONNECTIONS does not exist")
        
except ImportError as e:
    print(f"❌ Direct import failed: {e}")

# Test modern import
print("\n--- Testing modern import (mediapipe.solutions) ---")
try:
    from mediapipe import solutions
    print(f"✅ solutions module imported")
    print(f"   solutions type: {type(solutions)}")
    
    if hasattr(solutions, 'pose'):
        print(f"✅ solutions.pose exists")
        pose_module = solutions.pose
        
        if hasattr(pose_module, 'Pose'):
            print(f"✅ solutions.pose.Pose exists")
        else:
            print(f"❌ solutions.pose.Pose does not exist")
    else:
        print(f"❌ solutions.pose does not exist")
        
except ImportError as e:
    print(f"❌ Modern import failed: {e}")

# Test legacy import
print("\n--- Testing legacy import (mp.solutions) ---")
try:
    mp_solutions_pose = mp.solutions.pose
    print(f"✅ mp.solutions.pose imported")
    
    if hasattr(mp_solutions_pose, 'Pose'):
        print(f"✅ mp.solutions.pose.Pose exists")
    else:
        print(f"❌ mp.solutions.pose.Pose does not exist")
        
except (ImportError, AttributeError) as e:
    print(f"❌ Legacy import failed: {e}")

print("\n" + "=" * 60)
print("Diagnosis complete!")
print("=" * 60)
