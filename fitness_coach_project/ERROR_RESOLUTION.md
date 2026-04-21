# 🐛 Error Resolution & Setup Guide

## Problem: AttributeError with MediaPipe

### What You're Seeing

```
AttributeError: This app has encountered an error.
Traceback:
  File "...streamlit_pose_helper.py", line 22, in <module>
    mp_pose = mp.solutions.pose
    ^^^^^^^^^^^^
```

### Root Causes

1. **MediaPipe not installed** - Package missing from environment
2. **Wrong version** - Old MediaPipe version incompatible
3. **Import conflict** - Multiple Python environments
4. **Corrupted installation** - Incomplete or broken install

---

## Solution: 3-Step Fix

### Step 1: Run Diagnostic

```bash
python diagnose.py
```

This tells you exactly what's wrong. Look for:

- ❌ mediapipe: if this fails, media pipe isn't working
- ❌ files: if this fails, files are in wrong location

### Step 2: Fix the Issue

**If MediaPipe is missing:**

```bash
pip install mediapipe
```

**If MediaPipe is broken:**

```bash
pip uninstall mediapipe -y
pip install --upgrade mediapipe
```

**If everything is broken:**

```bash
pip install -r requirements.txt --upgrade --force-reinstall
```

### Step 3: Verify Fix

```bash
python diagnose.py
```

Should show: ✅ All checks should pass

---

## Using Sample Data

You already have sample images and videos! They're in `pose_captures/`:

**Sample Images:**

```
Squat.jpg
Squat1.jpg, Squat2.jpg, Squat3.jpg, Squat4.jpg
Push-up.jpg, Push-up1.jpg
Lunge (functional lower body).jpg
Plank (isometric core).jpg, Plank (isometric core)1.jpg, Plank (isometric core)2.jpg
Shoulder press (upper body).jpg, Shoulder press (upper body)1.jpg, Shoulder press (upper body)2.jpg
squat-jump-squat-178-1653334247.jpg
```

**Sample Videos:**

```
Squat.mp4 (shows squat exercise)
Lunge.mp4 (shows lunge exercise)
plank.mp4 (shows plank exercise)
Push Ups!.mp4 (shows push-up exercise)
Squats.mp4 (shows squat exercise)
```

**How to Use:**

1. Run app: `python run_app.py`
2. Select exercise (e.g., "Squat")
3. Choose input type (e.g., "📷 Image")
4. Upload from `pose_captures/` folder
5. Click analyze
6. See feedback!

---

## "No Exercise" Handling

### What Happens When Exercise Not Detected

When the system can't recognize the exercise, it will show:

```
❌ No exercise detected. Position yourself in the frame.
```

**This means:**

1. Person not in frame
2. Body not fully visible
3. Exercise is ambiguous
4. Lighting is too poor

### How to Fix "No Exercise"

✅ **Ensure Full Body Visible**

- Head to feet in frame
- Arms clearly visible
- Legs fully visible
- Good distance from camera

✅ **Improve Lighting**

- Natural light is best
- Avoid shadows on body
- Position with light behind camera
- Avoid backlighting

✅ **Clear Exercise Position**

- Start/end position of exercise
- Avoid mid-motion frames
- Clear arm/leg position
- Upright posture

✅ **Try a Sample First**

- Use `pose_captures/Squat.jpg` as test
- If app works with samples, it's the input quality
- If app fails with samples, it's a setup issue

---

## Testing the App

### Test 1: Verify Installation

```bash
python diagnose.py
```

**Expected:** All ✅

### Test 2: Test with Sample Image

1. Run: `python run_app.py`
2. Select: "Squat" exercise
3. Choose: "📷 Image"
4. Upload: `pose_captures/Squat.jpg`
5. Click: "Analyze Posture"
6. Should see: Pose detection ✅ and feedback

### Test 3: Test with Sample Video

1. Select: "Squat" exercise
2. Choose: "🎥 Video"
3. Upload: `pose_captures/Squats.mp4`
4. Click: "Analyze Video"
5. Should see: Progress bar, metrics, and reps counted

### Test 4: Test Detection Logic

If sample image shows "No Exercise":

1. Check if MediaPipe is detecting pose (should show skeleton)
2. Check if image quality is good
3. Try different sample image
4. Check browser console for errors

---

## Common Issues & Fixes

### Issue 1: "ModuleNotFoundError: mediapipe"

**Cause:** MediaPipe not installed
**Fix:**

```bash
pip install mediapipe
```

### Issue 2: "AttributeError: mp.solutions.pose"

**Cause:** Wrong MediaPipe version
**Fix:**

```bash
pip uninstall mediapipe -y
pip install --upgrade mediapipe
```

