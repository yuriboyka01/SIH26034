"""
Structured application logging.

Logs authentication events, inspection creation, image upload/delete, and errors.
Never logs passwords, JWT tokens, or sensitive credentials.
"""

import logging
import sys

# Create application logger
logger = logging.getLogger("sih26034")
logger.setLevel(logging.INFO)

# Console handler with structured format
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
handler.setFormatter(formatter)

# Avoid duplicate handlers on reload
if not logger.handlers:
    logger.addHandler(handler)


def log_auth_event(event: str, email: str, success: bool = True):
    """Log authentication events (login, register) without sensitive data."""
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"AUTH | {event} | email={email} | status={status}")


def log_inspection_event(event: str, inspection_id: str, user_id: str = ""):
    """Log inspection lifecycle events."""
    logger.info(f"INSPECTION | {event} | id={inspection_id} | user={user_id}")


def log_image_event(event: str, image_id: str, inspection_id: str):
    """Log image upload/delete events."""
    logger.info(f"IMAGE | {event} | image_id={image_id} | inspection_id={inspection_id}")
