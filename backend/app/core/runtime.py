import sys

def verify_runtime():
    """Verify that the backend is running under Python 3.11.x."""
    version = sys.version_info
    if version.major != 3 or version.minor != 11:
        current_version = f"{version.major}.{version.minor}.{version.micro}"
        error_msg = (
            f"\n\n==================================================\n"
            f"COMPLIQ OCR ENGINE ERROR\n"
            f"==================================================\n\n"
            f"COMPLIQ requires Python 3.11.x for the PaddleOCR runtime.\n\n"
            f"Current Python version: {current_version}\n\n"
            f"Please recreate the backend environment using:\n"
            f"    .\\setup_environment.ps1\n\n"
            f"==================================================\n"
        )
        print(error_msg, file=sys.stderr)
        sys.exit(1)
