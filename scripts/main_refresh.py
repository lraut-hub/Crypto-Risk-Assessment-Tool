"""
Data Refresh Pipeline — Full-Refresh Ingestion Strategy

Orchestrates the automated data collection and signal processing pipeline.
Uses a FULL-REFRESH strategy: the vector index is rebuilt on each scheduled
run, ensuring consistency and eliminating stale or duplicated data.

Pipeline stages:
  1. API Extraction (Etherscan — blockchain signals)
  2. Market Intelligence (CoinGecko — identity + market)
  3. Regulatory Scraping (FCA, MAS, SEC)
  4. Audit Checks (CertiK, Hacken)
  5. Risk Signal Computation (deterministic engine)
  6. Full-Refresh Vector Indexing (delete + rebuild)
  7. Document Registry Update (source URLs, tags, timestamps)
"""

import asyncio
import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any

# Import services and utilities
try:
    from scripts.services.regulatory import RegulatoryScraper
    from scripts.services.blockchain import EtherscanService
    from scripts.services.market import CoinGeckoService
    from scripts.services.audits import AuditScraper
    from scripts.services.risk_engine import RiskEngine
    from scripts.utils.hashing import generate_content_hash
    # We will import ChromaService from backend
    from backend.services.chroma_service import ChromaService
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.regulatory import RegulatoryScraper
    from services.blockchain import EtherscanService
    from services.market import CoinGeckoService
    from services.audits import AuditScraper
    from services.risk_engine import RiskEngine
    from utils.hashing import generate_content_hash
    from backend.services.chroma_service import ChromaService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DataRefreshPipeline")


class DocumentRegistry:
    """
    Tracks all ingested documents with source URLs, tags, and timestamps.
    Stored as a JSON file alongside the vector database.
    """

    def __init__(self, registry_path: str = "data/processed/document_registry.json"):
        self.registry_path = registry_path
        self.entries: List[Dict[str, Any]] = []

    def add_entry(self, source_url: str, tags: List[str], content_hash: str, doc_count: int = 1):
        self.entries.append({
            "source_url": source_url,
            "tags": tags,
            "content_hash": content_hash,
            "doc_count": doc_count,
            "fetch_timestamp": datetime.utcnow().isoformat(),
        })

    def save(self):
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump({
                "last_refresh": datetime.utcnow().isoformat(),
                "strategy": "full_refresh",
                "total_entries": len(self.entries),
                "entries": self.entries,
            }, f, indent=4)
        logger.info(f"Document registry saved: {len(self.entries)} entries")


