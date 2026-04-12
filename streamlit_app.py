import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
from collections import deque

st.title("Sign Language Detector 🤟")

run = st.checkbox('Start Camera')
FRAME_WINDOW = st.image([])

cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

while run:
    ret, frame = cap.read()
    if not ret:
        st.write("Camera not working")
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp.solutions.drawing_utils.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    FRAME_WINDOW.image(frame, channels='BGR')

cap.release()