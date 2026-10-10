"""Development server runner for SecureLex IDE (APSLA).

Starts the FastAPI backend with uvicorn on the local development port,
printing helpful connection information and endpoints.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn


def main() -> None:
    host = "127.0.0.1"
    port = int(os.environ.get("APSLA_API_PORT", "8010"))
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root / "src"))

    print("=" * 60)
    print("  SecureLex IDE (APSLA) - Development API Server")
    print("=" * 60)
    print(f"  Backend API:      http://{host}:{port}/api")
    print(f"  Health Check:     http://{host}:{port}/api/health")
    print(f"  Swagger Docs:     http://{host}:{port}/docs")
    print(f"  ReDoc Docs:       http://{host}:{port}/redoc")
    print("  Front-end (Vite): http://localhost:5173")
    print("=" * 60)
    print("Press Ctrl+C to terminate the server.\n")

    uvicorn.run(
        "apsla.server.app:app",
        host=host,
        port=port,
        # Running the Windows file-watcher spawns a child interpreter. Avoid
        # that indirection so this runner works reliably from packaged/source
        # checkouts; restart the process after backend edits.
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
