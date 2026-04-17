# Sign Language Detector

A real-time gesture recognition system that detects sign language hand gestures and converts them into text and speech using computer vision and machine learning.

## 🔍 Overview

This project uses Python, MediaPipe, and OpenCV to recognize 12+ hand gestures from webcam input. It provides real-time feedback with text output and voice synthesis, making it useful for accessibility and communication support.

## ✨ Features

* Real-time hand gesture detection
* Supports 12+ predefined gestures (OKAY, YES, NO, THANK YOU, etc.)
* Text output for recognized gestures
* Text-to-speech (TTS) conversion

## 🛠️ Tech Stack

* **Python**
* **MediaPipe** – Hand landmark detection
* **OpenCV** – Video processing
* **NumPy, Pillow** – Data & image processing
* **pyttsx3** – Text-to-speech

## 🚀 Run Locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## 💡 What I Learned

* Real-time computer vision using MediaPipe
* Gesture recognition using hand landmarks
* Handling video streams with OpenCV

## 🚀 Future Improvements

* Machine learning-based gesture classification
* More gestures (A–Z, numbers)
* Mobile app version
* Gesture sequence recognition
* Improved accuracy with training data

## 🌐 Use Cases

* Assistive tool for communication
* Learning basic sign language
* Demonstration of gesture recognition systems
