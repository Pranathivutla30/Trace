"""TRACE backend -- FastAPI entrypoint.

Serves standardized TRACE JSON to the frontend. Implements no ML and never
reads raw datasets -- all data arrives through services.data_service.

Run from inside backend/:
    uvicorn main:app --reload
Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import health, api

app = FastAPI(
    title="TRACE API",
    description="Temporal Reasoning & Analysis for Clinical Exploration",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(api.router)
