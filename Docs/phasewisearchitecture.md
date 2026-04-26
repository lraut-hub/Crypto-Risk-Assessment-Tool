# Crypto Risk Analysis Tool — Architecture & Phase-wise Implementation

This document outlines the architectural blueprint for the **Crypto Risk Analysis Tool** — a **chain-agnostic, identity-first, signal-driven risk verification system**.

The system is a **Deterministic Risk Intelligence Engine** that produces structured, source-backed outputs. It operates as a **single-shot analysis tool** — not a chatbot.

> **Core Principle**: Signals are computed from live APIs. The LLM only explains signals — it never generates them.

> **Delivery Paradigm**: Reusable Modular RAG tool, invocable via API or CLI, returning structured JSON reports.

---

## Design Principles

| # | Principle | Description |
|:--|:---|:---|
| 1 | **Identity-first processing** | All inputs resolved via CoinGecko before any logic. Canonical asset object is single source of truth. |
| 2 | **Search intelligence** | Multi-phase matching (exact → alias → fuzzy) with noise filters and rank guards. |
| 3 | **Chain-agnostic coverage** | Adapts based on asset type (EVM vs native). Structural signals only when applicable. |
| 4 | **Deterministic signals** | Derived only from APIs (CoinGecko, GoPlus) or verified sources. No LLM inference. |
| 5 | **Fixed signal schema** | Every response includes: Structural, Market, Audit, Regulatory. Never omitted. |
| 6 | **Graceful fallback** | Missing data explicitly labeled. System never returns empty or vague responses. |
| 7 | **Tool-first Architecture** | Single-shot analysis tool. No chat turns, no conversation history, no thread management. |
| 8 | **Accuracy over completeness** | Prefer "Not available" over approximation. |
| 9 | **No advisory output** | No predictions, recommendations, or subjective judgments. |
| 10 | **Separation of concerns** | Identity, search guards, signal computation, normalization, and explanation are independent layers. |

---

## End-to-End System Flow

```
User Input (Search Bar)
    │
    ▼
┌─────────────────────────┐
│   Query Router           │──── Advisory/Out-of-scope? → Static Refusal
│   (Intent Classifier)    │
└────────┬────────────────┘
         │ Factual
         ▼
┌─────────────────────────┐
│   Search Guardrails      │──── Noise Filter → Exact → Alias → Fuzzy → Rank Guard
│   (Smart-Strict Engine)  │──── Typo Correction (retry with cleaned query)
└────────┬────────────────┘
         │ Validated Query
         ▼
┌─────────────────────────┐
│   Entity Resolver        │──── CoinGecko (search → coin info → contract lookup)
│   (Identity Layer)       │
└────────┬────────────────┘
         │ Canonical Asset Object
         ▼
┌─────────────────────────┐
│   Asset Classifier       │──── smart_contract_token | native_asset | low_data_asset
└────────┬────────────────┘
         │ Applicable Layers
         ▼
┌─────────────────────────┐
│   Signal Engine          │──── Market (CoinGecko) + Structural/Audit (GoPlus) + Regulatory
│   (Multi-Layer)          │
└────────┬────────────────┘
         │ Raw Signals
         ▼
┌─────────────────────────┐
│   Signal Normalizer      │──── Standardized signals + explicit fallback values
│   + Fallback Handler     │
└────────┬────────────────┘
         │ Normalized Signals
         ▼
┌─────────────────────────┐
│   RAG Retriever          │──── Signal-driven queries → top-k chunks from knowledge base
└────────┬────────────────┘
         │ Retrieved Context
         ▼
┌─────────────────────────┐
│   LLM Layer              │──── Explanation only (Groq / Llama 3.3 70B)
└────────┬────────────────┘
         │ Raw Response
         ▼
┌─────────────────────────┐
│   Output Formatter       │──── Signal Report → Explanation → Source → Timestamp
└────────┬────────────────┘
         │ Formatted Response
         ▼
┌─────────────────────────┐
│   Post-Guards            │──── Structural validation + forbidden pattern blocking
└────────┬────────────────┘
         │
         ▼
   API/CLI Output (Structured JSON Report)
```

---

## Data Sources & Integration Strategy

### Active Sources

