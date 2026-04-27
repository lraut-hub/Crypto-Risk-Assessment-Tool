# 🕵️‍♂️ Crypto Risk Assessment Tool

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![Llama 3](https://img.shields.io/badge/Llama_3.3-Groq-orange?style=for-the-badge)](https://groq.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-blue?style=for-the-badge)](https://www.trychroma.com/)

A high-precision, modular **Retrieval-Augmented Generation (RAG)** engine designed for deterministic crypto asset risk verification. This tool converts raw blockchain, market, and regulatory data into structured, source-backed signal reports.

---

## 🚀 The Problem
In the volatile crypto landscape, retail traders and compliance teams often struggle with:
- **Information Overload**: Sifting through fragmented data across explorers and social media.
- **Speculative Bias**: LLMs often "hallucinate" advice or provide subjective analysis.
- **Hidden Risks**: Undetected honeypots, predatory taxes, or missing audits in obscure tokens.

**The Solution:** A fact-only, signal-first verification engine that prioritizes precision and transparency over conversational interaction.

---

## 🏗️ Architecture: The 9-Step Pipeline
The system follows a strict, deterministic workflow to ensure every risk report is grounded in verifiable data:

1.  **Query Router**: Classifies intent to block advisory/out-of-scope queries.
2.  **Entity Resolver**: Maps tickers/names to canonical IDs via **CoinGecko**.
3.  **Asset Classifier**: Identifies asset types (Smart Contract vs. Native Asset).
4.  **Signal Engine**: Concurrently fetches data from:
    - **GoPlus Security**: Smart contract vulnerabilities and tax flags.
    - **CoinGecko**: Market liquidity, rank, and exchange listings.
    - **Regulatory Lists**: Daily scraped data from FCA, SEC, and MAS.
5.  **Signal Normalizer**: Converts raw numbers into human-readable indicators (e.g., `⚠️ PREDATORY TAX`).
6.  **RAG Retriever**: Pulls context from **ChromaDB** for signal grounding.
7.  **LLM Explanation**: Uses **Llama 3.3 (Groq)** to generate a 2-3 line factual summary.
8.  **Output Formatter**: Builds a structured Markdown/JSON report.
9.  **Post-Guards**: Final regex check to ensure no advisory language is present.

---

## 🛡️ Key Signal Layers
| Layer | Indicators Tracked |
| :--- | :--- |
| **Structural** | Honeypots, Minting permissions, Proxy/Upgradable contracts, Buy/Sell taxes. |
| **Market** | Market Cap, Trading Volume, Exchange Listings, Market Rank. |
| **Audit** | Security audit status, Verified source code, Known audit providers. |
| **Regulatory** | Warnings from global regulators (FCA, SEC, MAS), Sanctioned status. |

---

## 🛠️ Tech Stack
- **Backend**: FastAPI (Python 3.10+)
- **Frontend**: React 19 + Vite + TypeScript + TailwindCSS
- **AI/LLM**: Groq Cloud (`llama-3.3-70b-versatile`)
- **Vector DB**: ChromaDB (Embeddings: `BAAI/bge-large-en-v1.5`)
- **Data APIs**: GoPlus Security API, CoinGecko API

---

## 🏁 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- API Keys: Groq, CoinGecko (optional), GoPlus

### Installation
1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/lraut-hub/Crypto-Risk-Assessment-Tool.git
    cd Crypto-Risk-Assessment-Tool
    ```
2.  **Backend Setup**:
    ```bash
    cd backend
    pip install -r requirements.txt
    python main.py
    ```
3.  **Frontend Setup**:
    ```bash
    cd ../frontend
    npm install
    npm run dev
    ```

---

## ⚠️ Disclaimer
**Facts-only. No investment advice.**
This tool reports historical and technical signals; it does not predict future performance or guarantee safety. Always perform your own research (DYOR).

---
*Built with precision for the next generation of crypto security.*
