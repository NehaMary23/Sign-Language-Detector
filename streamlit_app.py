import streamlit as st
from PIL import Image, ImageDraw
import mediapipe as mp
from mediapipe.solutions import hands as mp_hands
from mediapipe.solutions import drawing_utils as mp_drawing
import numpy as np

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
        w, h = image.size

        # Convert to numpy for MediaPipe
        img_array = np.array(image)

        # Use context manager to avoid resource leaks
        with mp_hands.Hands(
            static_image_mode=True,
            max_num_hands=2,
            min_detection_confidence=0.65,
            min_tracking_confidence=0.65
        ) as hands:
            results = hands.process(img_array)

        # Draw landmarks on PIL image
        draw = ImageDraw.Draw(image)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw circles on landmark points
                for landmark in hand_landmarks.landmark:
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    draw.ellipse([x-4, y-4, x+4, y+4], fill=(0, 255, 255))

                # Draw connections
                connections = mp_hands.HAND_CONNECTIONS
                for connection in connections:
                    start_idx, end_idx = connection[0], connection[1]
                    start = hand_landmarks.landmark[start_idx]
                    end = hand_landmarks.landmark[end_idx]
                    x1, y1 = int(start.x * w), int(start.y * h)
                    x2, y2 = int(end.x * w), int(end.y * h)
                    draw.line([(x1, y1), (x2, y2)], fill=(0, 180, 255), width=2)

        # Display annotated frame
        st.image(image, use_container_width=True)

        if results.multi_hand_landmarks:
            st.success(f"✅ Detected {len(results.multi_hand_landmarks)} hand(s)")
        else:
            st.warning("🖐️ No hands detected. Try again!")

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