### Issue 3: "AttributeError: module 'streamlit' has no attribute..."

**Cause:** Wrong Streamlit version
**Fix:**

```bash
pip install --upgrade streamlit
```

### Issue 4: App shows "No pose detected" on all images

**Cause:** MediaPipe not initialized correctly
**Fixes:**

1. Restart Python/Streamlit
2. Reinstall MediaPipe
3. Check image quality
4. Try sample image from `pose_captures/`

### Issue 5: "Port 8501 already in use"

**Cause:** Another app using same port
**Fix:**

```bash
streamlit run streamlit_app.py --server.port 8502
```

### Issue 6: Video processing very slow

**Cause:** Processing intensive operation
**Solution:**

- Use shorter videos
- Close other applications
- Use lower resolution
- Wait longer for processing

---

## Step-by-Step Setup Process

### 1. Navigate to Project

```bash
cd "c:\Users\USER\Documents\Niyi Analysis\fitness_coach_project\fitness_coach_project"
```

### 2. Check Python Version

```bash
python --version
# Should show 3.8 or higher
```

### 3. Run Fix Script

**Windows:**

```bash
fix.bat
```

**Mac/Linux:**

```bash
bash fix.sh
```

Or manually:

```bash
pip install -r requirements.txt --upgrade
```

### 4. Verify Setup

```bash
python diagnose.py
```

**Expected output:**

```
python           : ✅ PASS
packages         : ✅ PASS
mediapipe        : ✅ PASS
files            : ✅ PASS
streamlit        : ✅ PASS

All checks passed! You can run the app with:
  python run_app.py
```

### 5. Run Application

```bash
python run_app.py
```

Browser should open automatically at `http://localhost:8501`

### 6. Test with Sample

- Select "Squat" exercise
- Choose "📷 Image"
- Upload `pose_captures/Squat.jpg`
- Click "Analyze Posture"
- See pose detection and feedback

---

## Environment Check

To see which Python is being used:

```bash
python -c "import sys; print(sys.executable)"
```

Should print something like:

```
C:\Users\USER\AppData\Local\Programs\Python\Python310\python.exe
```

NOT:

```
C:\Users\USER\Documents\...\\.venv\Scripts\python.exe
```

(Unless you intentionally set up a virtual environment)

---

## Still Having Issues?

### Debug Steps

**1. Enable verbose logging:**

```bash
streamlit run streamlit_app.py --logger.level=debug
```

**2. Check MediaPipe directly:**

```bash
python -c "import mediapipe as mp; print(mp.__version__)"
```

**3. Test pose detection directly:**

```bash
python -c "from mediapipe import solutions; print(solutions.pose)"
```

**4. Check file permissions:**

```bash
# Make sure all files are readable
ls -la streamlit_app.py
ls -la src/
```

**5. Check requirements:**

```bash
pip list | grep -E "mediapipe|streamlit|opencv|numpy"
```

---

## Reference: File Locations

```
fitness_coach_project/
├── streamlit_app.py          ← Main app
├── diagnose.py               ← Diagnostic tool
├── fix.bat                   ← Fix script (Windows)
├── fix.sh                    ← Fix script (Mac/Linux)
├── requirements.txt          ← Dependencies
├── src/
│   ├── streamlit_pose_helper.py
│   ├── streamlit_video_processor.py
│   └── utils.py
└── pose_captures/            ← Sample images/videos
    ├── Squat.jpg
    ├── Squats.mp4
    ├── Push-up.jpg
    ├── Push Ups!.mp4
    └── ... more samples
```

---

## Success Checklist

Before reporting an issue, verify:

- [ ] Python 3.8+ installed (`python --version`)
- [ ] All packages installed (`pip install -r requirements.txt`)
- [ ] MediaPipe working (`python diagnose.py` shows ✅)
- [ ] Files in correct location (run from project root)
- [ ] Sample image can be analyzed (`Squat.jpg`)
- [ ] No errors in browser console
- [ ] App running on correct port (8501 default)

---

## Quick Commands Reference

```bash
# Check setup
python diagnose.py

# Fix everything
# Windows: fix.bat
# Mac/Linux: bash fix.sh

# Start app
python run_app.py

# Use different port
streamlit run streamlit_app.py --server.port 8502

# Test imports
python -c "import mediapipe as mp; print(mp.__version__)"

# Install fresh
pip install -r requirements.txt --force-reinstall
```

---

**Problems resolved? Enjoy your Fitness Coach AI! 🏋️**

For more help, see:

- `QUICK_START.md` - Quick setup
- `STREAMLIT_APP_GUIDE.md` - User guide
- `SETUP_COMPLETE.md` - Full deployment
