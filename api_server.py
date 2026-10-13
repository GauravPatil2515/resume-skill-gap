# FastAPI bridge exposing the ATS analysis engine to the Next.js frontend.
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make `src` importable so `from ats...` works when run directly.
ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import uvicorn  # noqa: E402
from ats.api import (  # noqa: E402
    ALLOWED_ORIGINS,
    AnalyzeResponse,
    app,
)

__all__ = ["app", "AnalyzeResponse", "ALLOWED_ORIGINS"]

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=False)
