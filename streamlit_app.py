import streamlit as st
from PIL import Image
import numpy as np
import os
from pathlib import Path
import sys
import time
from collections import deque

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Check if we're running on Streamlit Cloud (headless environment)
IS_STREAMLIT_CLOUD = "STREAMLIT_SERVER_HEADLESS" in os.environ or "streamlit.run" in sys.argv[0]

st.set_page_config(page_title="Sign Language Detector", layout="wide", initial_sidebar_state="expanded")
st.title("🤟 Real-Time Sign Language Detection")
st.markdown("Detect sign language gestures from your webcam with real-time text and speech output!")

# Initialize detector only if not on cloud
detector = None
if not IS_STREAMLIT_CLOUD:
    try:
        import cv2
        import mediapipe as mp
        from app import SignLanguageDetector
        
        @st.cache_resource(show_spinner=True)
        def load_detector():
            try:
                return SignLanguageDetector()
            except FileNotFoundError as e:
                st.error(f"❌ Model not found: {e}")
                return None
            except Exception as e:
                st.error(f"❌ Error loading detector: {str(e)}")
                return None
        
        detector = load_detector()
        
        if detector is None:
            st.warning("⚠️ Could not initialize hand gesture detector. Running in demo mode.")
    except Exception as e:
        st.warning(f"⚠️ Cloud environment detected. Running in demo mode.\nFor full functionality, [run locally](https://github.com/NehaMary23/Sign-Language-Detector)")
        detector = None
else:
    # Cloud environment - show info message
    st.info(
        """
        ### 🌐 Running on Streamlit Cloud (Demo Mode)
        
        This cloud version shows the interface but **cannot detect hand gestures** because:
        - Streamlit Cloud is a headless environment (no webcam access)
        - GPU libraries required by MediaPipe aren't available
        
        **For full functionality with hand gesture detection:**
        1. Clone the repository: `git clone https://github.com/NehaMary23/Sign-Language-Detector.git`
        2. Follow the [installation instructions](https://github.com/NehaMary23/Sign-Language-Detector#installation)
        3. Run locally: `streamlit run streamlit_app.py`
        """
    )
    detector = None

# Sidebar controls
st.sidebar.header("⚙️ Settings & Controls")
enable_voice = st.sidebar.checkbox("🔊 Enable Voice Output", value=True)
confidence_threshold = st.sidebar.slider("Confidence Threshold", 0.5, 1.0, 0.70)
clear_output = st.sidebar.button("🗑️ Clear Output Buffer", use_container_width=True)

# Session state initialization
if "detected_gestures" not in st.session_state:
    st.session_state.detected_gestures = deque(maxlen=10)
if "output_text" not in st.session_state:
    st.session_state.output_text = ""
if "gesture_history" not in st.session_state:
    st.session_state.gesture_history = []

if clear_output:
    st.session_state.output_text = ""
    st.session_state.detected_gestures.clear()
    st.session_state.gesture_history.clear()
    st.success("✅ Output cleared!")

