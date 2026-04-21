"""
Project Setup Validation and Optimization
Checks all components and provides setup instructions.
"""

import os
import sys
import subprocess
from pathlib import Path
import json

def check_python_version():
    """Verify Python version."""
    version = sys.version_info
    print(f"\n✓ Python {version.major}.{version.minor}.{version.micro}")
    return version.major >= 3 and version.minor >= 8

def check_dependencies():
    """Check installed packages."""
    required = {
        'numpy': 'Array operations',
        'pandas': 'Data processing',
        'sklearn': 'Machine learning',
        'opencv': 'Computer vision (cv2)',
        'joblib': 'Model persistence',
        'matplotlib': 'Visualization',
        'mediapipe': 'Pose detection (optional)',
    }
    
    missing = []
    for package, description in required.items():
        try:
            if package == 'opencv':
                import cv2
            elif package == 'sklearn':
                import sklearn
            elif package == 'mediapipe':
                import mediapipe
            else:
                __import__(package)
            print(f"  ✓ {package:15s} - {description}")
        except ImportError:
            print(f"  ✗ {package:15s} - {description} (MISSING)")
            missing.append(package)
    
    return missing

def check_project_structure():
    """Verify project folders and key files."""
    base_path = Path('.')
    required_dirs = ['src', 'data', 'results', 'models']
    required_files = {
        'requirements.txt': 'Dependency specification',
        'README.md': 'Documentation',
        'data/exercise_angles_preprocessed.csv': 'Training data',
        'results/baseline_run/model.joblib': 'Trained model',
        'src/utils.py': 'Utility functions',
        'src/train_exercise_classifier.py': 'Training script',
        'src/realtime_pose_coach.py': 'Real-time coach',
    }
    
    print("\n📁 PROJECT STRUCTURE:")
    
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        status = "✓" if dir_path.exists() else "✗"
        print(f"  {status} {dir_name}/")
    
    print("\n📄 KEY FILES:")
    for file_path, description in required_files.items():
        path = base_path / file_path
        status = "✓" if path.exists() else "✗"
        print(f"  {status} {file_path:40s} - {description}")
    
    return all((base_path / fp.split('/')[0]).exists() for fp in required_files.keys())

def check_model_performance():
    """Check trained model metrics."""
    model_summary = Path('results/baseline_run/run_summary.json')
    
    if not model_summary.exists():
        print("\n⚠ Model summary not found")
        return False
    
    try:
        with open(model_summary) as f:
            data = json.load(f)
        
        print("\n🤖 MODEL PERFORMANCE:")
        print(f"  Model Type: {data.get('model_name', 'Unknown')}")
        print(f"  Training Samples: {data.get('rows', 'Unknown'):,}")
        
        val = data.get('validation', {})
        test = data.get('test', {})
        
        print(f"\n  Validation Metrics:")
        print(f"    Accuracy: {val.get('accuracy', 0)*100:.2f}%")
        print(f"    Balanced Accuracy: {val.get('balanced_accuracy', 0)*100:.2f}%")
        print(f"    Macro F1: {val.get('macro_f1', 0)*100:.2f}%")
        
        print(f"\n  Test Metrics:")
        print(f"    Accuracy: {test.get('accuracy', 0)*100:.2f}%")
        print(f"    Balanced Accuracy: {test.get('balanced_accuracy', 0)*100:.2f}%")
        print(f"    Macro F1: {test.get('macro_f1', 0)*100:.2f}%")
        
        classes = data.get('class_counts', {})
        print(f"\n  Exercise Classes ({len(classes)} total):")
        for exercise, count in sorted(classes.items(), key=lambda x: x[1], reverse=True):
            print(f"    • {exercise:20s}: {count:5d} samples")
        
        return True
    except Exception as e:
        print(f"✗ Error reading model summary: {e}")
        return False

def check_src_scripts():
    """Verify all source scripts exist and are valid."""
    src_path = Path('src')
    scripts = [
        'utils.py',
        'train_exercise_classifier.py',
        'evaluate_saved_model.py',
        'realtime_pose_coach.py',
        'pose_capture_visualization.py',
        'simple_pose_visualization.py',
        'advanced_pose_capture.py',
        'pose_evaluation_system.py',
    ]
    
    print("\n📜 AVAILABLE SCRIPTS:")
    for script in scripts:
        path = src_path / script
        status = "✓" if path.exists() else "○"
        print(f"  {status} {script}")

