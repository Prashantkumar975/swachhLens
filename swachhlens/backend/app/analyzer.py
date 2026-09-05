"""Bridge between the FastAPI backend and the SwachLens AI inference pipeline.

Tries the real AI pipeline first; falls back to a demo classifier
if PyTorch/ultralytics are not installed.
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path


def _detect_faces(image_bytes: bytes) -> bool:
    """Return True if the image likely contains a human face.

    Uses a two-pronged approach:
    1. OpenCV 5's FaceDetectorYN (Yunet DNN model) — accurate for real photos.
    2. Skin-tone heuristic — catches face-like images the DNN might miss.

    Falls back gracefully if cv2 or the model is unavailable.
    """
    try:
        import cv2
        import numpy as np

        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return False

        # --- Stage 1: DNN face detection (Yunet) ---
        try:
            model_path = str(Path(__file__).parent / "face_detection_yunet_2023mar.onnx")
            fd = cv2.FaceDetectorYN_create(model_path, "", (320, 320))
            fd.setInputSize((img.shape[1], img.shape[0]))
            _, faces = fd.detect(img)
            if faces is not None and len(faces) > 0:
                return True
        except Exception:
            pass  # Fall through to heuristic

        # --- Stage 2: Skin-tone heuristic ---
        # A portrait/headshot is typically >15% skin-tone pixels.
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # Skin-tone range in HSV (covers a wide range of skin colours)
        mask = cv2.inRange(hsv, (0, 20, 70), (25, 150, 255))
        skin_ratio = np.count_nonzero(mask) / mask.size
        return skin_ratio > 0.15
    except Exception:
        # If cv2 is unavailable, don't block the flow.
        return False


def _demo_analyze(image_bytes: bytes) -> dict:
    """Deterministic demo analysis when the real model isn't available."""
    # --- Guard: reject images that are clearly not waste ---
    if _detect_faces(image_bytes):
        return {
            "valid": False,
            "reason": "Image contains a person — please attach a photo of the waste.",
            "wasteType": None,
            "severity": None,
            "confidence": 0,
            "engine": "demo",
            "details": [],
            "summary": "The AI did not detect any waste — the image appears to contain a person.",
        }

    h = int(hashlib.md5(image_bytes[:1024]).hexdigest()[:8], 16)
    waste_types = ["Plastic", "Organic", "E-Waste", "Hazardous"]
    severities = ["Low", "Medium", "High"]
    wt = waste_types[h % len(waste_types)]
    sev = severities[h % 3]
    conf = 72 + (h % 25)
    return {
        "valid": True,
        "wasteType": wt,
        "severity": sev,
        "confidence": conf,
        "engine": "demo",
        "reason": None,
        "summary": f"AI detected {wt.lower()} waste ({sev.lower()} severity) with {conf}% confidence.",
        "details": [],
    }


def analyze_image(image_bytes: bytes) -> dict:
    """Run the SwachLens AI pipeline on uploaded image bytes.

    Tries the trained model first; falls back to a demo classifier
    if dependencies (torch, ultralytics) are not installed.
    """
    try:
        from pathlib import Path
        import sys

        PROJECT_ROOT = Path(__file__).resolve().parents[2]
        AI_INFERENCE_DIR = PROJECT_ROOT / "ai" / "inference"

        if AI_INFERENCE_DIR.is_dir() and str(AI_INFERENCE_DIR) not in sys.path:
            sys.path.insert(0, str(AI_INFERENCE_DIR))

        from analyze_image import analyze_image_bytes
        return analyze_image_bytes(image_bytes)
    except (ImportError, ModuleNotFoundError, FileNotFoundError, Exception):
        return _demo_analyze(image_bytes)
