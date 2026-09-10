import sys
import argparse

def doctor():
    print("COMPLIQ Environment Doctor")
    print("----------------------------\n")

    healthy = True
    PASS = "[PASS]"
    FAIL = "[FAIL]"

    # 1. Check Python version
    version = sys.version_info
    py_version = f"{version.major}.{version.minor}.{version.micro}"
    if version.major == 3 and version.minor == 11:
        print(f"{'Python':<20} {py_version:<12} {PASS}")
    else:
        print(f"{'Python':<20} {py_version:<12} {FAIL} (Requires 3.11.x)")
        healthy = False

    # 2. Check Virtual Environment
    is_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if is_venv:
        print(f"{'Virtual Environment':<20} {'Active':<12} {PASS}")
    else:
        print(f"{'Virtual Environment':<20} {'Inactive':<12} {FAIL}")
        healthy = False

    print()

    # 3. Check PaddlePaddle
    try:
        import paddle
        print(f"{'PaddlePaddle':<20} {paddle.__version__:<12} {PASS}")
    except ImportError:
        print(f"{'PaddlePaddle':<20} {'Missing':<12} {FAIL}")
        healthy = False

    # 4. Check PaddleOCR
    try:
        import paddleocr
        print(f"{'PaddleOCR':<20} {paddleocr.__version__:<12} {PASS}")
    except ImportError:
        print(f"{'PaddleOCR':<20} {'Missing':<12} {FAIL}")
        healthy = False

    print()

    # 5. Check Engine Initialization
    if healthy:
        try:
            from app.ai.ocr_service import _get_ocr
            instance, engine_version, engine_name = _get_ocr()
            print(f"{'OCR Engine':<20} {engine_name:<12} {PASS}")
            print(f"{'OCR Initialization':<20} {'Successful':<12} {PASS}")
        except Exception as e:
            print(f"{'OCR Initialization':<20} {'Failed':<12} {FAIL}")
            print(f"\nError: {e}")
            healthy = False

    print("\n----------------------------")
    if healthy:
        print("Environment Status: HEALTHY")
    else:
        print("Environment Status: FAILED\n")
        print("Problems detected. Recommended fix:")
        print("    .\\setup_environment.ps1")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="COMPLIQ CLI")
    parser.add_argument("command", choices=["doctor"], help="Command to run")
    args = parser.parse_args()

    if args.command == "doctor":
        doctor()
