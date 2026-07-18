"""
backend/main.py
================
FastAPI application entry point for Nyaya Tarazu.
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from backend.routers import extract, retrieve, generate, export, lookup

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(
    title="Nyaya Tarazu API",
    description=(
        "RAG-grounded dual-brief legal drafting assistant for Indian criminal law. "
        "Grounds every argument in retrieved statutory sections from BNS/BNSS/BSA (new code) "
        "or IPC/CrPC/Indian Evidence Act (old code)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — allow React frontend
# ---------------------------------------------------------------------------
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://localhost:3000", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(extract.router)
app.include_router(retrieve.router)
app.include_router(generate.router)
app.include_router(export.router)
app.include_router(lookup.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["meta"])
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "nyaya-tarazu-api", "version": "1.0.0"})


@app.get("/", tags=["meta"])
async def root() -> JSONResponse:
    return JSONResponse({
        "name": "Nyaya Tarazu API",
        "docs": "/docs",
        "endpoints": [
            "POST /extract-facts",
            "POST /retrieve",
            "POST /generate-brief",
            "POST /export",
            "POST /lookup",
        ],
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
