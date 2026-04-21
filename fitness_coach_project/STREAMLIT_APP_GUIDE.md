# 🏋️ Fitness Coach AI - Web Application Guide

## Overview

The Fitness Coach AI is a web-based application built with **Streamlit** that provides real-time AI-powered exercise form correction using computer vision and deep learning. It analyzes your exercise form and provides instant feedback to help you maintain proper posture.

## Features

✅ **Real-Time Posture Analysis**

- AI-powered body pose detection using MediaPipe
- Analyzes 10+ biomechanical joint angles
- Instant form assessment

✅ **Multiple Input Sources**

- 📷 Image upload and analysis
- 🎥 Video file processing with frame-by-frame analysis
- 📹 Real-time webcam analysis (where supported)

✅ **Supported Exercises**

- Squat
- Lunge
- Push-up
- Deadlift
- Bicep Curl

✅ **Detailed Feedback**

- Specific form corrections
- Form accuracy percentage
- Repetition counting for video analysis
- Detailed joint angle measurements

✅ **Performance Metrics**

- Processing speed
- Confidence scores
- Form accuracy
- Repetition statistics

## Installation

### 1. Install Dependencies

```bash
# Navigate to the project directory
cd fitness_coach_project

# Install required packages
pip install -r requirements.txt
```

### 2. (Optional) Train a Model

```bash
# If you have a CSV with exercise data
python src/train_exercise_classifier.py \
  --csv data/exercise_angles_preprocessed.csv \
  --output_dir results/baseline_run
```

## Running the Application

### Quick Start

```bash
# Option 1: Using the launcher script
python run_app.py

# Option 2: Direct streamlit command
streamlit run streamlit_app.py
```

The application will open automatically in your default browser at `http://localhost:8501`

### Command Line Options

```bash
# Run with custom port
streamlit run streamlit_app.py --server.port 8502

# Run in development mode
streamlit run streamlit_app.py --logger.level=debug

# Run headless (no browser auto-open)
streamlit run streamlit_app.py --server.headless true
```

## How to Use

### Step 1: Select Your Exercise

1. In the **sidebar**, select the exercise you want to analyze:
   - Squat
   - Lunge
   - Push-up
   - Deadlift
   - Bicep Curl

### Step 2: Choose Input Source

Select how you want to provide input:

#### 📷 Image Analysis

1. Click **"📷 Image"** in the sidebar
2. Click **"Upload an exercise image"**
3. Select a JPG, PNG, or BMP file from your computer
4. Click **"🔍 Analyze Posture"**
5. View results with:
   - Annotated pose visualization
   - Exercise classification
   - Feedback and corrections
   - Joint angle measurements

#### 🎥 Video Analysis

1. Click **"🎥 Video"** in the sidebar
2. Click **"Upload an exercise video"**
3. Select an MP4, AVI, MOV, or MKV file
4. Click **"🔍 Analyze Video"**
5. Wait for frame-by-frame processing (shows progress)
6. View results with:
   - Overall accuracy metrics
   - Repetition count
   - Exercise detection breakdown
   - Sample frames from analysis
   - Option to download annotated video

#### 📹 Real-Time Webcam

1. Click **"📹 Webcam"** in the sidebar
2. Allow browser camera access when prompted
3. Position yourself in good lighting
4. Perform your exercise
5. Get real-time feedback as you move

### Step 3: View Results

Results display include:

| Metric           | Meaning                                      |
| ---------------- | -------------------------------------------- |
| **Exercise**     | Detected exercise type                       |
| **Confidence**   | Model confidence in prediction (0-100%)      |
| **Feedback**     | Specific form correction suggestions         |
| **Accuracy**     | Percentage of correct form frames (video)    |
| **Repetitions**  | Number of complete reps detected (video)     |
| **Joint Angles** | Individual angle measurements for each joint |

## Tips for Best Results

### General

- ✅ Ensure **full body is visible** in frame
- ✅ Use **good lighting** (natural light is best)
- ✅ Position camera **perpendicular to body**
- ✅ Clear background helps with detection
- ❌ Avoid shadows and backlighting
- ❌ Don't wear loose clothing that obscures body lines

### For Images

- Use clear, well-lit photos
- Show the exercise at a key position (deepest squat, extended push-up, etc.)
- Straight-on angle works best

### For Videos

- Perform smooth, controlled movements
- Complete full range of motion
- Maintain consistent speed for accurate rep counting
- Minimum 30 FPS recommended

### For Webcam

- Test camera focus and lighting first
- Ensure device has good computational power
- Close other applications for better performance
- Position 3-6 feet away from camera

## Understanding Feedback

### Feedback Symbols

- ✅ **Checkmark**: Correct form detected
- 📍 **Pin**: Form correction needed
- ⚠️ **Warning**: Exercise not recognized
- ℹ️ **Info**: General guidance

### Example Feedback Messages

**Squat:**

- ✅ "Perfect squat form!"
- 📍 "Go deeper to reach stronger squat depth."
- 📍 "Keep your chest more upright during the squat."
- 📍 "Avoid collapsing too low at the hips."

**Push-up:**

- ✅ "Perfect push-up form!"
- 📍 "Keep your core braced and maintain a straighter body line."
- 📍 "Lower further for a fuller range of motion."
- 📍 "Do not shrug your shoulders; keep them stable."

**Lunge:**

- ✅ "Perfect lunge form!"
- 📍 "Bend the lead knee more to reach proper depth."
- 📍 "Keep your torso more upright."

