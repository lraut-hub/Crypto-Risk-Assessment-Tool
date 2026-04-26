# Problem Statement: Crypto Risk Verification Tool

---

## Overview
The goal is to build a high-precision, modular Retrieval-Augmented Generation (RAG) tool for crypto asset risk assessment. A user submits a token name, ticker, or contract address and the system returns a structured, source-backed risk report derived from four independent signal layers — structural, market, audit, and regulatory.

This is not a chatbot or a prediction engine. It is a deterministic, fact-only analysis tool invocable via API or CLI.

---

## Objective
Design and implement a modular RAG-based analysis engine that:
- Resolves the identity of a queried asset via CoinGecko
- Filters low-quality inputs using a multi-phase Smart-Strict search guardrail
- Retrieves structural, market, audit, and regulatory signals from live APIs and scraped regulatory sources
- Uses a constrained LLM to produce 2-3 neutral, signal-grounded explanatory sentences
- Returns a structured JSON report — no advice, no predictions, no speculative output

---

## Target Users
- Retail traders performing quick due-diligence on unknown tokens
- Compliance teams needing deterministic risk snapshots
- Developers integrating crypto risk checks into their own pipelines
- Security analysts verifying smart contract safety

---

## Scope of Work

### Data Sources
- CoinGecko API — token identity and market data (fetched per query)
- GoPlus Security API — smart contract and audit signals (fetched per query)
- Regulatory Warning Lists — FCA, MAS, SEC (scraped daily)
- Static Knowledge Base — risk terminology definitions embedded in ChromaDB for RAG grounding

### Search Intelligence
The system applies a multi-phase resolution pipeline before processing any query:
- Noise Filter — rejects inputs shorter than 2 characters
- Exact Match — resolves known tickers and names (case-insensitive)
- Smart Alias — matches partial words within a token name
- Fuzzy Match — handles minor misspellings (similarity ≥ 0.85)
- Rank Guard — short queries must resolve to a Top-1000 asset
- Typo Correction — retries with a cleaned query
- Rejection — unresolvable queries return a clear "Not Found" message

### Signal Framework
The engine evaluates every asset across four independent layers:
- **Structural** — Honeypot, minting, proxy, and buy/sell tax flags (EVM tokens via GoPlus)
- **Market** — Market cap, rank, and exchange listing count (CoinGecko, all assets)
- **Audit** — Audit status and provider name (GoPlus; fallback for native assets)
- **Regulatory** — FCA, MAS, and SEC warning flags (scraped regulatory lists, all assets)

Missing data never returns an empty field — it uses a defined fallback string such as "Not applicable for this asset type".

### Refusal Handling
The query router classifies intent before any pipeline processing:
- Factual queries proceed to the full analysis pipeline
- Advisory queries (buy, sell, invest, predict) return a static refusal message
- Out-of-scope queries return a scope-boundary message

Intent classification uses deterministic keyword matching only — no LLM is involved.

---

## Technical Stack
- **Backend** — FastAPI (Python 3.10+)
- **LLM** — Groq Cloud (`llama-3.3-70b-versatile`)
- **Vector DB** — ChromaDB (direct Python client)
- **Embeddings** — `BAAI/bge-large-en-v1.5` (1024 dimensions)
- **Security API** — GoPlus Security
- **Market API** — CoinGecko
- **Frontend (optional)** — React 19 + Vite + TypeScript

---

## Expected Deliverables
- Modular RAG tool — Python package or API endpoint returning a structured JSON risk report
- Search intelligence engine — multi-phase resolver with typo correction and rank guards
- Signal pipeline — 9-step deterministic process (Router → Resolver → Classifier → Signals → Normalizer → RAG → LLM → Formatter → Guards)
- README — setup instructions, architecture overview, data sources, and known limitations
- Disclaimer — "Facts-only. No investment advice."

---

## Known Limitations
- The system reports signals; it does not predict scams or guarantee safety
- Newly listed or obscure tokens may not exist in the CoinGecko index
- GoPlus coverage varies by chain — newer or non-EVM chains may have limited data
- Regulatory lists are updated daily; very recent warnings may not be reflected immediately
- CoinGecko free tier has rate limits that may affect high-traffic usage

---

## Success Criteria
- Accurate identity resolution across names, tickers, and contract addresses
- Reliable rejection of junk or ambiguous queries
- Consistent, structured risk signal output with valid source citations
- Strict adherence to facts-only responses
- Correct refusal of advisory or out-of-scope queries

---

## Summary
The goal is to build a trustworthy, transparent, and compliant crypto risk verification tool that converts raw blockchain, market, and regulatory data into a structured, source-backed signal report. The system prioritizes precision and determinism over conversational interaction, providing rapid due-diligence without advisory bias or speculative content.

---