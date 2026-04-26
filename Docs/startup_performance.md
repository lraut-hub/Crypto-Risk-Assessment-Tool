# Startup Performance Analysis

## 🚀 Current Startup Times
- **Backend (API)**: ~15-20 seconds
- **Frontend (Vite)**: ~1-2 seconds

## 🔍 Bottleneck Analysis

### 1. Backend: Large Language Model & Embeddings
The primary bottleneck is the initialization of the `BGE-large-en-v1.5` embedding model.
- **Size**: ~1.5 GB
- **Loading Logic**: The model is loaded into memory when the `RAGService` is instantiated. Because this happens at the module level in `backend/main.py`, the entire FastAPI application must wait for the model to load before it can start accepting requests.
- **Hardware**: Currently running on **CPU**. Loading and initializing such a large model on a CPU is significantly slower than on a GPU.

### 2. Backend: Service Chain Initialization
The `RAGService` also initializes several other components sequentially:
- `CoinGeckoService` (External API check)
- `ChromaDB` (Local vector database connection)
- `GroqService` (LLM API initialization)

## 💡 Proposed Solutions

### A. Lazy Loading (Immediate)
We can move the embedding model initialization inside the first request handler or use a background task. This allows the API to start immediately (reporting "starting up" or "healthy" for simple endpoints) while the heavy model loads in the background.

### B. Smaller Model (Performance Trade-off)
Swap `bge-large-en-v1.5` for `bge-small-en-v1.5`.
- **Large**: 1.5GB, slower, higher precision.
- **Small**: ~100MB, significantly faster, slightly lower precision.

### C. Hosted Embedding API (Infrastructure)
Instead of running the embedding model locally on CPU, we could use an API (like Voyage AI, OpenAI, or a self-hosted instance on a GPU server). This would reduce startup time to < 1 second.

### D. Model Caching / Persistent Shared Memory
If running multiple worker processes, ensure the model is loaded once in shared memory rather than once per worker.

---

## 🛠️ Execution Log: Restart Sequence
- **Backend Start**: 12:00:43 UTC
- **Frontend Start**: 12:00:50 UTC
- **Ready Status**: 12:01:15 UTC (Total Wait: ~32 seconds)
