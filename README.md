# Sign Language Detection (Basic Semester Project)

A real-time sign language detection MVP using:

- Python
- OpenCV
- MediaPipe (21 hand landmarks)
- NumPy
- Optional text-to-speech (pyttsx3)

This version is built for a **Computer Graphics / Image Processing semester project** and focuses on a **basic level** (word mode):

- `HELLO`, `THANK YOU`, `YES`, `PLEASE`, `NO`, `GOOD`, `I LOVE YOU`

---

## Features

- Live webcam hand tracking
- Gesture-to-word detection (basic fixed vocabulary)
- Confidence score display
- Stable prediction logic (reduces flicker)
- Gesture-to-text conversion (builds sentence over time)
- Optional voice output (speaks accepted words)

---

## Project Structure

```text
compg/
  app.py
  requirements.txt
  README.md
```

---

## Installation

1. Make sure Python 3.14 is installed.
2. Install dependencies:

```bash
py -3.14 -m pip install -r requirements.txt
```

---

## Run

```bash
py -3.14 app.py
```

Press keys while running:

- `v`: Toggle voice on/off
- `c`: Clear output text
- `q`: Quit

---

## Demo Flow

1. Run the program
2. Webcam starts
3. Show hand gesture
4. System recognizes word (`HELLO`, `I LOVE YOU`, etc.)
5. Recognized words are appended to output text

Example on screen:

- `Gesture detected: I LOVE YOU`
- `Confidence: 0.86`
- `Text Output: HELLO I LOVE YOU PLEASE`

---

## Notes for Presentation

- Explain MediaPipe’s 21 landmark points and fingertip tracking
- Explain rule-based finger state detection (open/closed fingers)
- Explain stability filtering and confidence scoring
- Discuss how this can be extended to sentence-level detection using sequence models

---

## Important Limitation

This project is a **rule-based demo** with a small fixed vocabulary.

Detecting **all words and full sentences in universal sign language** is not feasible with simple hand-shape rules alone. For that, you need:

- A large labeled sign-language dataset
- A trained temporal model (LSTM/Transformer) for motion + context
- Support for both hands, body pose, and facial expressions
- Language-specific modeling (ASL/ISL/BSL are different languages)

---

## Future Enhancements

- Add all alphabets (A-Z)
- Add word-level recognition
- Add deep learning classifier for better accuracy
- Add GUI dashboard with Tkinter/Pygame
- Add sentence-level sign interpretation
