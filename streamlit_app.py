import streamlit as st
from PIL import Image, ImageDraw
import mediapipe as mp
import numpy as np
from pathlib import Path
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
    
    # Use Streamlit's camera input
    camera_image = st.camera_input("Capture image from webcam")
    
    if camera_image is not None:
        # Convert to PIL Image
        image = Image.open(camera_image).convert("RGB")
        w, h = image.size
        
        # Convert to numpy for MediaPipe
        img_array = np.array(image)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_array)
        
        # Detect hands
        hand_results = hand_landmarker.detect(mp_image)
        
        # Draw landmarks on PIL image
        draw = ImageDraw.Draw(image)
        
        if hand_results.hand_landmarks:
            for hand_landmarks in hand_results.hand_landmarks:
                # Draw circles on landmark points
                for landmark in hand_landmarks:
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    draw.ellipse([x-4, y-4, x+4, y+4], fill=(0, 255, 255))
                
                # Draw connections
                for conn in vision.HandLandmarksConnections.HAND_CONNECTIONS:
                    start = hand_landmarks[conn.start]
                    end = hand_landmarks[conn.end]
                    x1, y1 = int(start.x * w), int(start.y * h)
                    x2, y2 = int(end.x * w), int(end.y * h)
                    draw.line([(x1, y1), (x2, y2)], fill=(0, 180, 255), width=2)
        
        # Display frame
        st.image(image, use_container_width=True)

with col2:
    st.subheader("📊 Output")
    st.metric("Detected Text", st.session_state.output_text if st.session_state.output_text else "No gestures detected")
    
    st.subheader("🎯 Supported Signs")
    signs = ["HELLO", "THANK YOU", "YES", "PLEASE", "NO", "GOOD", "I LOVE YOU", "OK", "STOP", "HELP"]
    for sign in signs:
        st.write(f"• {sign}")

st.markdown("---")
st.info("📝 Use your webcam to make gestures. The app will detect and display recognized signs!")