| Layer | Source | Type | Usage |
|:---|:---|:---|:---|
| **Identity + Market** | [CoinGecko](https://www.coingecko.com/en/api/documentation) | Free API (no key) | Entity resolution, market cap, rank, exchange count |
| **Structural + Audit** | [GoPlus Security](https://gopluslabs.io/) | Free API (no key) | Honeypot, minting, proxy, tax, audit status (multi-chain) |
| **Regulatory** | [FCA](https://www.fca.org.uk/scamsmart/warning-list), [MAS](https://www.mas.gov.sg/investor-alert-list), [SEC](https://www.investor.gov/) | Scraping | Warning / alert detection |
| **Explanation Grounding** | [Investopedia](https://www.investopedia.com/) | Embedded once | Definitions for risk concepts (RAG corpus) |

### CoinGecko Endpoints (Free, No API Key)

| Endpoint | Purpose |
|:---|:---|
| `/api/v3/search?query={input}` | Identity resolution — map user input to token ID |
| `/api/v3/coins/{id}` | Core data — full token details |
| `/api/v3/coins/{platform}/contract/{address}` | Contract-based lookup |

### GoPlus Security Signals

| Signal | Field | Risk Implication |
|:---|:---|:---|
| Honeypot | `is_honeypot` | Token cannot be sold after purchase |
| Minting | `is_mintable` | Owner can create unlimited supply |
| Proxy | `is_proxy` | Contract logic can be changed |
| Buy Tax | `buy_tax` | Hidden fee on purchases |
| Sell Tax | `sell_tax` | Hidden fee on sales |
| Audit | `is_audited` | External code review status |

### Excluded Sources

- Event calendars, social media, blogs, duplicate aggregators, news feeds

---

## Phase 1: Project Foundation

### 1.1 Technical Stack

| Component | Technology |
|:---|:---|
| **Backend** | FastAPI (Python 3.10+) |
| **Orchestration** | Direct SDK usage (no LangChain) |
| **Vector DB** | ChromaDB (Direct Python Client) |
| **Embeddings** | `BAAI/bge-large-en-v1.5` (1024 dimensions) |
| **LLM** | Groq Cloud — `llama-3.3-70b-versatile` |
| **Frontend** | React 19 + Vite + TypeScript + Vanilla CSS |
| **Animations** | Framer Motion |
| **Icons** | Lucide React |
| **HTTP Client** | httpx (async) |

### 1.2 Project Structure

```
crypto-risk-dashboard/
├── backend/
│   ├── main.py                          # FastAPI entry point (single /api/v1/chat endpoint)
│   ├── requirements.txt
│   ├── prompts/
│   │   └── assistant_prompts.py         # System prompt + RAG templates
│   ├── services/
│   │   ├── coingecko_service.py         # CoinGecko API + Search Guardrails
│   │   ├── entity_resolver.py           # Identity resolution layer
│   │   ├── asset_classifier.py          # Asset type classification
│   │   ├── goplus_service.py            # GoPlus Security API wrapper
│   │   ├── rag_service.py               # Main 9-step pipeline orchestrator
│   │   ├── signal_normalizer.py         # Raw → standardized signals
│   │   ├── query_router.py              # Intent classification (factual/advisory/OOS)
│   │   ├── output_formatter.py          # Fixed response schema enforcer
│   │   ├── post_guards.py               # Structural + pattern validation
│   │   ├── chroma_service.py            # ChromaDB interface
│   │   ├── groq_service.py              # LLM interface (Groq/Llama)
│   │   └── audit_detector.py            # Audit status detection
│   └── utils/
│       └── embeddings.py                # BGE embedding wrapper
├── frontend/                             # Optional UI consumer
│   └── src/
│       ├── App.tsx                       # Root: state management, view routing
│       ├── index.css                     # Design system (CSS variables, themes)
│       ├── components/                   # UI components for displaying signals
│       └── services/
│           └── api.ts                    # Backend API client
├── scripts/                              # Scheduled data pipeline
├── data/                                 # ChromaDB + raw/processed data
├── Docs/
│   ├── phasewisearchitecture.md          # This document
│   └── improvements.md                   # Strategy reference
└── problemstatement.md
```

---

## Phase 2: Search Intelligence & Guardrails

This is a **new phase** added to ensure the system rejects noise and only processes high-confidence queries.

### 2.1 Multi-Phase Search Resolution

The CoinGecko search endpoint returns fuzzy results by default. Without guardrails, a query like "v" or "xyzabc" would return random low-rank tokens. The system implements:

```
User Query
    │
    ├── len < 2? → REJECT (Noise Filter)
    │
    ├── CoinGecko /search → 0 results?
    │       ├── Strip repeated trailing chars ("Bitcoinn" → "Bitcoin") → RETRY
    │       └── Trim last char ("Ethereumm" → "Ethereum") → RETRY
    │       └── Still 0? → REJECT with "Not Found" message
    │
    ├── PHASE 1: Exact ticker/name match? → ACCEPT
    │
    ├── PHASE 2: Query is a word in token name? (Smart Alias)
    │       └── Short (≤3 chars) + Rank > 1000? → REJECT (Rank Guard)
    │       └── Otherwise → ACCEPT
    │
    ├── PHASE 3: Fuzzy similarity ≥ 0.85? (SequenceMatcher)
    │       └── Short (≤3 chars) + Rank > 1000? → REJECT (Rank Guard)
    │       └── Otherwise → ACCEPT
    │
    └── Score < 0.85 → REJECT with "Not Found" message
```

### 2.2 Guardrail Examples

| Input | Phase | Result | Reason |
|:---|:---|:---|:---|
| `"v"` | Noise Filter | ❌ Rejected | Single character |
| `"Bitcoin"` | Phase 1 | ✅ Accepted | Exact name match |
| `"BTC"` | Phase 1 | ✅ Accepted | Exact ticker match |
| `"Ether"` | Phase 2 | ✅ Accepted | Word in "Ethereum" |
| `"Bitcoinn"` | Retry + Phase 1 | ✅ Accepted | Cleaned to "Bitcoin" |
| `"xyzabc123"` | Phase 3 | ❌ Rejected | Score < 0.85 |
| `"op"` (Optimism) | Phase 1 | ✅ Accepted | Exact ticker, Rank #30 |

### 2.3 Rejection Response

When search fails: *"Asset not found in our database. Please check the spelling or search using a contract address (0x...)."*

---

## Phase 3: Entity Resolution & Asset Classification

### 3.1 Entity Resolver

Uses CoinGecko APIs to map validated input into a **Canonical Asset Object**:

```python
CanonicalAsset(
    asset_id="uniswap",
    name="Uniswap",
    symbol="UNI",
    chain="ethereum",
    contract_address="0x1f98...",
    platforms={"ethereum": "0x1f98...", "polygon-pos": "0x..."},
    market_cap_rank=22,
    market_cap=5400000000,
    total_volume=120000000,
    homepage="https://uniswap.org",
    exchange_count=45,
    market_presence="Established",
    resolved=True,
)
```

### 3.2 Asset Classifier

| Asset Type | Criteria | Applicable Layers |
|:---|:---|:---|
| `smart_contract_token` | Has contract on EVM chain | Structural ✓ Market ✓ Audit ✓ Regulatory ✓ |
| `native_asset` | BTC, ETH, XRP, SOL (no contract) | Market ✓ Audit (fallback) ✓ Regulatory ✓ |
| `low_data_asset` | Minimal data (no rank, low volume) | Market (limited) ✓ Regulatory ✓ |

---

## Phase 4: Multi-Layer Signal Engine

### 4.1 Structural Layer (EVM only — via GoPlus)

| Signal | Source | Normalization |
|:---|:---|:---|
| Honeypot | GoPlus `is_honeypot` | `"Honeypot detected"` or `"No honeypot risk"` |
| Minting Authority | GoPlus `is_mintable` | `"Owner can mint tokens"` or `"No minting authority"` |
| Proxy Contract | GoPlus `is_proxy` | `"Proxy contract detected"` or `"No proxy"` |
| Buy/Sell Tax | GoPlus `buy_tax`/`sell_tax` | Percentage values |

### 4.2 Market Layer (All assets — via CoinGecko)

| Signal | Source | Normalization |
|:---|:---|:---|
| Listing Presence | CoinGecko search | `"Listed on CoinGecko"` or `"Not found"` |
| Market Cap + Rank | `/coins/{id}` | `"Market Cap: $X (Rank #Y)"` |
| Exchange Count | `/coins/{id}` tickers | `"Listed on X exchanges"` |

### 4.3 Audit Layer (via GoPlus + Cache)

| Signal | Source | Normalization |
|:---|:---|:---|
| Audit Status | GoPlus `is_audited` | `"Audited by [Provider]"` or `"No audit found"` |

GoPlus results are **cached in ChromaDB** using a Cache-Aside pattern to avoid redundant API calls.

### 4.4 Regulatory Layer (Scraped — daily refresh)

| Signal | Source | Normalization |
|:---|:---|:---|
| FCA Warning | FCA warning list | `"FCA warning detected"` or `"No FCA warnings"` |
| MAS Alert | MAS investor alert | `"MAS alert detected"` or `"No MAS alerts"` |
| SEC Alert | SEC bulletins | `"SEC alert detected"` or `"No SEC alerts"` |

---

## Phase 5: Signal Normalization & Fallback

### 5.1 Normalization Rules

| Raw Data | Normalized Output |
|:---|:---|
| `contract_address: None` | `"Asset Type: Native blockchain asset"` |
| `market_cap: 32000000` | `"Market Cap: $32.0M"` |
| `exchange_count: 5` | `"Exchange Listings: 5"` |
| `is_honeypot: true` | `"⚠️ Honeypot detected"` |

### 5.2 Graceful Fallback

| Condition | Fallback Value |
|:---|:---|
| No contract address | Structural → `"Not applicable for this asset type"` |
| No audit data | Audit → `"No audit found"` |
| No regulatory match | Regulatory → `"No regulatory warnings found"` |
| Entity not resolved | → `"Asset not found in our database..."` |

---

## Phase 6: RAG & LLM Explanation

### 6.1 Signal-Driven Retrieval

RAG is used **only to explain detected signals** — not for generic crypto education.

- Retrieval queries constructed from **normalized signals**, not raw user input
- ChromaDB knowledge base contains curated risk definitions
- Context compressed to max **500 tokens** per query

### 6.2 LLM Constraints (Groq / Llama 3.3 70B)

- **Role**: Summarize observed signals in 2–3 factual sentences
- **Forbidden**: "suggests", "indicates", "appears", "likely", "potential"
- **No inference**: Only reports what is explicitly in the signals
- **No education**: Definitions handled by the client application or optional UI layer

---

## Phase 7: Output & Post-Guards

### 7.1 Output Schema

```
Risk Signal Report: [Asset Name]

📋 Asset Profile — ID, Type, Address, Market Cap, Rank, Exchanges
🔍 Smart Contract Risk — Honeypot, Minting, Proxy, Tax (EVM only)
📊 Market Risk — Cap, Rank, Listings
🛡️ Verification — Audit status, Regulatory warnings
💬 Explanation — 2-3 factual sentences
📎 Source + Timestamp
```

### 7.2 Post-Guards

| Check | Action |
|:---|:---|
| All 4 signal categories present | Block if missing → trigger fallback |
| Forbidden patterns detected | Block advice, comparisons, speculation |
| Missing source citation | Inject default source URL |

---

## Phase 8: API & Output Delivery

### 8.1 API Endpoint

- **Route**: `POST /api/v1/analyze`
- **Input**: JSON payload with `query` (string)
- **Output**: Structured JSON report containing all 4 signal layers, LLM explanation, and citations

### 8.2 Client Integration (Optional UI)

While the core system is an API tool, an optional frontend can consume the endpoint to display:
- **Signal Visualization**: Mapping JSON data to color-coded cards (e.g., Red for High Risk, Green for Clear)
- **Search Interface**: A simple input field to pass queries to the backend
- **State Management**: Managing loading states and rendering the returned structured report

---

## Phase 9: Evaluation & Benchmarking

### 9.1 Metrics

| Metric | Target |
|:---|:---|
| **Search Precision** | Correct resolution for exact, alias, and fuzzy inputs |
| **Signal Coverage** | 100% responses contain all 4 categories |
| **Tokens-Per-Query** | < 400 total tokens |
| **Refusal Accuracy** | Correct handling of advisory queries |

### 9.2 Coverage Matrix

| Asset Type | Structural | Market | Audit | Regulatory |
|:---|:---|:---|:---|:---|
| **EVM tokens** | ✅ Full (GoPlus) | ✅ Full | ✅ Full (GoPlus) | ✅ Full |
| **Native assets** | ⬜ N/A fallback | ✅ Full | ⚠️ Fallback | ✅ Full |
| **New tokens** | ⚠️ Limited | ⚠️ Limited | ⚠️ Fallback | ✅ Full |

---

## Summary

This architecture ensures the system:

1. **Resolves identity with precision** — multi-phase search with noise filters, alias support, and rank guards
2. **Produces consistent, structured outputs** — fixed 4-category signal schema, never omitted
3. **Avoids noise and junk results** — Smart-Strict matching rejects low-confidence queries
4. **Maintains facts-only design** — LLM explains signals, never generates them
5. **Delivers a reliable tool experience** — structured JSON output, easy API/CLI integration
6. **Uses live, high-trust sources** — CoinGecko + GoPlus for real-time data, scraped regulators for warnings
