"""
Crypto Risk Verification Assistant — FastAPI Application

Main API entry point. Provides endpoints for:
- Chat-based risk verification queries
- Health checks
- Thread-based conversation management
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import logging
from dotenv import load_dotenv
from backend.services.rag_service import RAGService
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Crypto Risk Verification Assistant API",
    description="Chain-agnostic, identity-first risk signal verification",
    version="2.0.0",
)


# ─── Request / Response Models ────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    risk_profile: Optional[Dict[str, Any]] = None
    thread_id: str
    version: str = "2.0.0"

# ─── Service Instance ────────────────────────────────────────────────────────

rag_service = RAGService()

# ─── CORS Configuration ──────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "message": "Crypto Risk Verification Assistant API is running",
        "version": "2.0.0",
        "architecture": "Chain-agnostic, Identity-first, Multi-layer Risk Engine",
        "pipeline": [
            "Query Router",
            "Entity Resolver (CoinGecko)",
            "Asset Classifier",
            "Signal Engine (Structural + Market + Audit + Regulatory)",
            "Signal Normalizer + Fallback",
            "RAG Retriever (Signal-driven)",
            "LLM Explanation (Groq/Llama)",
            "Output Formatter",
            "Post-Guards",
        ],
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main endpoint for user-assistant interaction.

    Processes the query through the full pipeline:
    Query Router → Entity Resolver → Asset Classifier → Signal Engine →
    Signal Normalizer → RAG Retriever → LLM → Output Formatter → Post-Guards

    Accepts:
    - Token names (e.g., "Bitcoin", "Uniswap")
    - Ticker symbols (e.g., "BTC", "UNI")
    - Contract addresses (e.g., "0x1f9840...")
    - Risk-related questions about specific assets
    """
    # Generate or reuse thread ID
    thread_id = request.thread_id or str(uuid.uuid4())

    response, risk_profile = await rag_service.answer_query(request.message)

    return ChatResponse(
        response=response,
        risk_profile=risk_profile,
        thread_id=thread_id,
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
