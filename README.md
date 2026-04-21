# Fitness Coach Research Codebase

This project was prepared for a dissertation on fitness coaching using computer vision, angle features, exercise classification, and rule-based corrective feedback.

## What this code can do now

- train and evaluate a supervised exercise classifier on the CSV;
- generate confusion matrices, metrics, and feature importance;
- run a real-time MediaPipe-based pose pipeline from webcam;
- calculate biomechanical angles in real time;
- produce rule-based feedback for common exercises;
- log FPS and latency;
- save session outputs for later analysis.

## What you still need for the full dissertation

To fully satisfy the proposal objectives, add at least one dataset or annotation set that includes:

- the five target exercises: squat, push-up, lunge, shoulder press, plank;
- correct/incorrect or error-type labels;
- ideally subject or video IDs for leakage-safe splitting.

## Project structure

- `src/train_exercise_classifier.py` — trains a tabular angle-feature classifier on the provided CSV.
- `src/evaluate_saved_model.py` — reloads a saved model and evaluates on the test split.
- `src/realtime_pose_coach.py` — real-time webcam pipeline using MediaPipe + OpenCV + rule-based feedback.
- `src/utils.py` — helper functions for angles, metrics, plotting, and label handling.
- `requirements.txt` — Python packages.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 1) Train the classifier on the provided CSV

```bash
python src/train_exercise_classifier.py \
  --csv /mnt/data/exercise_angles_preprocessed.csv \
  --output_dir results/baseline_run
```

### 2) Evaluate the saved model

```bash
python src/evaluate_saved_model.py \
  --model_path results/baseline_run/model.joblib \
  --test_path results/baseline_run/test_split.csv \
  --output_dir results/baseline_eval
```

### 3) Run the real-time pose coach

```bash
python src/realtime_pose_coach.py \
  --model_path results/baseline_run/model.joblib \
  --camera 0 \
  --save_session true
```

### Objective I

Use `realtime_pose_coach.py` to benchmark webcam FPS, latency, and landmark availability.

### Objective II

Use `train_exercise_classifier.py` to report accuracy, macro-F1, balanced accuracy, and confusion matrix.

### Objective III

Use the rule engine in `realtime_pose_coach.py` to validate interpretable feedback against biomechanical thresholds.

### Objective IV

Use the end-to-end pipeline and exported session logs to report integrated performance.

streamlit run "c:/Users/USER/Documents/Analysis/fitness_coach_project/fitness_coach_project/streamlit_app.py"


python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt