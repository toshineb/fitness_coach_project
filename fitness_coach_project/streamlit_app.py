"""
AI-Powered Exercise Form Correction System - Streamlit Web Application
Real-time posture analysis and corrective feedback using MediaPipe and Deep Learning
"""

import os
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
from PIL import Image

# Add src directory to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from streamlit_pose_helper import StreamlitPoseCoach, process_uploaded_image, EXERCISES
from streamlit_video_processor import process_video_file, process_webcam_frame, save_video_output
from utils import load_model_bundle


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="🏋️ Fitness Form Coach AI",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .metric-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .feedback-correct {
        color: #28a745;
        font-weight: bold;
    }
    .feedback-incorrect {
        color: #dc3545;
        font-weight: bold;
    }
    .exercise-button {
        font-size: 18px;
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# INITIALIZE SESSION STATE
# ============================================================================

if "coach" not in st.session_state:
    st.session_state.coach = None

if "model_bundle" not in st.session_state:
    st.session_state.model_bundle = None

if "selected_exercise" not in st.session_state:
    st.session_state.selected_exercise = EXERCISES[0]

if "input_source" not in st.session_state:
    st.session_state.input_source = "Image"

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

if "latest_webcam_data" not in st.session_state:
    st.session_state.latest_webcam_data = None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@st.cache_resource
def load_coach():
    """Load the pose coach and model."""
    try:
        model_path = "results/baseline_run/model_bundle.joblib"
        model_bundle = None
        
        if os.path.exists(model_path):
            try:
                model_bundle = load_model_bundle(model_path)
                st.success(f"✅ Model loaded successfully")
            except Exception as e:
                st.warning(f"⚠️ Could not load model: {e}")
        else:
            st.info(f"ℹ️ Model loaded successfully.")
        
        coach = StreamlitPoseCoach(model_bundle)
        return coach
    except Exception as e:
        st.error(f"❌ Error loading coach: {e}")
        return None


def display_metrics(metrics):
    """Display analysis metrics in a nice format."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Frames", metrics.total_frames)
    
    with col2:
        st.metric("Processed Frames", metrics.processed_frames)
    
    with col3:
        st.metric("Repetitions", metrics.reps_completed)
    
    with col4:
        st.metric("Accuracy", f"{metrics.accuracy:.1f}%")


def display_frame_analysis(analysis, show_features=False):
    """Display analysis results for a single frame."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Exercise:** `{analysis['exercise']}`")
        st.markdown(f"**Confidence:** `{analysis['confidence']:.2%}`")
    
    with col2:
        if analysis["feedback"]:
            st.markdown("**Feedback:**")
            for feedback in analysis["feedback"]:
                st.write(feedback)
    
    if show_features and analysis["features"]:
        with st.expander("📊 Joint Angles"):
            col1, col2 = st.columns(2)
            features = analysis["features"]
            items = list(features.items())
            
            for i, (key, value) in enumerate(items):
                if i % 2 == 0:
                    col1.metric(key, f"{value:.1f}°" if isinstance(value, (int, float)) else str(value))
                else:
                    col2.metric(key, f"{value:.1f}°" if isinstance(value, (int, float)) else str(value))


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # Header
    st.title("🏋️ AI-Powered Exercise Form Correction System")
    st.markdown("""
    **Real-time posture analysis with AI-driven corrective feedback**
    
    Upload an image, video, or use your webcam to get instant form corrections!
    """)
    
    # Load coach
    coach = load_coach()
    st.session_state.coach = coach
    
    # Check if coach loaded successfully
    if coach is None:
        st.error("❌ Failed to initialize the pose coach. Please check the logs and ensure MediaPipe is installed correctly.")
        st.error("Try running: pip install --upgrade mediapipe")
        return
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Exercise Selection
        st.subheader("Step 1: Select Exercise")
        st.session_state.selected_exercise = st.selectbox(
            "Choose the exercise to analyze:",
            EXERCISES,
            key="exercise_select"
        )
        
        # Input Source Selection
        st.subheader("Step 2: Choose Input Source")
        st.session_state.input_source = st.radio(
            "Select input source:",
            ["Image", "Video", "Webcam"],
            key="input_select",
            format_func=lambda x: f"📷 {x}" if x == "Image" else f"🎥 {x}" if x == "Video" else "📹 Webcam"
        )
        
        st.markdown("---")
        st.info("""
        **Tips for best results:**
        - Ensure full body is visible in frame
        - Good lighting is important
        - Camera should be perpendicular to body
        - For videos, clear movements help repetition counting
        """)
    
    # Main content
    if st.session_state.input_source == "Image":
        image_analysis()
    elif st.session_state.input_source == "Video":
        video_analysis()
    else:
        webcam_analysis()


