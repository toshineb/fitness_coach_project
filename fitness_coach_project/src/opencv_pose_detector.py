#!/usr/bin/env python
"""OpenCV-based pose detection as a fallback for MediaPipe."""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import urllib.request
import os

# OpenPose model URLs (from OpenCV's model zoo)
OPENPOSE_PROTO_URL = "https://raw.githubusercontent.com/CMU-Perceptual-Computing-Lab/openpose/master/models/openpose/coco/openpose.prototxt"
OPENPOSE_WEIGHTS_URL = "https://download.01.org/opencv/openpose/openpose_coco.caffemodel"

MODEL_DIR = "models"
PROTO_PATH = os.path.join(MODEL_DIR, "openpose.prototxt")
WEIGHTS_PATH = os.path.join(MODEL_DIR, "openpose_coco.caffemodel")


def download_model_files():
    """Download OpenPose model files if they don't exist."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Download prototxt
    if not os.path.exists(PROTO_PATH):
        print(f"Downloading {OPENPOSE_PROTO_URL}...")
        try:
            urllib.request.urlretrieve(OPENPOSE_PROTO_URL, PROTO_PATH)
            print(f"✅ Downloaded proto")
        except Exception as e:
            print(f"❌ Failed to download proto: {e}")
            return False
    
    # Download weights (large file ~200MB)
    if not os.path.exists(WEIGHTS_PATH):
        print(f"Downloading {OPENPOSE_WEIGHTS_URL}...")
        print("⏳ This is a large file (~200MB), please wait...")
        try:
            urllib.request.urlretrieve(OPENPOSE_WEIGHTS_URL, WEIGHTS_PATH)
            print(f"✅ Downloaded weights")
        except Exception as e:
            print(f"❌ Failed to download weights: {e}")
            return False
    
    return True


def create_pose_detector():
    """Create an OpenCV-based pose detector."""
    if not download_model_files():
        return None
    
    try:
        net = cv2.dnn.readNetFromCaffe(PROTO_PATH, WEIGHTS_PATH)
        return net
    except Exception as e:
        print(f"Error creating pose detector: {e}")
        return None


def detect_pose(net, image: np.ndarray) -> Tuple[Optional[List], np.ndarray]:
    """Detect pose in an image using OpenCV DNN."""
    if net is None:
        return None, image
    
    h, w = image.shape[:2]
    
    # Prepare blob for network
    blob = cv2.dnn.blobFromImage(
        image, 1.0 / 255, (368, 368),
        [0, 0, 0], swapRB=False, crop=False
    )
    
    net.setInput(blob)
    out = net.forward()
    
    # Parse output to find key points
    h_out = out.shape[2]
    w_out = out.shape[3]
    
    # 25 points for COCO dataset
    points = []
    
    for i in range(25):
        # confidence map
        heatmap = out[0, i, :, :]
        
        # find the position of maximum confidence
        _, conf, _, point = cv2.minMaxLoc(heatmap)
        
        x = int((point[0] * w) / w_out)
        y = int((point[1] * h) / h_out)
        
        if conf > 0.1:
            points.append((x, y, conf))
        else:
            points.append((0, 0, 0))
    
    return points, image


if __name__ == "__main__":
    print("Checking OpenCV pose detection capabilities...")
    
    # Try to download models
    success = download_model_files()
    if success:
        print("✅ Models ready for use")
    else:
        print("❌ Could not set up models")
