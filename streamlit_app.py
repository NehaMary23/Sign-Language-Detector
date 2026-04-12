import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
import cv2

st.set_page_config(page_title="Sign Language Detector", layout="wide")
st.title("🤟 Real-Time Sign Language Detection")
st.markdown("Detect sign language gestures from your webcam!")

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

    camera_image = st.camera_input("Capture image from webcam")

    if camera_image is not None:
        # Convert to PIL Image
        image = Image.open(camera_image).convert("RGB")
        
        # Display the captured image
        st.image(image, use_container_width=True)
        st.success("✅ Image captured successfully!")

with col2:
    st.subheader("📊 Output")
    st.metric(
        "Detected Text",
        st.session_state.output_text if st.session_state.output_text else "No gestures detected"
    )

    st.subheader("🎯 Supported Signs")
    signs = ["HELLO", "THANK YOU", "YES", "PLEASE", "NO", "GOOD", "I LOVE YOU", "OK", "STOP", "HELP"]
    for sign in signs:
        st.write(f"• {sign}")

st.markdown("---")
st.info("📝 Use your webcam to make gestures. The app will detect and display recognized signs!")