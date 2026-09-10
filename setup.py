#!/usr/bin/env python3
"""
setup.py — One-command full-stack project setup for SIH26034.

Sets up both Backend (Python venv, packages, migrations) and
Frontend (npm install).

Usage:
    python setup.py              # Core backend + frontend setup
    python setup.py --full       # Full backend (CV + PaddleOCR) + frontend setup
    python setup.py --backend    # Backend only
    python setup.py --frontend   # Frontend only

Works seamlessly on Windows, Linux, and macOS.
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


def print_banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def setup_backend(root_dir: str, extra_args: list) -> int:
    backend_dir = os.path.join(root_dir, "backend")
    backend_setup = os.path.join(backend_dir, "setup.py")

    if not os.path.isfile(backend_setup):
        print(f"❌ Could not find backend setup script: {backend_setup}")
        return 1

    print_banner("1/2 Setting Up Backend (Python 3.11 + Database)")
    cmd = [sys.executable, backend_setup] + extra_args
    result = subprocess.run(cmd, cwd=backend_dir)
    return result.returncode


def setup_frontend(root_dir: str) -> int:
    frontend_dir = os.path.join(root_dir, "frontend")
    package_json = os.path.join(frontend_dir, "package.json")

    if not os.path.isfile(package_json):
        print(f"❌ Could not find frontend package.json in {frontend_dir}")
        return 1

    print_banner("2/2 Setting Up Frontend (Node.js + React)")

    # Check for npm
    npm_cmd = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm_cmd:
        print("⚠️  'npm' command not found on PATH.")
        print("   Please install Node.js (v18+) from https://nodejs.org/")
        print("   Then run: cd frontend && npm install")
        return 1

    print(f"📦  Installing frontend dependencies using {npm_cmd}...")
    result = subprocess.run(f'"{npm_cmd}" install', cwd=frontend_dir, shell=True)
    if result.returncode != 0:
        print(f"\n❌  Frontend setup failed with exit code {result.returncode}")
        return result.returncode

    print("\n✅  Frontend dependencies installed successfully!")
    return 0


def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))

    backend_only = "--backend" in sys.argv
    frontend_only = "--frontend" in sys.argv

    # Filter out root-specific flags to forward backend flags cleanly
    backend_args = [arg for arg in sys.argv[1:] if arg not in ("--backend", "--frontend")]

    do_backend = not frontend_only
    do_frontend = not backend_only

    print_banner("COMPLIQ — Full-Stack Project Setup")
    target_desc = (
        "Backend only"
        if backend_only
        else "Frontend only"
        if frontend_only
        else "Full-Stack (Backend + Frontend)"
    )
    print(f"Target: {target_desc}\n")

    if do_backend:
        backend_code = setup_backend(root_dir, backend_args)
        if backend_code != 0:
            print("\n❌ Backend setup failed. Halting setup.")
            sys.exit(backend_code)

    if do_frontend:
        frontend_code = setup_frontend(root_dir)
        if frontend_code != 0:
            print("\n❌ Frontend setup encountered issues.")
            sys.exit(frontend_code)

    print_banner("🎉 Full-Stack Setup Complete!")
    print("How to start the project:")
    print("  • Option 1 (One-click launch both servers):")
    if os.name == "nt":
        print("      .\\start_local.ps1")
    else:
        print("      ./start_local.sh")
    print("\n  • Option 2 (Manual startup):")
    if os.name == "nt":
        print("      Backend:   cd backend; .\\venv\\Scripts\\activate; uvicorn app.main:app --reload --port 8000")
    else:
        print("      Backend:   cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000")
    print("      Frontend:  cd frontend && npm run dev")
    print()


if __name__ == "__main__":
    main()
