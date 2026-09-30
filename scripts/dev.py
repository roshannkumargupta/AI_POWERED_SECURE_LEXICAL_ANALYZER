"""Development server runner for SecureLex IDE (APSLA).

Starts the FastAPI backend with uvicorn and auto-reload on port 8000,
printing helpful connection information and endpoints.
"""

from __future__ import annotations

import uvicorn


def main() -> None:
    host = "127.0.0.1"
    port = 8000

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
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
