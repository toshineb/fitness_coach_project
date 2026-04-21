"""
Quick launcher script for the Fitness Coach Streamlit application.
Run this script to start the web server.
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Start the Streamlit application."""
    
    # Get the project root directory
    project_root = Path(__file__).parent
    
    # Check if requirements are installed
    try:
        import streamlit
        import cv2
        import mediapipe
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("\n🔧 Installing dependencies...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", 
            str(project_root / "requirements.txt")
        ])
        print("✅ Dependencies installed!")
    
    # Change to project directory
    os.chdir(project_root)
    
    # Start Streamlit app
    print("\n🚀 Starting Fitness Coach AI Web Application...")
    print("💻 Open your browser to: http://localhost:8501\n")
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        str(project_root / "streamlit_app.py"),
        "--logger.level=info"
    ])


if __name__ == "__main__":
    main()
