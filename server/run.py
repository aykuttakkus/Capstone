from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def main(host: str | None = None, port: str | None = None) -> None:
    print("=" * 60)
    print("🚀 Starting Calma backend (FastAPI)...")
    print("=" * 60)

    repo_root = Path(__file__).resolve().parent.parent
    venv_python = repo_root / ".venv" / "bin" / "python"

    if venv_python.exists():
        py_executable = str(venv_python)
        print("   [System] Using Python from virtual environment (.venv)")
    else:
        py_executable = sys.executable
        print("   [System] Warning: No .venv found. Using system Python.")

    backend_host = host or os.getenv("BACKEND_HOST", "127.0.0.1")
    backend_port = port or os.getenv("BACKEND_PORT", "8000")
    reload_enabled = _env_flag("RELOAD", True)

    command = [py_executable, "-m", "uvicorn", "server.app.main:app", "--host", backend_host, "--port", backend_port]
    if reload_enabled:
        command.append("--reload")

    process = subprocess.Popen(command, cwd=str(repo_root))

    print("=" * 60)
    print("✨ Backend is running ✨")
    print(f"👉 Backend API running at: http://{backend_host}:{backend_port}")
    print(f"👉 Reload mode: {'on' if reload_enabled else 'off'}")
    print("👉 Run the frontend separately: cd client && npm run dev")
    print("Press Ctrl+C to stop the server.")
    print("=" * 60)

    try:
        process.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 KeyboardInterrupt received. Shutting down server...")
        process.terminate()
        process.wait()
        print("✅ Gracefully exited.")


if __name__ == "__main__":
    main()