**Deadlift:**

- ✅ "Perfect deadlift form!"
- 📍 "Keep your back straighter; maintain neutral spine."
- 📍 "Extend your legs more fully."

**Bicep Curl:**

- ✅ "Perfect curl form!"
- 📍 "Bring the weight higher to complete the range."
- 📍 "Keep your shoulders stable; minimize swinging."

## Understanding Metrics

### Confidence Score

- Higher = More certain the model is about its prediction
- > 80%: High confidence
- 60-80%: Moderate confidence
- <60%: Low confidence (consider adjusting camera angle)

### Accuracy (Video Analysis)

- Percentage of frames with correct form
- 90-100%: Excellent form consistency
- 80-90%: Good form with minor errors
- <80%: Form needs improvement

### Repetition Count

- Automatically counts complete reps
- One rep = full range of motion (up → down → up)
- Only counts if executed with proper form

### Joint Angles

- Measured in degrees (0-180°)
- Different exercises have different optimal angles
- Helps fine-tune form corrections

## Advanced Features

### Export Results

- For video analysis, download the annotated video showing all detections
- Review frame-by-frame to identify form issues

### Batch Processing

For analyzing multiple videos:

```python
# Create a script using the underlying modules
from src.streamlit_video_processor import process_video_file
from src.streamlit_pose_helper import StreamlitPoseCoach

coach = StreamlitPoseCoach()
output_frames, metrics, results = process_video_file(
    "path/to/video.mp4",
    coach,
    "Squat"
)
```

## Troubleshooting

### Issue: "No pose detected"

**Solution:**

- Ensure full body is visible
- Improve lighting
- Move closer to camera
- Adjust camera angle

### Issue: "Wrong exercise detected"

**Solution:**

- Perform exercise with clear, complete movements
- Ensure camera is perpendicular to body
- Avoid ambiguous positions

### Issue: Slow processing

**Solution:**

- Close other applications
- Reduce video resolution
- Use shorter video clips
- Check CPU usage

### Issue: Webcam not working

**Solution:**

- Allow browser camera permissions
- Check browser supports WebRTC
- Try uploading a video instead
- Restart browser

### Issue: Model not loading

**Solution:**

- Train a model: `python src/train_exercise_classifier.py --csv data/exercise_angles_preprocessed.csv --output_dir results/baseline_run`
- Or use heuristic analysis (no trained model needed)

## System Requirements

- **Python:** 3.8 or higher
- **RAM:** 4GB minimum (8GB recommended)
- **Storage:** 500MB free space
- **Browser:** Chrome, Firefox, Safari, or Edge (recent versions)
- **Camera:** For webcam features (optional)

## File Structure

```
fitness_coach_project/
├── streamlit_app.py                  # Main web application
├── run_app.py                        # Application launcher
├── requirements.txt                  # Dependencies
│
├── src/
│   ├── streamlit_pose_helper.py     # Pose detection module
│   ├── streamlit_video_processor.py # Video processing module
│   ├── utils.py                      # Utility functions
│   ├── realtime_pose_coach.py       # Original pose coach
│   └── ... (other original files)
│
├── data/
│   └── exercise_angles_preprocessed.csv  # Training data
│
└── results/
    └── baseline_run/                 # Trained model location
        └── model_bundle.joblib
```

## Performance Tips

1. **Faster Processing:**
   - Use images instead of videos for single-frame analysis
   - Reduce video resolution
   - Close background applications

2. **Better Detection:**
   - Improve lighting
   - Use wider camera angle
   - Wear fitted clothing

3. **Accuracy:**
   - Follow the exercise movement closely
   - Use 30+ FPS video
   - Train model with more diverse data

## Advanced Configuration

### Using Custom Models

If you have your own trained model:

```python
# In streamlit_app.py, modify the load_coach() function
model_bundle = load_model_bundle("path/to/your/model.joblib")
coach = StreamlitPoseCoach(model_bundle)
```

### Customizing Feedback Rules

Edit the `get_feedback()` method in `streamlit_pose_helper.py` to add custom feedback for your exercises.

## Research Integration

This application is designed to support the research objectives:

1. **Objective I:** Real-time pose estimation using MediaPipe ✅
2. **Objective II:** Exercise classification via deep learning ✅
3. **Objective III:** Rule-based feedback engine ✅
4. **Objective IV:** System performance evaluation ✅

All analysis results can be exported for research evaluation.

## Support & Documentation

- **Main Documentation:** See `analysis/README.md`
- **Dataset Info:** See `data/` folder
- **Training Guide:** See `src/train_exercise_classifier.py`
- **Analysis Reports:** See `analysis/` folder

## License & Attribution

This project uses:

- **MediaPipe** (Google) for pose detection
- **Streamlit** for web interface
- **OpenCV** for image processing
- **Scikit-learn** for machine learning

## FAQ

**Q: Can I use this without training a model?**
A: Yes! The heuristic analysis works without a trained model.

**Q: Can I add more exercises?**
A: Yes, edit the EXERCISES list in `streamlit_pose_helper.py` and add feedback rules.

**Q: How accurate is the system?**
A: Accuracy depends on video quality, lighting, and the trained model (90%+ with good training data).

**Q: Can I use this for physical therapy?**
A: Yes, but consult with a professional. This is an educational tool.

**Q: How much data do I need to train?**
A: Start with 50+ images per exercise/form combination for decent accuracy.

---

**Happy training! 🏋️💪**
