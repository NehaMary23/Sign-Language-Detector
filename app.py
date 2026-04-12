import time
import queue
import threading
from pathlib import Path
from collections import deque

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.core import base_options as base_options_module

try:
    import pyttsx3
except Exception:
    pyttsx3 = None

try:
    import pythoncom
    from win32com.client import Dispatch
except Exception:
    pythoncom = None
    Dispatch = None


class SignLanguageDetector:
    def __init__(self):
        self.model_path = Path(__file__).parent / "models" / "hand_landmarker.task"
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {self.model_path}. "
                "Please download hand_landmarker.task into the models folder."
            )

        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(
                model_asset_path=str(self.model_path),
                delegate=base_options_module.Delegate.CPU
            ),
            running_mode=vision.RunningMode.IMAGE,
            num_hands=2,
            min_hand_detection_confidence=0.65,
            min_hand_presence_confidence=0.65,
            min_tracking_confidence=0.65,
        )
        self.hand_landmarker = vision.HandLandmarker.create_from_options(options)

        self.pred_buffer = deque(maxlen=10)
        self.last_accepted = ""
        self.last_accept_time = 0.0
        self.cooldown_seconds = 0.8
        self.no_pred_frames = 0
        self.reset_repeat_after_frames = 12
        self.min_hand_area_ratio = 0.035
        self.min_palm_ratio = 0.11

        self.thank_you_tracking = False
        self.thank_you_start_time = 0.0
        self.thank_you_start_wrist = None
        self.thank_you_emit_until = 0.0

        self.output_text = ""
        self.display_word_queue = deque()
        self.current_display_word = ""
        self.next_word_time = 0.0
        self.word_display_seconds = 0.7
        self.use_sapi = Dispatch is not None
        self.tts_supported = self.use_sapi or (pyttsx3 is not None)
        self.voice_enabled = self.tts_supported
        self.speech_queue = queue.Queue(maxsize=50)
        self.tts_stop_event = threading.Event()
        self.tts_thread = None

        if self.tts_supported:
            self.tts_thread = threading.Thread(target=self._speech_worker, daemon=True)
            self.tts_thread.start()

    @staticmethod
    def _distance(a, b):
        return np.linalg.norm(np.array(a) - np.array(b))

    def _finger_states(self, lm, handedness="Right"):
        # lm: list of 21 (x, y) points in pixel coords
        # Landmark indices:
        # Thumb: tip 4, ip 3, mcp 2
        # Index: tip 8, pip 6
        # Middle: tip 12, pip 10
        # Ring: tip 16, pip 14
        # Pinky: tip 20, pip 18

        if handedness == "Left":
            thumb_open = lm[4][0] < lm[3][0]
        else:
            thumb_open = lm[4][0] > lm[3][0]
        index_open = lm[8][1] < lm[6][1]
        middle_open = lm[12][1] < lm[10][1]
        ring_open = lm[16][1] < lm[14][1]
        pinky_open = lm[20][1] < lm[18][1]

        return {
            "thumb": thumb_open,
            "index": index_open,
            "middle": middle_open,
            "ring": ring_open,
            "pinky": pinky_open,
        }

    def _classify_gesture(self, lm, handedness="Right"):
        states = self._finger_states(lm, handedness)

        # Palm scale reference (wrist to middle MCP)
        palm_size = max(self._distance(lm[0], lm[9]), 1.0)

        # Distances for shape-based gestures
        thumb_index = self._distance(lm[4], lm[8]) / palm_size
        index_middle = self._distance(lm[8], lm[12]) / palm_size
        index_ring = self._distance(lm[8], lm[16]) / palm_size
        thumb_pinky = self._distance(lm[4], lm[20]) / palm_size

        open_count = sum(states.values())
        thumb_up = lm[4][1] < lm[3][1]

        # Rule-based gestures mapped to words
        # OK: thumb-index circle, middle/ring/pinky open (index may be bent)
        if (
            states["middle"]
            and states["ring"]
            and states["pinky"]
            and thumb_index < 0.28
        ):
            return "OK", 0.91

        # STOP: open palm with wider thumb-pinky spread
        if open_count == 5 and thumb_pinky > 1.25:
            return "STOP", 0.90

        # NO: closed fist with thumb crossing the curled fingers
        if (
            (not states["index"])
            and (not states["middle"])
            and (not states["ring"])
            and (not states["pinky"])
            and thumb_index < 0.42
            and thumb_pinky < 1.05
        ):
            return "NO", 0.90

        # SORRY: compact fist variant
        if open_count <= 1 and thumb_index < 0.22 and index_middle < 0.25:
            return "SORRY", 0.80

        # YES: four fingers open, thumb closed
        if (
            (not states["thumb"])
            and states["index"]
            and states["middle"]
            and states["ring"]
            and states["pinky"]
        ):
            return "YES", 0.88

        # GOOD: thumbs-up (only thumb open and pointing upward)
        if (
            states["thumb"]
            and (not states["index"])
            and (not states["middle"])
            and (not states["ring"])
            and (not states["pinky"])
            and thumb_up
        ):
            return "GOOD", 0.92

        # HELP: only thumb open, but not thumbs-up orientation
        if (
            states["thumb"]
            and (not states["index"])
            and (not states["middle"])
            and (not states["ring"])
            and (not states["pinky"])
            and (not thumb_up)
        ):
            return "HELP", 0.84

        # I LOVE YOU: thumb + index + pinky open, middle + ring closed
        if (
            states["thumb"]
            and states["index"]
            and (not states["middle"])
            and (not states["ring"])
            and states["pinky"]
        ):
            return "I LOVE YOU", 0.93

        # WATER: W-handshape (index + middle + ring open, thumb + pinky closed)
        if (
            (not states["thumb"])
            and states["index"]
            and states["middle"]
            and states["ring"]
            and (not states["pinky"])
            and index_ring < 0.95
        ):
            return "WATER", 0.90

        # PLEASE: open hand with thumb open and moderate spread (avoid overlap with YES/STOP)
        if (
            states["thumb"]
            and states["index"]
            and states["middle"]
            and states["ring"]
            and states["pinky"]
            and 0.50 <= thumb_index <= 1.05
            and thumb_pinky < 1.20
        ):
            return "PLEASE", 0.82

        return "-", 0.0

    def _classify_thank_you_motion(self, lm, handedness, frame_shape):
        now = time.time()
        if now < self.thank_you_emit_until:
            return "THANK YOU", 0.96

        h, w = frame_shape[0], frame_shape[1]
        states = self._finger_states(lm, handedness)
        open_count = sum(states.values())

        wrist_x, wrist_y = lm[0]
        index_tip = lm[8]
        middle_tip = lm[12]
        ring_tip = lm[16]
        pinky_tip = lm[20]
        hand_center_x, hand_center_y = lm[9]

        fingertips_avg_y = (index_tip[1] + middle_tip[1] + ring_tip[1] + pinky_tip[1]) / 4.0
        finger_spread = self._distance(index_tip, pinky_tip)

        near_face_zone = (0.22 * h) <= fingertips_avg_y <= (0.58 * h) and (0.28 * w) <= hand_center_x <= (0.72 * w)
        upright_hand = fingertips_avg_y < (wrist_y - 0.06 * h)
        flat_open_hand = open_count >= 4 and finger_spread < (0.38 * w)

        start_pose = near_face_zone and upright_hand and flat_open_hand

        if start_pose and not self.thank_you_tracking:
            self.thank_you_tracking = True
            self.thank_you_start_time = now
            self.thank_you_start_wrist = (hand_center_x, fingertips_avg_y)
            return "-", 0.0

        if self.thank_you_tracking:
            elapsed = now - self.thank_you_start_time
            if elapsed > 1.0:
                self.thank_you_tracking = False
                self.thank_you_start_wrist = None
                return "-", 0.0

            start_x, start_y = self.thank_you_start_wrist
            moved_forward_2d = (fingertips_avg_y - start_y) > (0.08 * h)
            moved_outward = abs(hand_center_x - start_x) > (0.08 * w)

            if open_count >= 4 and (moved_forward_2d or moved_outward):
                self.thank_you_tracking = False
                self.thank_you_start_wrist = None
                self.thank_you_emit_until = now + 0.6
                return "THANK YOU", 0.96

        return "-", 0.0

    def _classify_help_two_hand(self, hands_data, frame_shape):
        if len(hands_data) < 2:
            return "-", 0.0

        frame_h, frame_w = frame_shape[0], frame_shape[1]

        fist_candidates = []
        palm_candidates = []
        for hand in hands_data:
            lm = hand["lm"]
            handedness = hand["handedness"]
            states = self._finger_states(lm, handedness)
            open_count = sum(states.values())

            if open_count <= 1:
                fist_candidates.append(hand)
            if open_count >= 4:
                palm_candidates.append(hand)

        if not fist_candidates or not palm_candidates:
            return "-", 0.0

        for fist in fist_candidates:
            for palm in palm_candidates:
                if fist is palm:
                    continue

                fist_lm = fist["lm"]
                palm_lm = palm["lm"]

                fist_wrist_x, fist_wrist_y = fist_lm[0]
                palm_wrist_x, palm_wrist_y = palm_lm[0]
                palm_center_x, palm_center_y = palm_lm[9]

                horizontal_close = abs(fist_wrist_x - palm_center_x) < (0.22 * frame_w)
                near_palm_vertically = (palm_center_y - 0.25 * frame_h) < fist_wrist_y < (palm_center_y + 0.08 * frame_h)
                stacked_hands = fist_wrist_y < (palm_wrist_y + 0.02 * frame_h)
                palms_close = self._distance((fist_wrist_x, fist_wrist_y), (palm_center_x, palm_center_y)) < (0.28 * frame_w)

                if horizontal_close and near_palm_vertically and stacked_hands and palms_close:
                    return "HELP", 0.93

        return "-", 0.0

    def _is_hand_close(self, lm, frame_shape):
        frame_h, frame_w = frame_shape[0], frame_shape[1]
        if frame_h <= 0 or frame_w <= 0:
            return False

        xs = [pt[0] for pt in lm]
        ys = [pt[1] for pt in lm]
        hand_w = max(xs) - min(xs)
        hand_h = max(ys) - min(ys)

        hand_area_ratio = (hand_w * hand_h) / float(frame_w * frame_h)
        palm_ratio = self._distance(lm[0], lm[9]) / float(min(frame_w, frame_h))

        return hand_area_ratio >= self.min_hand_area_ratio or palm_ratio >= self.min_palm_ratio

    def _speech_worker(self):
        if not self.tts_supported:
            return

        tts_engine = None
        sapi_speaker = None
        if self.use_sapi:
            try:
                pythoncom.CoInitialize()
                sapi_speaker = Dispatch("SAPI.SpVoice")
                sapi_speaker.Rate = 0
            except Exception:
                sapi_speaker = None

        if sapi_speaker is None:
            try:
                tts_engine = pyttsx3.init()
                tts_engine.setProperty("rate", 165)
            except Exception:
                if self.use_sapi and pythoncom is not None:
                    try:
                        pythoncom.CoUninitialize()
                    except Exception:
                        pass
                return

        while not self.tts_stop_event.is_set():
            try:
                phrase = self.speech_queue.get(timeout=0.15)
            except queue.Empty:
                continue

            if phrase is None:
                break

            if self.voice_enabled:
                try:
                    if sapi_speaker is not None:
                        sapi_speaker.Speak(phrase)
                    else:
                        tts_engine.say(phrase)
                        tts_engine.runAndWait()
                except Exception:
                    pass

        if self.use_sapi and pythoncom is not None:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

    def _speak(self, text):
        if not self.tts_supported:
            return
        spoken_text = text.strip()
        if not spoken_text:
            return
        try:
            self.speech_queue.put_nowait(spoken_text)
        except queue.Full:
            pass

    def _emit_words(self, phrase):
        words = [word for word in phrase.strip().split() if word]
        if not words:
            return

        for word in words:
            self.display_word_queue.append(word)
            self._speak(word)

    def _update_output_text(self):
        now = time.time()
        if now < self.next_word_time:
            return

        if self.display_word_queue:
            self.current_display_word = self.display_word_queue.popleft()
            self.output_text = self.current_display_word
            self.next_word_time = now + self.word_display_seconds
        elif self.current_display_word:
            self.current_display_word = ""
            self.output_text = ""

    def _accept_prediction(self, pred, conf):
        if pred == "-":
            self.no_pred_frames += 1
            if self.no_pred_frames >= self.reset_repeat_after_frames:
                self.last_accepted = ""
                self.pred_buffer.clear()
            return

        self.no_pred_frames = 0

        self.pred_buffer.append(pred)
        if len(self.pred_buffer) < self.pred_buffer.maxlen:
            return

        majority = max(set(self.pred_buffer), key=self.pred_buffer.count)
        majority_ratio = self.pred_buffer.count(majority) / len(self.pred_buffer)

        now = time.time()
        if majority_ratio >= 0.7 and conf >= 0.70:
            if majority != self.last_accepted and (now - self.last_accept_time) > self.cooldown_seconds:
                self.last_accepted = majority
                self.last_accept_time = now
                self._emit_words(majority)

    @staticmethod
    def _draw_hand(frame, hand_landmarks):
        h, w, _ = frame.shape
        points = []
        for p in hand_landmarks:
            x, y = int(p.x * w), int(p.y * h)
            points.append((x, y))
            cv2.circle(frame, (x, y), 4, (0, 255, 255), -1)

        for conn in vision.HandLandmarksConnections.HAND_CONNECTIONS:
            start = points[conn.start]
            end = points[conn.end]
            cv2.line(frame, start, end, (0, 180, 255), 2)

        return points

    @staticmethod
    def _open_camera():
        candidates = [
            (0, cv2.CAP_DSHOW),
            (0, cv2.CAP_MSMF),
            (0, None),
            (1, cv2.CAP_DSHOW),
            (1, None),
        ]

        for index, backend in candidates:
            cap = cv2.VideoCapture(index, backend) if backend is not None else cv2.VideoCapture(index)
            if not cap.isOpened():
                cap.release()
                continue

            for _ in range(8):
                ok, _ = cap.read()
                if ok:
                    return cap
                cv2.waitKey(30)

            cap.release()

        return None

    def run(self):
        cap = self._open_camera()
        if cap is None:
            print("Error: Could not open webcam or read frames. Close other camera apps and try again.")
            return

        window_name = "Sign Language Detection - Word Mode"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            hand_results = self.hand_landmarker.detect(mp_image)

            pred, conf = "-", 0.0
            hands_data = []
            far_hand_detected = False

            if hand_results.hand_landmarks:
                for idx, hand_landmarks in enumerate(hand_results.hand_landmarks):
                    handedness = "Right"
                    if idx < len(hand_results.handedness) and hand_results.handedness[idx]:
                        handedness = hand_results.handedness[idx][0].category_name or "Right"

                    lm = self._draw_hand(frame, hand_landmarks)
                    if not self._is_hand_close(lm, frame.shape):
                        far_hand_detected = True
                        continue

                    hands_data.append({"lm": lm, "handedness": handedness})
                    this_pred, this_conf = self._classify_thank_you_motion(lm, handedness, frame.shape)
                    if this_pred == "-" and (not self.thank_you_tracking):
                        this_pred, this_conf = self._classify_gesture(lm, handedness)
                    if this_conf > conf:
                        pred, conf = this_pred, this_conf

                help_pred, help_conf = self._classify_help_two_hand(hands_data, frame.shape)
                if help_conf > conf:
                    pred, conf = help_pred, help_conf

            self._accept_prediction(pred, conf)
            self._update_output_text()

            h, w, _ = frame.shape
            panel_width = min(980, w - 20)
            cv2.rectangle(frame, (10, 10), (10 + panel_width, 160), (20, 20, 20), -1)
            cv2.putText(frame, f"Gesture detected: {pred}", (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            cv2.putText(frame, f"Confidence: {conf:.2f}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 220, 0), 2)
            cv2.putText(frame, f"Text Output: {self.output_text}", (20, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
            if far_hand_detected and pred == "-":
                cv2.putText(frame, "Move hand closer to camera", (20, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
            cv2.putText(
                frame,
                f"Voice: {'ON' if self.voice_enabled else 'OFF'} | Keys: v=voice, c=clear, q=quit",
                (20, 145),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (180, 180, 180),
                1,
            )

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break
            if key == ord("c"):
                self.output_text = ""
                self.current_display_word = ""
                self.display_word_queue.clear()
                self.next_word_time = 0.0
                self.last_accepted = ""
                self.pred_buffer.clear()
            if key == ord("v"):
                if self.tts_supported:
                    self.voice_enabled = not self.voice_enabled

        cap.release()
        self.hand_landmarker.close()
        self.tts_stop_event.set()
        if self.tts_thread is not None and self.tts_thread.is_alive():
            try:
                self.speech_queue.put_nowait(None)
            except queue.Full:
                pass
            self.tts_thread.join(timeout=1.0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    detector = SignLanguageDetector()
    detector.run()
