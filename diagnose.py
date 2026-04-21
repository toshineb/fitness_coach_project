"""
Diagnostic and Fix Script for Fitness Coach AI Streamlit App
Helps identify and resolve common setup issues
"""

import sys
import os


def check_python_version():
    """Check if Python version is compatible."""
    print("\n" + "="*60)
    print("CHECKING PYTHON VERSION")
    print("="*60)
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ ERROR: Python 3.8+ required")
        return False
    print("✅ Python version is compatible")
    return True


def check_required_packages():
    """Check if all required packages are installed."""
    print("\n" + "="*60)
    print("CHECKING REQUIRED PACKAGES")
    print("="*60)
    
    packages = {
        'numpy': 'Data handling',
        'pandas': 'Data frames',
        'opencv-python': 'cv2 - Image processing',
        'scikit-learn': 'ML models',
        'matplotlib': 'Plotting',
        'mediapipe': 'MediaPipe - Pose detection',
        'streamlit': 'Streamlit - Web app',
        'Pillow': 'Image handling',
    }
    
    missing = []
    for package, description in packages.items():
        try:
            if package == 'opencv-python':
                import cv2
                print(f"✅ {package}: {cv2.__version__} - {description}")
            elif package == 'Pillow':
                import PIL
                print(f"✅ {package}: {PIL.__version__} - {description}")
            elif package == 'scikit-learn':
                import sklearn
                print(f"✅ {package}: {sklearn.__version__} - {description}")
            else:
                mod = __import__(package.replace('-', '_'))
                version = getattr(mod, '__version__', 'unknown')
                print(f"✅ {package}: {version} - {description}")
        except ImportError:
            print(f"❌ {package}: NOT INSTALLED - {description}")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print(f"\nTo install, run:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    print("\n✅ All required packages are installed")
    return True


def check_mediapipe_detailed():
    """Check MediaPipe specifically and try different import methods."""
    print("\n" + "="*60)
    print("CHECKING MEDIAPIPE IN DETAIL")
    print("="*60)
    
    try:
        import mediapipe
        print(f"✅ mediapipe version: {mediapipe.__version__}")
        
        # Try the modern import method
        try:
            from mediapipe import solutions
            print("✅ New import method (from mediapipe import solutions) works")
            
            mp_pose = solutions.pose
            print(f"✅ solutions.pose available: {mp_pose}")
            
            mp_drawing = solutions.drawing_utils
            print(f"✅ solutions.drawing_utils available: {mp_drawing}")
            
            return True
        except ImportError as e:
            print(f"⚠️  New import method failed: {e}")
            
            # Try the old import method
            try:
                mp_pose = mediapipe.solutions.pose
                print(f"✅ Old import method (mp.solutions.pose) works: {mp_pose}")
                return True
            except (ImportError, AttributeError) as e:
                print(f"❌ Old import method also failed: {e}")
                return False
    
    except ImportError as e:
        print(f"❌ MediaPipe not installed: {e}")
        return False


def check_files_exist():
    """Check if essential project files exist."""
    print("\n" + "="*60)
    print("CHECKING PROJECT FILES")
    print("="*60)
    
    files_to_check = [
        'streamlit_app.py',
        'run_app.py',
        'requirements.txt',
        'src/streamlit_pose_helper.py',
        'src/streamlit_video_processor.py',
        'src/utils.py',
        '.streamlit/config.toml',
    ]
    
    all_exist = True
    for file in files_to_check:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} ({size} bytes)")
        else:
            print(f"❌ {file} - NOT FOUND")
            all_exist = False
    
    # Check for sample data
    print("\nSample Data:")
    sample_dirs = ['pose_captures', 'data', 'results']
    for dir_name in sample_dirs:
        if os.path.isdir(dir_name):
            file_count = len([f for f in os.listdir(dir_name) if os.path.isfile(os.path.join(dir_name, f))])
            print(f"✅ {dir_name}/ ({file_count} files)")
        else:
            print(f"⚠️  {dir_name}/ - not found")
    
    return all_exist


def test_streamlit_import():
    """Test if Streamlit can be imported and basic functionality works."""
    print("\n" + "="*60)
    print("TESTING STREAMLIT IMPORT")
    print("="*60)
    
    try:
        import streamlit as st
        print(f"✅ Streamlit version: {st.__version__}")
        print("✅ Streamlit is ready to use")
        return True
    except ImportError as e:
        print(f"❌ Cannot import Streamlit: {e}")
        print("\nTo fix, run:")
        print("  pip install streamlit")
        return False


def recommend_fixes(checks):
    """Recommend fixes based on failed checks."""
    print("\n" + "="*60)
    print("RECOMMENDED ACTIONS")
    print("="*60)
    
    all_passed = all(checks.values())
    
    if all_passed:
        print("✅ All checks passed! You can run the app with:")
        print("  python run_app.py")
        return True
    
    print("\nTo fix the issues, try these steps:\n")
    
    if not checks.get('python', False):
        print("1. Install Python 3.8 or higher")
        print("   https://www.python.org/downloads/")
    
    if not checks.get('packages', False):
        print("2. Install required packages:")
        print("   pip install -r requirements.txt")
    
    if not checks.get('mediapipe', False):
        print("3. Fix MediaPipe installation:")
        print("   pip uninstall mediapipe -y")
        print("   pip install --upgrade mediapipe")
    
    if not checks.get('streamlit', False):
        print("4. Install Streamlit:")
        print("   pip install streamlit")
    
    if not checks.get('files', False):
        print("5. Check that you're in the correct directory:")
        print("   cd 'c:\\Users\\USER\\Documents\\Niyi Analysis\\fitness_coach_project\\fitness_coach_project'")
    
    print("\nAfter fixing issues, run:")
    print("  python diagnose.py  (to re-check)")
    print("  python run_app.py   (to start the app)")
    
    return False


def main():
    """Run all diagnostic checks."""
    print("\n" + "="*60)
    print("FITNESS COACH AI - DIAGNOSTIC TOOL")
    print("="*60)
    print("Checking your system setup for Streamlit app compatibility\n")
    
    checks = {
        'python': check_python_version(),
        'packages': check_required_packages(),
        'mediapipe': check_mediapipe_detailed(),
        'files': check_files_exist(),
        'streamlit': test_streamlit_import(),
    }
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for check_name, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name:15} : {status}")
    
    # Recommend actions
    success = recommend_fixes(checks)
    
    print("\n" + "="*60)
    if success:
        print("✅ READY TO RUN")
    else:
        print("❌ NEEDS FIXES")
    print("="*60 + "\n")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