# Main interface
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📹 Webcam Feed")
    
    if detector is None:
        # Cloud mode - show placeholder
        st.warning("⚠️ Webcam input requires local installation. Run the app locally to use hand gesture detection.")
        # Still show camera input for UI, but don't process it
        camera_image = st.camera_input("Capture image from webcam")
    else:
        # Local mode - capture and process
        camera_image = st.camera_input("Capture image from webcam")
        
        if camera_image is not None:
            try:
                import cv2
                import mediapipe as mp
                
                # Convert PIL image to OpenCV format
                image = Image.open(camera_image).convert("RGB")
                img_array = np.array(image)
                
                # Convert to MediaPipe Image format (SRGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_array)
                
                # Detect hand landmarks
                hand_results = detector.hand_landmarker.detect(mp_image)
                
                # Process detections
                detected_text = ""
                if hand_results.hand_landmarks:
                    max_conf = 0.0
                    best_gesture = "-"
                    hands_data = []
                    
                    for idx, hand_landmarks in enumerate(hand_results.hand_landmarks):
                        # Get handedness
                        handedness = "Right"
                        if idx < len(hand_results.handedness):
                            handedness = hand_results.handedness[idx].display_name
                        
                        # Convert landmarks to pixel coordinates
                        h, w = img_array.shape[:2]
                        lm = [(lm.x * w, lm.y * h) for lm in hand_landmarks]
                        
                        # Check if hand is close enough
                        if not detector._is_hand_close(lm, img_array.shape):
                            continue
                        
                        # Store for two-hand gesture detection
                        hands_data.append({"lm": lm, "handedness": handedness})
                        
                        # Try THANK YOU motion first
                        gesture, conf = detector._classify_thank_you_motion(lm, handedness, img_array.shape)
                        
                        # If not THANK YOU, try regular gesture
                        if gesture == "-" and not detector.thank_you_tracking:
                            gesture, conf = detector._classify_gesture(lm, handedness)
                        
                        # Track best gesture
                        if conf > max_conf:
                            max_conf = conf
                            best_gesture = gesture
                    
                    # Check for two-hand HELP gesture
                    if len(hands_data) >= 2:
                        gesture, conf = detector._classify_help_two_hand(hands_data, img_array.shape)
                        if conf > max_conf:
                            max_conf = conf
                            best_gesture = gesture
                    
                    # Display result if above threshold
                    if best_gesture != "-" and max_conf >= confidence_threshold:
                        detected_text = f"✅ {best_gesture} ({max_conf:.0%})"
                        st.session_state.detected_gestures.append(best_gesture)
                        
                        # Update history
                        if not st.session_state.gesture_history or st.session_state.gesture_history[-1] != best_gesture:
                            st.session_state.gesture_history.append(best_gesture)
                        
                        # Text-to-speech if enabled
                        if enable_voice and detector.tts_supported:
                            try:
                                detector.speech_queue.put_nowait(best_gesture)
                            except:
                                pass
                    else:
                        detected_text = "🖐️ Hand(s) detected but no gesture recognized"
                else:
                    detected_text = "👋 No hands detected. Try again!"
                
                # Display detected gesture
                if "✅" in detected_text:
                    st.success(detected_text)
                else:
                    st.warning(detected_text)
                
                # Show the image
                st.image(image, use_container_width=True, caption="Your Gesture")
            except Exception as e:
                st.error(f"Error processing image: {str(e)}")

with col2:
    st.subheader("📊 Results")
    
    # Display current output
    if st.session_state.detected_gestures:
        current = st.session_state.detected_gestures[-1]
        st.metric("Last Gesture", current)
    else:
        st.metric("Last Gesture", "None")
    
    # Supported signs
    st.subheader("🎯 Supported Signs")
    signs = [
        "HELLO", "THANK YOU", "YES", "PLEASE", "NO", 
        "GOOD", "I LOVE YOU", "OK", "STOP", "HELP", "WATER", "SORRY"
    ]
    
    cols = st.columns(2)
    for i, sign in enumerate(signs):
        with cols[i % 2]:
            st.write(f"• {sign}")
    
    # Recent detections
    if st.session_state.gesture_history:
        st.subheader("📜 Recent Gestures")
        # Show unique recent gestures
        unique_recent = []
        for g in reversed(st.session_state.gesture_history[-10:]):
            if g not in unique_recent:
                unique_recent.append(g)
        
        for i, gesture in enumerate(unique_recent[:5], 1):
            st.caption(f"#{i}: {gesture}")

# Footer
st.markdown("---")
st.info("""
📝 **How to use:**
1. Position your hand clearly in the webcam
2. Make a gesture from the supported signs list
3. The app will detect and display recognized signs with confidence scores
4. Enable voice output to hear the detected gestures
🔧 **Tip:** Keep your hand closer to the camera for better detection
""")

# Display voice status
if detector and detector.tts_supported:
    st.markdown(f"🔊 Voice Support: **Enabled** - Using {'SAPI (Windows)' if detector.use_sapi else 'pyttsx3'}")
elif detector:
    st.markdown("🔊 Voice Support: **Not Available**")
    st.markdown("🔊 Voice Support: **Not available** - Text-to-speech libraries not detected")