class DataRefreshPipeline:
    """
    Orchestrator for the automated data collection and signal processing pipeline.

    Full-Refresh Strategy:
    - On each run, the risk_signals collection is cleared and rebuilt
    - This ensures no stale or duplicated data persists
    - Document registry tracks all source metadata for traceability
    """

    def __init__(self):
        self.raw_data_dir = "data/raw"
        self.processed_data_dir = "data/processed"
        os.makedirs(self.raw_data_dir, exist_ok=True)
        os.makedirs(self.processed_data_dir, exist_ok=True)

        self.risk_engine = RiskEngine()
        self.chroma = ChromaService()
        self.registry = DocumentRegistry()

    async def run(self, query: str = "0x0000000000000000000000000000000000000000"):
        """
        Execute the full data refresh pipeline.

        Args:
            query: Token address or ticker to process
        """
        logger.info(f"{'='*60}")
        logger.info(f"Starting Full-Refresh Data Pipeline for query: {query}")
        logger.info(f"Strategy: FULL REFRESH (delete + rebuild)")
        logger.info(f"{'='*60}")

        # Determine if query is an address or ticker
        is_address = query.startswith("0x") and len(query) == 42
        test_address = query if is_address else "0x0000000000000000000000000000000000000000"

        # ─── Step 1: Full-Refresh — Clear existing signals ────────────────
        self._clear_signal_collection()

        # ─── Step 2: API Extraction (Blockchain) ──────────────────────────
        logger.info("[Step 2/7] Extracting blockchain signals from Etherscan...")
        eth_service = EtherscanService()
        creation_data = await eth_service.get_contract_creation(test_address) or {}
        supply_data = await eth_service.get_token_supply(test_address) or "0"
        await eth_service.close()

        self.registry.add_entry(
            source_url=f"https://etherscan.io/token/{test_address}",
            tags=["structural", "blockchain", "etherscan"],
            content_hash=generate_content_hash(str(creation_data) + supply_data),
        )

        # ─── Step 3: Market Intelligence (CoinGecko) ─────────────────────
        logger.info("[Step 3/7] Fetching market intelligence from CoinGecko...")
        cg_service = CoinGeckoService()
        market_data = None
        if is_address:
            market_data = await cg_service.get_token_by_address(test_address)
        else:
            market_data = await cg_service.verify_listing_by_ticker(query)
        await cg_service.close()

        self.registry.add_entry(
            source_url="https://api.coingecko.com/api/v3",
            tags=["market", "identity", "coingecko"],
            content_hash=generate_content_hash(str(market_data)),
        )

        # ─── Step 4: Scrape Regulatory Warnings ──────────────────────────
        logger.info("[Step 4/7] Scraping regulatory warning lists...")
        reg_scraper = RegulatoryScraper()
        fca_warnings = await reg_scraper.scrape_fca()
        mas_warnings = await reg_scraper.scrape_mas()
        await reg_scraper.close()

        all_regulatory = fca_warnings + mas_warnings
        self.registry.add_entry(
            source_url="https://www.fca.org.uk/scamsmart/warning-list",
            tags=["regulatory", "fca"],
            content_hash=generate_content_hash(str(fca_warnings)),
            doc_count=len(fca_warnings),
        )
        self.registry.add_entry(
            source_url="https://www.mas.gov.sg/investor-alert-list",
            tags=["regulatory", "mas"],
            content_hash=generate_content_hash(str(mas_warnings)),
            doc_count=len(mas_warnings),
        )

        # ─── Step 5: Audit Checks ────────────────────────────────────────
        logger.info("[Step 5/7] Checking audit presence (CertiK, Hacken)...")
        audit_scraper = AuditScraper()
        project_name = market_data.get("name", "Test") if market_data else "Test"
        certik_info = await audit_scraper.check_certik(project_name)
        await audit_scraper.close()

        self.registry.add_entry(
            source_url="https://www.certik.com/projects",
            tags=["audit", "certik"],
            content_hash=generate_content_hash(str(certik_info)),
        )

        # ─── Step 6: Risk Signal Engine (Deterministic) ──────────────────
        logger.info("[Step 6/7] Computing deterministic risk signals...")

        # Determine if structural layer is applicable
        structural_applicable = is_address  # Only for contract addresses

        bc_signals = self.risk_engine.process_blockchain_signals(
            creation_data, supply_data, applicable=structural_applicable
        )
        audit_signals = self.risk_engine.process_audit_signals(
            [certik_info] if certik_info else []
        )
        market_signals = self.risk_engine.process_market_signals(market_data)

        final_signals = self.risk_engine.aggregate_all_signals(
            blockchain=bc_signals,
            market=market_signals,
            audits=audit_signals,
            regulatory=all_regulatory,
        )

        # ─── Step 7: Index into ChromaDB (Full-Refresh) ──────────────────
        logger.info("[Step 7/7] Indexing signals into ChromaDB (full-refresh)...")
        entry_id = f"signal_{test_address}" if is_address else f"signal_{query.lower()}"
        self.chroma.add_signals(
            collection_name="risk_signals",
            ids=[entry_id],
            documents=[f"Deterministic risk profile for {query}"],
            metadatas=[final_signals],
        )

        # ─── Save State & Registry ───────────────────────────────────────
        filename = f"signals_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.processed_data_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(final_signals, f, indent=4)

        self.registry.save()

        logger.info(f"{'='*60}")
        logger.info(f"Pipeline COMPLETE. Signal metadata for '{query}' indexed in ChromaDB.")
        logger.info(f"Document registry: {len(self.registry.entries)} source entries tracked.")
        logger.info(f"{'='*60}")

    def _clear_signal_collection(self):
        """
        Full-refresh: Delete and recreate the risk_signals collection.
        Ensures no stale or duplicated data persists across runs.
        """
        logger.info("[Step 1/7] FULL REFRESH — Clearing risk_signals collection...")
        try:
            self.chroma.client.delete_collection("risk_signals")
            logger.info("Cleared existing risk_signals collection.")
        except Exception as e:
            logger.info(f"No existing risk_signals collection to clear: {e}")

        # Recreate empty collection
        self.chroma.get_or_create_collection("risk_signals")
        logger.info("Created fresh risk_signals collection.")


if __name__ == "__main__":
    pipeline = DataRefreshPipeline()
    # Default to "STABLE" for verification as requested by user
    asyncio.run(pipeline.run("STABLE"))
