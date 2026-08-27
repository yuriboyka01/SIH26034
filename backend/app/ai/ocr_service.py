"""
PaddleOCR service — wraps PaddleOCR and returns normalized OCRResult dataclasses.

Phase 3 (declaration extraction) must depend only on app.ai.models, never on
PaddleOCR internals directly.

Design:
  - Singleton PaddleOCR instance (lazy initialized) to avoid reloading models per request.
  - Two-track strategy: run on original AND preprocessed image, keep the better result
    (more blocks with higher average confidence wins).
  - Polygon bboxes from PaddleOCR are converted to axis-aligned [x1,y1,x2,y2] rectangles.
"""

import re
import time
from typing import List, Optional, Tuple
import numpy as np

from app.ai.models import OCRTextBlock, OCRResult, ImageQuality
from app.ai.preprocessing import preprocess_image_path, load_image
from app.core.logging import logger

_paddle_ocr_instance = None
_paddle_ocr_version = "unknown"

def _get_paddle_ocr():
    """Return (or create) the shared PaddleOCR instance."""
    global _paddle_ocr_instance, _paddle_ocr_version
    if _paddle_ocr_instance is None:
        try:
            from paddleocr import PaddleOCR
            import paddleocr
            _paddle_ocr_version = getattr(paddleocr, "__version__", "unknown")
            logger.info(f"Initialising PaddleOCR (CPU) version={_paddle_ocr_version}")
            # Initialize with show_log=False to reduce noise, use_angle_cls=True for rotated text
            _paddle_ocr_instance = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        except ImportError as exc:
            raise RuntimeError(
                "PaddleOCR is not installed. Run: pip install paddleocr"
            ) from exc
    return _paddle_ocr_instance, _paddle_ocr_version

def _normalize_text(raw: str) -> str:
    """
    Light normalization: strip edges, collapse repeated spaces/newlines.
    Preserves the detected content — does NOT rewrite it.
    """
    text = raw.strip()
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text

def _polygon_to_bbox(polygon) -> List[float]:
    """
    Convert a PaddleOCR polygon (list of [x,y] points) to [x1, y1, x2, y2].
    We take the axis-aligned bounding box of all points.
    """
    xs = [pt[0] for pt in polygon]
    ys = [pt[1] for pt in polygon]
    return [float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))]

def _run_paddle_on_image(image: np.ndarray) -> List[OCRTextBlock]:
    """
    Run PaddleOCR on a BGR numpy array.
    Returns a list of OCRTextBlock instances.
    """
    ocr, _ = _get_paddle_ocr()
    blocks: List[OCRTextBlock] = []

    try:
        raw_result = ocr.ocr(image, cls=True)
        if not raw_result:
            return blocks

        for page in raw_result:
            if not page:
                continue
            for line in page:
                if not line or len(line) < 2:
                    continue
                polygon, (text, confidence) = line
                raw_text = str(text)
                normalized = _normalize_text(raw_text)
                bbox = _polygon_to_bbox(polygon)
                blocks.append(OCRTextBlock(
                    raw_text=raw_text,
                    normalized_text=normalized,
                    confidence=float(confidence),
                    bbox=bbox,
                ))
        return blocks
    except Exception as e:
        logger.error(f"OCR inference error: {e}")
        return blocks

def _score_blocks(blocks: List[OCRTextBlock]) -> float:
    """
    Composite score: number of blocks × average confidence.
    """
    if not blocks:
        return 0.0
    avg_conf = sum(b.confidence for b in blocks) / len(blocks)
    return len(blocks) * avg_conf

def extract(image_path: str) -> OCRResult:
    """
    Run the full OCR pipeline on an image file.
    """
    start = time.monotonic()

    # --- Load and preprocess ---
    original, preprocessed, preprocessing_steps, quality_dict = preprocess_image_path(image_path)

    # --- OCR on original ---
    logger.info(f"OCR | running on original image: {image_path}")
    blocks_original = _run_paddle_on_image(original)

    # --- OCR on preprocessed ---
    logger.info(f"OCR | running on preprocessed image: {image_path}")
    blocks_preprocessed = _run_paddle_on_image(preprocessed)

    # --- Choose better result ---
    score_orig = _score_blocks(blocks_original)
    score_prep = _score_blocks(blocks_preprocessed)

    if score_prep > score_orig:
        chosen_blocks = blocks_preprocessed
        used_steps = preprocessing_steps
        logger.info(f"OCR | using preprocessed result (score {score_prep:.2f} vs {score_orig:.2f})")
    else:
        chosen_blocks = blocks_original
        used_steps = []
        logger.info(f"OCR | using original result (score {score_orig:.2f} vs {score_prep:.2f})")

    full_text = "\n".join(b.normalized_text for b in chosen_blocks)
    processing_ms = int((time.monotonic() - start) * 1000)

    _, version = _get_paddle_ocr()

    quality = ImageQuality(
        status=quality_dict["status"],
        blur_score=quality_dict["blur_score"],
        brightness_score=quality_dict["brightness_score"],
        issues=quality_dict["issues"],
    )

    logger.info(
        f"OCR | done | image={image_path} | blocks={len(chosen_blocks)} "
        f"| quality={quality.status} | time={processing_ms}ms"
    )

    return OCRResult(
        image_path=image_path,
        engine="paddleocr",
        engine_version=version,
        blocks=chosen_blocks,
        full_text=full_text,
        processing_time_ms=processing_ms,
        preprocessing_applied=used_steps,
        quality=quality,
    )
