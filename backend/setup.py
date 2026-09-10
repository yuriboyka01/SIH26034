#!/usr/bin/env python3
"""
setup.py — One-command backend setup for SIH26034.

Usage:
    python setup.py              # Install core deps + run migrations
    python setup.py --full       # Also install OpenCV + OCR (large downloads)

Works on Windows, Linux, and macOS.
Auto-detects and uses Python 3.11/3.12 for PaddleOCR compatibility.
"""

import os
import sys
import shutil
import subprocess

# Safe UTF-8 console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def run(cmd: str, check: bool = True) -> int:
    """Run a shell command, streaming output."""
    print(f"\n{'='*60}")
    print(f"  Running: {cmd}")
    print(f"{'='*60}\n")
    result = subprocess.run(cmd, shell=True)
    if check and result.returncode != 0:
        print(f"\n❌  Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    return result.returncode


def find_compatible_python():
    """Find a Python interpreter between 3.10 and 3.12 (preferably 3.11)."""
    # 1. Try Windows py launcher
    for flag in ["-3.11", "-3.12", "-3.10"]:
        try:
            out = subprocess.check_output(
                f'py {flag} -c "import sys; print(sys.executable)"',
                shell=True,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            if out and os.path.isfile(out):
                return out
        except Exception:
            pass

    # 2. Try direct binary names
    for bin_name in ["python3.11", "python3.12", "python3.10"]:
        try:
            out = subprocess.check_output(
                f'{bin_name} -c "import sys; print(sys.executable)"',
                shell=True,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            if out and os.path.isfile(out):
                return out
        except Exception:
            pass

    # 3. Try common Windows installation locations
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        os.path.join(local_app_data, r"Programs\Python\Python311\python.exe"),
        os.path.join(local_app_data, r"Programs\Python\Python312\python.exe"),
        r"C:\Python311\python.exe",
        r"C:\Python312\python.exe",
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate

    return None


def get_python_version_tuple(python_exe: str):
    """Retrieve the (major, minor) version of a Python executable."""
    try:
        out = subprocess.check_output(
            f'"{python_exe}" -c "import sys; print(f\'{{sys.version_info.major}}.{{sys.version_info.minor}}\')"',
            shell=True,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        parts = [int(p) for p in out.split(".")]
        return tuple(parts)
    except Exception:
        return (0, 0)


def main():
    full_flag = "--full" in sys.argv
    cur_py = sys.version_info[:3]
    print(f"🐍  Host Python: {cur_py[0]}.{cur_py[1]}.{cur_py[2]}")

    # ── 0. If invoked with Python > 3.12, auto-switch to 3.11 if available ───
    if cur_py > (3, 12):
        print(f"⚠️   Detected Python {cur_py[0]}.{cur_py[1]} (PaddleOCR requires Python 3.10–3.12).")
        compat_exe = find_compatible_python()
        if compat_exe and os.path.abspath(compat_exe) != os.path.abspath(sys.executable):
            print(f"🔄  Switching automatically to: {compat_exe}\n")
            cmd = [compat_exe, os.path.abspath(__file__)] + [a for a in sys.argv[1:]]
            res = subprocess.run(cmd)
            sys.exit(res.returncode)

    backend_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(backend_dir, "venv")

    if os.name == "nt":
        venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
        pip = os.path.join(venv_dir, "Scripts", "pip.exe")
        alembic = os.path.join(venv_dir, "Scripts", "alembic.exe")
    else:
        venv_python = os.path.join(venv_dir, "bin", "python")
        pip = os.path.join(venv_dir, "bin", "pip")
        alembic = os.path.join(venv_dir, "bin", "alembic")

    # ── 1. Create or verify virtual environment ──────────────────────────────
    if os.path.isdir(venv_dir) and os.path.isfile(venv_python):
        venv_version = get_python_version_tuple(venv_python)
        if venv_version > (3, 12):
            print(f"⚠️   Existing venv uses Python {venv_version[0]}.{venv_version[1]} (incompatible with PaddleOCR).")
            compat_exe = find_compatible_python()
            if compat_exe:
                print(f"♻️   Recreating venv using Python 3.11 ({compat_exe})...")
                shutil.rmtree(venv_dir, ignore_errors=True)
                run(f'"{compat_exe}" -m venv "{venv_dir}"')
                venv_version = get_python_version_tuple(venv_python)
            else:
                print("⚠️   No Python 3.10–3.12 found to recreate venv. Continuing with existing.")
        else:
            print(f"✅  Virtual environment already exists (Python {venv_version[0]}.{venv_version[1]}).")
    else:
        print("📦  Creating virtual environment...")
        create_py = sys.executable
        if cur_py > (3, 12):
            compat_exe = find_compatible_python()
            if compat_exe:
                create_py = compat_exe
        run(f'"{create_py}" -m venv "{venv_dir}"')
        venv_version = get_python_version_tuple(venv_python)
        print(f"✅  Created virtual environment (Python {venv_version[0]}.{venv_version[1]}).")

    # ── 2. Upgrade packaging tools ───────────────────────────────────────────
    print("📦  Upgrading pip, setuptools, wheel...")
    run(f'"{venv_python}" -m pip install --upgrade pip setuptools wheel', check=False)

    # ── 3. Install core requirements ─────────────────────────────────────────
    print("📥  Installing core dependencies...")
    req_file = os.path.join(backend_dir, "requirements.txt")
    run(f'"{pip}" install -r "{req_file}"')

    # ── 4. Install optional large deps ───────────────────────────────────────
    if full_flag:
        print("📥  Installing OpenCV (image preprocessing)...")
        cv_req = os.path.join(backend_dir, "requirements-cv.txt")
        run(f'"{pip}" install -r "{cv_req}"', check=False)

        # Check venv's Python version for PaddleOCR
        if venv_version <= (3, 12) and venv_version >= (3, 10):
            print("📥  Installing PaddleOCR...")
            ocr_req = os.path.join(backend_dir, "requirements-ocr.txt")
            run(f'"{pip}" install -r "{ocr_req}"', check=False)

            # Verification check
            print("\n🔍  Verifying PaddleOCR engine initialization...")
            chk_script = (
                "import sys; "
                "sys.stdout.reconfigure(encoding='utf-8', errors='replace') if hasattr(sys.stdout, 'reconfigure') else None; "
                "from app.ai.ocr_service import _get_ocr; "
                "instance, ver, eng = _get_ocr(); "
                "print(f'[OK] PaddleOCR engine ({eng} v{ver}) initialized successfully!')"
            )
            res = subprocess.run([venv_python, "-c", chk_script], cwd=backend_dir)
            if res.returncode == 0:
                print("✅  PaddleOCR engine verified and ready.")
            else:
                print("⚠️   PaddleOCR initialization check reported an issue.")
        else:
            print(f"⚠️   Skipping PaddleOCR (venv Python is {venv_version[0]}.{venv_version[1]}; requires Python ≤3.12)")
    else:
        print("ℹ️   Skipping OpenCV/OCR (use --full to install)")

    # ── 5. Run migrations ────────────────────────────────────────────────────
    print("🗃️   Running database migrations...")
    run(f'"{alembic}" upgrade head')

    # ── 6. Done ──────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  ✅  Setup complete!")
    print(f"{'='*60}")
    if os.name == "nt":
        print(f"\n  Activate:  venv\\Scripts\\activate")
    else:
        print(f"\n  Activate:  source venv/bin/activate")
    print(f"  Start:     uvicorn app.main:app --reload --port 8000\n")


if __name__ == "__main__":
    main()
