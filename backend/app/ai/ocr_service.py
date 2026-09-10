"""
OCR service — wraps PaddleOCR and returns normalized OCRResult dataclasses.

Phase 3 (declaration extraction) must depend only on app.ai.models, never on
OCR engine internals directly.

Design:
  - Singleton OCR instance (lazy initialized) to avoid reloading models per request.
  - Two-track strategy: run on original AND preprocessed image, keep the better result
    (more blocks with higher average confidence wins).
  - PaddleOCR is strictly required (requires Python 3.11.x). No fallbacks.
"""

import re
import time
from typing import List, Optional, Tuple
import numpy as np

from app.ai.models import OCRTextBlock, OCRResult, ImageQuality
from app.ai.preprocessing import preprocess_image_path, load_image
from app.core.logging import logger

# ── Exceptions ───────────────────────────────────────────────────────────────

class OCREngineUnavailableError(RuntimeError):
    """Raised when the OCR engine (PaddleOCR) fails to initialize."""
    pass

# ── Engine selection ─────────────────────────────────────────────────────────

_ocr_engine = None          # "paddle" | None
_ocr_instance = None
_ocr_version = "unknown"


def _get_ocr():
    """Return (or create) the shared OCR engine instance.

    Returns:
        Tuple of (instance, version_string, engine_name)
    """
    global _ocr_engine, _ocr_instance, _ocr_version

    if _ocr_instance is not None:
        return _ocr_instance, _ocr_version, _ocr_engine

    try:
        from paddleocr import PaddleOCR
        import paddleocr
        _ocr_version = getattr(paddleocr, "__version__", "unknown")
        logger.info(f"Initialising PaddleOCR (CPU) version={_ocr_version}")
        _ocr_instance = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        _ocr_engine = "paddle"
        return _ocr_instance, _ocr_version, _ocr_engine
    except ImportError as e:
        logger.error(f"Failed to import PaddleOCR: {e}")
        raise OCREngineUnavailableError(
            "PaddleOCR is not available. Please ensure you are running Python 3.11 "
            "and have installed paddlepaddle and paddleocr via the setup script."
        ) from e
    except Exception as e:
        logger.error(f"Failed to initialize PaddleOCR: {e}")
        raise OCREngineUnavailableError(f"PaddleOCR initialization failed: {e}") from e


# ── Text helpers ─────────────────────────────────────────────────────────────

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


# ── PaddleOCR runner ────────────────────────────────────────────────────────

def _run_paddle_on_image(ocr, image: np.ndarray) -> List[OCRTextBlock]:
    """Run PaddleOCR on a BGR numpy array."""
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
    except Exception as e:
        logger.error(f"PaddleOCR inference error: {e}")
    return blocks


# ── Scoring ─────────────────────────────────────────────────────────────────

def _score_blocks(blocks: List[OCRTextBlock]) -> float:
    """Composite score: number of blocks × average confidence."""
    if not blocks:
        return 0.0
    avg_conf = sum(b.confidence for b in blocks) / len(blocks)
    return len(blocks) * avg_conf


# ── Public API ──────────────────────────────────────────────────────────────

def extract(image_path: str) -> OCRResult:
    """Run the full OCR pipeline on an image file."""
    start = time.monotonic()

    # --- Load and preprocess ---
    original, preprocessed, preprocessing_steps, quality_dict = preprocess_image_path(image_path)

    # --- Get engine ---
    try:
        engine, version, engine_name = _get_ocr()
    except OCREngineUnavailableError as e:
        logger.warning(f"OCR | engine unavailable, skipping OCR: {e}")
        return OCRResult(
            image_path=image_path,
            engine="none",
            engine_version="0.0.0",
            blocks=[],
            full_text="",
            processing_time_ms=int((time.monotonic() - start) * 1000),
            preprocessing_applied=preprocessing_steps,
            quality=ImageQuality(
                status=quality_dict["status"],
                blur_score=quality_dict["blur_score"],
                brightness_score=quality_dict["brightness_score"],
                issues=quality_dict["issues"],
            )
        )

    # --- OCR on original ---
    logger.info(f"OCR | running {engine_name} on original image: {image_path}")
    blocks_original = _run_paddle_on_image(engine, original)

    # --- OCR on preprocessed ---
    logger.info(f"OCR | running {engine_name} on preprocessed image: {image_path}")
    blocks_preprocessed = _run_paddle_on_image(engine, preprocessed)

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

    quality = ImageQuality(
        status=quality_dict["status"],
        blur_score=quality_dict["blur_score"],
        brightness_score=quality_dict["brightness_score"],
        issues=quality_dict["issues"],
    )

    logger.info(
        f"OCR | done | image={image_path} | engine={engine_name} | blocks={len(chosen_blocks)} "
        f"| quality={quality.status} | time={processing_ms}ms"
    )

    return OCRResult(
        image_path=image_path,
        engine=engine_name,
        engine_version=version,
        blocks=chosen_blocks,
        full_text=full_text,
        processing_time_ms=processing_ms,
        preprocessing_applied=used_steps,
        quality=quality,
    )