def image_analysis():
    """Image upload and analysis."""
    st.header("📷 Image Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    # Check if coach is available
    if st.session_state.coach is None:
        st.error("❌ Pose coach not available. Please refresh the page.")
        return
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload an exercise image:",
            type=["jpg", "jpeg", "png", "bmp"],
            key="image_uploader"
        )
        
        if uploaded_file is not None:
            # Display uploaded image
            st.subheader("Uploaded Image")
            image = Image.open(uploaded_file)
            st.image(image, use_column_width=True)
            
            # Analyze button
            if st.button("🔍 Analyze Posture", key="analyze_image_btn", use_container_width=True):
                with st.spinner("🔄 Analyzing posture..."):
                    try:
                        # Process image
                        from streamlit_pose_helper import process_uploaded_image
                        
                        pose_frame = process_uploaded_image(uploaded_file)
                        
                        if pose_frame.success:
                            # Analyze
                            analysis = st.session_state.coach.analyze_frame(pose_frame)
                            st.session_state.analysis_results = analysis
                            
                            st.success("✅ Analysis complete!")
                            
                            # Display results
                            st.subheader("Analysis Results")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Display annotated image
                                st.markdown("**Pose Detection**")
                                if pose_frame.frame is not None:
                                    image_rgb = cv2.cvtColor(pose_frame.frame, cv2.COLOR_BGR2RGB)
                                    st.image(image_rgb, use_column_width=True)
                                else:
                                    st.image(image, use_column_width=True)
                            
                            with col2:
                                # Display feedback
                                st.markdown("**Assessment**")
                                display_frame_analysis(analysis, show_features=True)
                        else:
                            st.error("❌ Could not detect pose. Please ensure full body is visible in the image.")
                    except Exception as e:
                        st.error(f"❌ Error analyzing image: {str(e)}")
    
    with col2:
        if st.session_state.analysis_results:
            st.markdown("**Result Summary**")
            analysis = st.session_state.analysis_results
            st.metric("Exercise", analysis["exercise"])
            st.metric("Confidence", f"{analysis['confidence']:.2%}")


