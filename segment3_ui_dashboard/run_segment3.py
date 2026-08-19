"""
Segment 3 Interactive Financial Dashboard & AI Review UI CLI.
Launches the FastAPI backend presentation layer (port 8000) and
the React Vite financial audit dashboard (port 5173).
"""

import argparse
import os
import sys
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description="Segment 3 Financial Audit Dashboard & Presentation Server")
    parser.add_argument("--backend-port", type=int, default=8000, help="Port for FastAPI backend (default: 8000)")
    parser.add_argument("--frontend-port", type=int, default=5173, help="Port for Vite frontend (default: 5173)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--backend-only", action="store_true", help="Launch only FastAPI backend daemon")
    parser.add_argument("--frontend-only", action="store_true", help="Launch only Vite React frontend")
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(project_root, "frontend")
    if not os.path.exists(frontend_dir):
        frontend_dir = os.path.join(project_root, "segment3_ui_dashboard", "frontend")

    print("=" * 75)
    print(">>> SEGMENT 3: INTERACTIVE FINANCIAL AUDIT DASHBOARD & AI PRESENTATION LAYER")
    print("=" * 75)
    print(f"[*] Project Root : {project_root}")
    print(f"[*] Backend URL  : http://{args.host}:{args.backend_port}")
    print(f"[*] Frontend URL : http://{args.host}:{args.frontend_port}")
    print("=" * 75)

    processes = []
    try:
        if not args.frontend_only:
            print(f"[+] Launching FastAPI backend on http://{args.host}:{args.backend_port}...")
            p_back = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", args.host, "--port", str(args.backend_port)],
                cwd=project_root
            )
            processes.append(p_back)

        if not args.backend_only:
            print(f"[+] Launching Vite React Dashboard on http://{args.host}:{args.frontend_port}...")
            p_front = subprocess.Popen(
                ["npx", "vite", "--port", str(args.frontend_port), "--host", args.host],
                cwd=frontend_dir
            )
            processes.append(p_front)

        print("\n[✓] Segment 3 services are running! Press Ctrl+C to terminate.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Shutting down Segment 3 services...")
        for p in processes:
            p.terminate()
        for p in processes:
            p.wait()
        print("[✓] Segment 3 services stopped.")


if __name__ == "__main__":
    main()
