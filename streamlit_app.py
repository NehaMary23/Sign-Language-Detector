import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
from pathlib import Path
from collections import deque
import time

st.set_page_config(page_title="Sign Language Detector", layout="wide")
st.title("🤟 Real-Time Sign Language Detection")
st.markdown("Detect sign language gestures from your webcam!")

# Load model
model_path = Path(__file__).parent / "models" / "hand_landmarker.task"

if not model_path.exists():
    st.error(f"❌ Model file not found: {model_path}")
    st.stop()

# Initialize MediaPipe
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

options = vision.HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=str(model_path)),
    running_mode=vision.RunningMode.IMAGE,
    num_hands=2,
    min_hand_detection_confidence=0.65,
)
hand_landmarker = vision.HandLandmarker.create_from_options(options)

# Sidebar
st.sidebar.header("Controls")
clear_btn = st.sidebar.button("🗑️ Clear Output", use_container_width=True)

# Session state
if "output_text" not in st.session_state:
    st.session_state.output_text = ""

if clear_btn:
    st.session_state.output_text = ""

# Main layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📹 Webcam Feed")
    
    # Use Streamlit's camera input (works better on cloud)
    camera_image = st.camera_input("Capture image from webcam")
    
    if camera_image is not None:
        # Convert to OpenCV format
        from PIL import Image
        image = Image.open(camera_image)
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Process with MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        hand_results = hand_landmarker.detect(mp_image)
        
        # Draw landmarks
        if hand_results.hand_landmarks:
            h, w, _ = frame.shape
            for hand_landmarks in hand_results.hand_landmarks:
                for landmark in hand_landmarks:
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    cv2.circle(frame, (x, y), 4, (0, 255, 255), -1)
                
                # Draw connections
                for conn in vision.HandLandmarksConnections.HAND_CONNECTIONS:
                    start = hand_landmarks[conn.start]
                    end = hand_landmarks[conn.end]
                    x1, y1 = int(start.x * w), int(start.y * h)
                    x2, y2 = int(end.x * w), int(end.y * h)
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 180, 255), 2)
        
        # Display processed frame
        st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_container_width=True)

with col2:
    st.subheader("📊 Output")
    st.metric("Detected Text", st.session_state.output_text if st.session_state.output_text else "No gestures detected")
    
    st.subheader("🎯 Supported Signs")
    signs = ["HELLO", "THANK YOU", "YES", "PLEASE", "NO", "GOOD", "I LOVE YOU", "OK", "STOP", "HELP"]
    for sign in signs:
        st.write(f"• {sign}")

st.markdown("---")
st.info("📝 Use your webcam to make gestures. The app will detect and display recognized signs!")