#!/usr/bin/env python
"""Inspect MediaPipe 0.10.33 structure."""

import mediapipe as mp
print("MediaPipe attributes:")
print(dir(mp))
print()

print("Checking for pose in different locations:")

# Check top level
if hasattr(mp, 'pose'):
    print("✅ mp.pose exists")
    print(f"   Type: {type(mp.pose)}")
    print(f"   Attributes: {dir(mp.pose)[:10]}")
else:
    print("❌ mp.pose does not exist")

print()

# Check all submodules
import pkgutil
print("MediaPipe submodules:")
for importer, modname, ispkg in pkgutil.iter_modules(mp.__path__):
    print(f"  - {modname} (package: {ispkg})")
