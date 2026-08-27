"""
Image preprocessing pipeline using OpenCV.

Implements a simple two-track strategy:
  1. Run OCR on the original image.
  2. Run OCR on a preprocessed version (grayscale + denoise + contrast).
  3. Return whichever yields a better result (more blocks, higher avg confidence).

This module only produces processed image data — it does NOT call OCR.
"""

import time
from typing import List, Tuple, Optional
import cv2
import numpy as np

from app.core.logging import logger


# ---------------------------------------------------------------------------
# Quality Analysis
# ---------------------------------------------------------------------------

IMAGE_MIN_WIDTH = 200
IMAGE_MIN_HEIGHT = 200
BLUR_THRESHOLD = 100.0      # Laplacian variance below this is considered blurry
DARK_THRESHOLD = 0.20       # Normalised brightness below this is too dark
BRIGHT_THRESHOLD = 0.90     # Normalised brightness above this is too bright


def analyze_quality(image: np.ndarray) -> dict:
    """
    Analyse image quality and return a quality dict compatible with ImageQuality dataclass.

    Args:
        image: BGR or grayscale numpy array.

    Returns:
        dict with keys: status, blur_score, brightness_score, issues
    """
    h, w = image.shape[:2]
    issues: List[str] = []

    # --- Resolution check ---
    if w < IMAGE_MIN_WIDTH or h < IMAGE_MIN_HEIGHT:
        issues.append("IMAGE_TOO_SMALL")

    # --- Blur (Laplacian variance) ---
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if blur_score < BLUR_THRESHOLD:
        issues.append("IMAGE_TOO_BLURRY")

    # --- Brightness (mean pixel / 255) ---
    brightness_score = float(np.mean(gray) / 255.0)
    if brightness_score < DARK_THRESHOLD:
        issues.append("IMAGE_TOO_DARK")
    elif brightness_score > BRIGHT_THRESHOLD:
        issues.append("IMAGE_TOO_BRIGHT")

    # --- Overall status ---
    if not issues:
        status = "GOOD"
    elif "IMAGE_TOO_SMALL" in issues or "IMAGE_TOO_BLURRY" in issues:
        status = "POOR"
    else:
        status = "FAIR"

    return {
        "status": status,
        "blur_score": blur_score,
        "brightness_score": brightness_score,
        "issues": issues,
    }


# ---------------------------------------------------------------------------
# Preprocessing Steps
# ---------------------------------------------------------------------------

def load_image(image_path: str) -> np.ndarray:
    """Load image from disk, raise ValueError if unreadable."""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot load image: {image_path}")
    return img


def resize_for_ocr(image: np.ndarray, target_max_dim: int = 1920) -> Tuple[np.ndarray, bool]:
    """
    Resize image if the longest dimension exceeds target_max_dim.
    Returns (image, was_resized).
    """
    h, w = image.shape[:2]
    max_dim = max(h, w)
    if max_dim <= target_max_dim:
        return image, False
    scale = target_max_dim / max_dim
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, True


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert BGR to grayscale. If already grayscale, return as-is."""
    if len(image.shape) == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def denoise(gray: np.ndarray) -> np.ndarray:
    """Apply non-local means denoising."""
    return cv2.fastNlMeansDenoising(gray, h=10)


def enhance_contrast(gray: np.ndarray) -> np.ndarray:
    """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def grayscale_to_bgr(gray: np.ndarray) -> np.ndarray:
    """Convert grayscale back to BGR for PaddleOCR (expects 3-channel)."""
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


# ---------------------------------------------------------------------------
# Preprocessing Pipeline
# ---------------------------------------------------------------------------

def build_preprocessed_image(original: np.ndarray) -> Tuple[np.ndarray, List[str]]:
    """
    Apply the standard preprocessing pipeline:
      resize → grayscale → denoise → contrast enhancement → back to BGR

    Returns:
        (processed_bgr, list_of_steps_applied)
    """
    steps: List[str] = []
    img = original.copy()

    img, was_resized = resize_for_ocr(img)
    if was_resized:
        steps.append("resize")

    gray = to_grayscale(img)
    steps.append("grayscale")

    denoised = denoise(gray)
    steps.append("denoise")

    contrasted = enhance_contrast(denoised)
    steps.append("contrast")

    result_bgr = grayscale_to_bgr(contrasted)
    return result_bgr, steps


def preprocess_image_path(image_path: str) -> Tuple[np.ndarray, np.ndarray, List[str], dict]:
    """
    High-level entry point: load, analyse quality, preprocess.

    Returns:
        (original_bgr, preprocessed_bgr, preprocessing_steps, quality_dict)
    """
    original = load_image(image_path)
    quality = analyze_quality(original)
    preprocessed, steps = build_preprocessed_image(original)
    return original, preprocessed, steps, quality