def generate_quick_start():
    """Generate quick start guide."""
    guide = """
╔═══════════════════════════════════════════════════════════════╗
║           QUICK START GUIDE - POSE EVALUATION SYSTEM          ║
╚═══════════════════════════════════════════════════════════════╝

📊 PROJECT OVERVIEW
═══════════════════════════════════════════════════════════════

Your fitness coach project includes:
  • 6 exercise classes (Push Ups, Squats, Pull ups, etc.)
  • 37,033 annotated samples with joint angles
  • 96.9% accurate Random Forest classifier
  • Real-time pose detection with MediaPipe
  • Form accuracy evaluation

═══════════════════════════════════════════════════════════════
🎯 MAIN WORKFLOWS
═══════════════════════════════════════════════════════════════

1️⃣  REAL-TIME POSE EVALUATION (Recommended)
   ─────────────────────────────────────
   Command:
     python src/pose_evaluation_system.py
   
   Features:
     • Captures your pose in real-time
     • Classifies exercise with 96.9% accuracy
     • Evaluates form quality (0-100%)
     • Provides corrective feedback
     • Records session data to CSV
   
   Controls:
     c - Capture and evaluate pose
     r - Start/stop recording session
     s - Save current frame
     q - Quit
   
   Output:
     • evaluation_reports/ - Form analysis reports
     • pose_captures/ - Saved screenshots
     • pose_data/ - Session CSV files


2️⃣  SIMPLE POSE VISUALIZATION
   ────────────────────────────
   Command:
     python src/simple_pose_visualization.py
   
   Features:
     • Silhouette-based pose detection
     • No external model downloads needed
     • Multiple visualization modes (edge, contour, background)
     • Good for testing camera setup
   
   Controls:
     e - Edge detection mode
     c - Contour mode
     b - Background subtraction
     s - Save frame
     q - Quit


3️⃣  ADVANCED POSE CAPTURE WITH ANGLES
   ───────────────────────────────────
   Command:
     python src/advanced_pose_capture.py
   
   Features:
     • Extracts all joint angles
     • Calculates shoulder, elbow, hip, knee angles
     • Records angle data to CSV for training
     • Real-time angle display
   
   Controls:
     r - Start/stop recording
     s - Save frame
     p - Toggle skeleton
     a - Toggle angles
     q - Quit


4️⃣  REAL-TIME FITNESS COACH
   ────────────────────────
   Command (with model):
     python src/realtime_pose_coach.py --model_path results/baseline_run/model.joblib
   
   Features:
     • Real-time exercise classification
     • Rule-based corrective feedback
     • Performance metrics (FPS, latency)
     • Session logging


═══════════════════════════════════════════════════════════════
🔧 TRAINING & EVALUATION
═══════════════════════════════════════════════════════════════

Train New Model:
  python src/train_exercise_classifier.py \\
    --csv data/exercise_angles_preprocessed.csv \\
    --output_dir results/my_model

Evaluate Model:
  python src/evaluate_saved_model.py \\
    --model_path results/baseline_run/model.joblib \\
    --test_path results/baseline_run/test_split.csv


═══════════════════════════════════════════════════════════════
📊 UNDERSTANDING YOUR MODEL
═══════════════════════════════════════════════════════════════

Model Type: Random Forest Classifier
Accuracy: 96.9% on test set

Features Used (10 angles + side):
  • Shoulder_Angle
  • Elbow_Angle
  • Hip_Angle
  • Knee_Angle
  • Ankle_Angle
  • Shoulder_Ground_Angle
  • Elbow_Ground_Angle
  • Hip_Ground_Angle
  • Knee_Ground_Angle
  • Ankle_Ground_Angle
  • Side_is_left (1 for left, 0 for right)

Exercises Classified:
  1. Push Ups (9,764 samples)
  2. Pull ups (6,659 samples)
  3. No Exercise (6,000 samples)
  4. Jumping Jacks (5,209 samples)
  5. Squats (4,997 samples)
  6. Russian twists (4,404 samples)


═══════════════════════════════════════════════════════════════
💡 FORM ACCURACY EVALUATION
═══════════════════════════════════════════════════════════════

The system evaluates form by:
  1. Comparing detected angles to exercise standards
  2. Checking if angles are within acceptable ranges
  3. Scoring 0-100% based on deviation
  4. Providing specific corrective feedback

Form Score Interpretation:
  ✓ 80-100% - Excellent form
  ◐ 60-80%  - Good form, minor adjustments needed
  ✗ 0-60%   - Needs improvement, follow feedback


═══════════════════════════════════════════════════════════════
📁 OUTPUT FILES
═══════════════════════════════════════════════════════════════

After running pose_evaluation_system.py:

pose_captures/
  └─ pose_YYYYMMDD_HHMMSS.png    - Captured frames with skeleton

evaluation_reports/
  └─ report_YYYYMMDD_HHMMSS.txt  - Detailed form analysis

pose_data/
  └─ session_YYYYMMDD_HHMMSS.csv - Recorded angle data


═══════════════════════════════════════════════════════════════
🚀 GETTING STARTED
═══════════════════════════════════════════════════════════════

1. Start the pose evaluation system:
   $ python src/pose_evaluation_system.py

2. In the camera window:
   • Move in front of the camera
   • Perform an exercise (squat, push-up, etc.)
   • Press 'c' to capture and evaluate
   • Check the console for detailed feedback

3. Optional: Record a session by pressing 'r'
   • Data saved to pose_data/session_*.csv
   • Use for further analysis or retraining


═══════════════════════════════════════════════════════════════
🐛 TROUBLESHOOTING
═══════════════════════════════════════════════════════════════

Camera Not Detected:
  → Check camera permissions
  → Try: python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"

MediaPipe Import Error:
  → Run: pip install --upgrade mediapipe
  → Use simple_pose_visualization.py as fallback

No Pose Detected:
  → Ensure good lighting
  → Position yourself in frame center
  → Try adjusting camera angle
  → Use pose_capture_visualization.py for debugging

Model Not Found:
  → Verify results/baseline_run/model.joblib exists
  → Or train new model: python src/train_exercise_classifier.py


═══════════════════════════════════════════════════════════════
📚 ADDITIONAL RESOURCES
═══════════════════════════════════════════════════════════════

Project Structure:
  src/                  - All Python scripts
  data/                 - Training datasets
  models/               - Model files
  results/              - Training results & metrics
  pose_captures/        - Saved frames
  pose_data/            - Session recordings
  evaluation_reports/   - Form analysis reports

Key Files:
  requirements.txt      - Python dependencies
  README.md             - Full documentation


═══════════════════════════════════════════════════════════════
✨ NEXT STEPS
═══════════════════════════════════════════════════════════════

→ Run pose_evaluation_system.py to see everything in action
→ Record a few sessions to understand angle patterns
→ Collect more data for specific exercises to improve accuracy
→ Fine-tune form standards in pose_evaluation_system.py
→ Train new models with expanded datasets

═══════════════════════════════════════════════════════════════
"""
    return guide

def main():
    print("\n" + "=" * 65)
    print("🔍 FITNESS COACH PROJECT - SETUP VALIDATION & OPTIMIZATION")
    print("=" * 65)
    
    # Check Python version
    print("\n🐍 PYTHON VERSION:")
    check_python_version()
    
    # Check dependencies
    print("\n📦 DEPENDENCIES:")
    missing = check_dependencies()
    
    if missing:
        print(f"\n⚠  Missing packages: {', '.join(missing)}")
        print("  Install with: pip install -r requirements.txt")
    
    # Check project structure
    check_project_structure()
    
    # Check model
    check_model_performance()
    
    # Check scripts
    check_src_scripts()
    
    # Print quick start guide
    guide = generate_quick_start()
    print(guide)
    
    print("\n" + "=" * 65)
    print("✓ VALIDATION COMPLETE")
    print("=" * 65)
    print("\n🎯 NEXT: Run 'python src/pose_evaluation_system.py' to start!\n")

if __name__ == "__main__":
    main()
