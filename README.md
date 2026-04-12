# 🤟 Sign Language Detector

A real-time sign language gesture detection application using MediaPipe and Streamlit with text and speech output.

## Features

- 🎥 **Live Webcam Detection** - Real-time hand gesture recognition
- 🎯 **Multiple Gestures** - HELLO, OK, YES, NO, GOOD, I LOVE YOU, THANK YOU, WATER, PLEASE, HELP, SORRY, STOP
- 🔊 **Text & Speech Output** - Converts recognized gestures to text and optionally speaks them
- 📊 **Confidence Scoring** - Shows confidence level for each detection
- 🎨 **Web Interface** - Built with Streamlit for easy deployment
- ⚡ **Stable Predictions** - Advanced filtering to reduce flicker and false positives

## Tech Stack

- **Python 3.13+**
- **Streamlit** - Web framework
- **MediaPipe** - Hand landmark detection (21-point hand model)
- **OpenCV** - Video processing
- **pyttsx3** - Text-to-speech engine

## Installation

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/NehaMary23/Sign-Language-Detector.git
cd Sign-Language-Detector
```

2. Create a virtual environment:
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate      # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download the MediaPipe model:
   - Download `hand_landmarker.task` from [MediaPipe Models](https://developers.google.com/mediapipe/solutions/vision/hand_landmarker#models)
   - Place it in the `models/` folder

## Running Locally

### Streamlit Web App
```bash
streamlit run streamlit_app.py
```

The app opens at `http://localhost:8501`

### Desktop App
```bash
python app.py
```

## Deployment to Streamlit Cloud

### Step 1: Ensure Repository is Up-to-Date
```bash
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

### Step 2: Deploy to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Connect your repository
5. Select:
   - **Repository**: NehaMary23/Sign-Language-Detector
   - **Branch**: main
   - **Main file path**: streamlit_app.py
6. Click "Deploy"

The app will be live at a URL like: `https://[your-username]-sign-lang-detector.streamlit.app`

### Note on Webcam Access
Streamlit Cloud apps run in the cloud without local webcam access. For webcam functionality, you must:
- Run the app locally using `streamlit run streamlit_app.py`
- Or implement the desktop version with `python app.py`

## File Structure

```
Sign-Lang-Detector/
├── app.py                    # Core detector class & desktop app
├── streamlit_app.py         # Streamlit web interface
├── requirements.txt         # Python dependencies
├── models/
│   ├── hand_landmarker.task
│   └── pose_landmarker.task
├── .streamlit/
│   └── config.toml         # Streamlit configuration
└── README.md
```

## Supported Gestures

| Gesture | Hand Shape | Notes |
|---------|-----------|-------|
| OK | Thumb-index circle | Middle/ring/pinky open |
| STOP | Open palm | Wide thumb-pinky spread |
| YES | Four fingers open, thumb closed | |
| NO | Closed fist | Thumb crosses fingers |
| GOOD | Thumbs-up | Thumb only, pointing up |
| HELP | Thumb open | Thumb down/sideways |
| I LOVE YOU | Thumb + index + pinky open | Middle & ring closed |
| WATER | W-handshape | Index/middle/ring open |
| PLEASE | Open hand | All fingers spread |
| SORRY | Compact fist | Thumb crosses curled fingers |
| THANK YOU | Motion gesture | Hand moves outward from face |
| HELP (2-hand) | One fist + one palm | Stacked hands position |

## How It Works

1. **Hand Detection** - MediaPipe detects hand landmarks in real-time
2. **Finger Analysis** - Determines which fingers are open/closed
3. **Gesture Recognition** - Rule-based classifier matches finger patterns to gestures
4. **Stability Filtering** - Buffers predictions to avoid flicker
5. **Cooldown Logic** - Prevents rapid repeated recognition of the same gesture
6. **Text Output** - Recognized words are appended to output text
7. **Speech Synthesis** - Optional pyttsx3-based voice output

## Configuration

Edit `.streamlit/config.toml` to customize:
- Theme colors
- Logging level
- Server settings
- Browser behavior

## Limitations

- **Fixed vocabulary** - Limited to pre-defined gestures
- **Single language** - Rule-based, not language-specific
- **Hand-only** - Doesn't include body pose or facial expressions
- **Accuracy** - Depends on hand visibility and lighting conditions
- **No webcam in cloud** - Streamlit Cloud doesn't support webcam access

## Future Improvements

- Add trained model for sentence-level recognition
- Support for full sign language vocabulary
- Incorporate body pose and facial expressions
- Multi-language support (ASL, ISL, BSL)
- Real-time translation to spoken language
- Mobile app version

## License

This project is provided as-is for educational purposes.

## Contact

For questions or issues, please create an issue on [GitHub](https://github.com/NehaMary23/Sign-Language-Detector/issues)