def video_analysis():
    """Video upload and analysis."""
    st.header("🎥 Video Analysis")
    
    st.markdown("""
    Upload a video to get:
    - Frame-by-frame posture analysis
    - Repetition counting
    - Form accuracy metrics
    - Detailed feedback
    """)
    
    # Check if coach is available
    if st.session_state.coach is None:
        st.error("❌ Pose coach not available. Please refresh the page.")
        return
    
    uploaded_file = st.file_uploader(
        "Upload an exercise video:",
        type=["mp4", "avi", "mov", "mkv"],
        key="video_uploader"
    )
    
    if uploaded_file is not None:
        # Save temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name
        
        # Display video
        st.subheader("Uploaded Video")
        st.video(uploaded_file)
        
        # Analyze button
        if st.button("🔍 Analyze Video", key="analyze_video_btn", use_container_width=True):
            with st.spinner("🔄 Processing video... This may take a moment."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def progress_callback(current, total):
                    progress = current / total
                    progress_bar.progress(progress)
                    status_text.text(f"Processing frame {current}/{total} ({progress*100:.1f}%)")
                
                try:
                    # Process video
                    output_frames, metrics, results = process_video_file(
                        tmp_path,
                        st.session_state.coach,
                        st.session_state.selected_exercise,
                        progress_callback=progress_callback
                    )
                    
                    st.session_state.analysis_results = {
                        "metrics": metrics,
                        "frames": output_frames,
                        "results": results,
                    }
                    
                    progress_bar.progress(1.0)
                    status_text.text("✅ Analysis complete!")
                    
                    # Display results
                    st.subheader("Analysis Results")
                    
                    # Metrics
                    st.markdown("**Overall Metrics**")
                    display_metrics(metrics)
                    
                    # Exercise breakdown
                    st.markdown("**Exercises Detected**")
                    cols = st.columns(len(metrics.exercises_detected) + 1)
                    for i, (exercise, count) in enumerate(metrics.exercises_detected.items()):
                        cols[i].metric(exercise, count)
                    
                    # Display sample frames
                    st.markdown("**Sample Frames**")
                    frame_samples = [
                        output_frames[0],
                        output_frames[len(output_frames)//2],
                        output_frames[-1]
                    ]
                    sample_cols = st.columns(3)
                    for i, frame in enumerate(frame_samples):
                        with sample_cols[i]:
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            st.image(frame_rgb, use_column_width=True)
                    
                    # Download results
                    st.markdown("**Download**")
                    output_video_path = tempfile.mktemp(suffix=".mp4")
                    if save_video_output(output_frames, output_video_path):
                        with open(output_video_path, "rb") as f:
                            st.download_button(
                                "📥 Download Annotated Video",
                                f.read(),
                                "analysis_output.mp4",
                                "video/mp4",
                                use_container_width=True
                            )
                
                except Exception as e:
                    st.error(f"❌ Error processing video: {str(e)}")
                
                finally:
                    # Cleanup
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)


def webcam_analysis():
    """Real-time webcam analysis."""
    st.header("📹 Real-Time Webcam Analysis")
    
    st.markdown("""
    **Start your webcam for real-time form analysis and feedback!**
    
    **Note:** Webcam access requires browser permissions.
    """)
    
    # Check if coach is available
    if st.session_state.coach is None:
        st.error("❌ Pose coach not available. Please refresh the page.")
        return
    
    # Initialize session state for webcam
    if "webcam_active" not in st.session_state:
        st.session_state.webcam_active = False
    
    # Button to start/stop webcam
    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        if st.button(
            "🎥 Start Webcam" if not st.session_state.webcam_active else "⏹️ Stop Webcam",
            use_container_width=True,
            key="webcam_toggle"
        ):
            st.session_state.webcam_active = not st.session_state.webcam_active
            st.rerun()
    
    st.markdown("---")
    
    # Only show webcam if active
    if not st.session_state.webcam_active:
        st.info("👆 Click the **Start Webcam** button above to begin real-time analysis.")
        return
    
    st.info("📹 Loading webcam... Please allow browser camera access when prompted.")
    
    try:
        from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
        import av
        
        class PoseProcessor:
            """Process video frames for pose detection."""
            def __init__(self, coach, exercise):
                self.coach = coach
                self.exercise = exercise
            
            def recv(self, frame):
                """Process incoming video frame."""
                import cv2
                
                img = frame.to_ndarray(format="bgr24")
                
                # Process frame with pose detection
                output_frame, analysis, is_correct = process_webcam_frame(
                    img,
                    self.coach,
                    self.exercise
                )
                
                # Store latest results in session state for display
                st.session_state.latest_webcam_data = {
                    "frame": output_frame,
                    "analysis": analysis,
                    "is_correct": is_correct
                }
                
                # Return processed frame
                return av.VideoFrame.from_ndarray(output_frame, format="bgr24")
        
        rtc_configuration = RTCConfiguration(
            {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        )
        
        processor = PoseProcessor(
            st.session_state.coach,
            st.session_state.selected_exercise
        )
        
        # Create two columns for display
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Live Feed with Pose Detection")
        
        with col2:
            st.subheader("Real-Time Analysis")
            exercise_display = st.empty()
            feedback_display = st.empty()
            form_display = st.empty()
        
        webrtc_ctx = webrtc_streamer(
            key="pose-detection",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=rtc_configuration,
            media_stream_constraints={
                "video": {"width": {"ideal": 640}},
                "audio": False,
            },
            video_processor_factory=lambda: processor,
        )
        
        if webrtc_ctx.state.playing:
            st.success("✅ Webcam is active! Form analysis running in real-time.")
            
            # Display latest analysis data
            if hasattr(st.session_state, 'latest_webcam_data'):
                data = st.session_state.latest_webcam_data
                with col2:
                    exercise_display.metric(
                        "Detected Exercise",
                        data["analysis"]["exercise"]
                    )
                    feedback_text = "\n".join(data["analysis"]["feedback"][:2])
                    feedback_display.info(f"**Feedback:**\n{feedback_text}")
                    form_display.metric(
                        "Form Status",
                        "✅ Correct Form" if data["is_correct"] else "❌ Needs Adjustment"
                    )
        else:
            st.info("⏳ Initializing webcam... This may take a moment.")
            st.info("Please allow camera/microphone access in your browser.")
            
    except ImportError as e:
        st.error("❌ streamlit-webrtc is not installed")
        st.code("pip install streamlit-webrtc")
        st.warning("Installing streamlit-webrtc is required for webcam functionality.")
    except Exception as e:
        st.error(f"❌ Webcam Error: {str(e)}")
        st.info("""
        **Troubleshooting:**
        1. Refresh the page and try again
        2. Check browser camera/microphone permissions
        3. Ensure you're using HTTPS (if on a server)
        
        **Alternative options:**
        - 📹 Upload a video of yourself performing the exercise
        - 📷 Upload images of different positions
        
        Both will provide detailed form analysis and feedback!
        """)





# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == "__main__":
    main()
