"""
RAG Service — Main Pipeline Orchestrator

Implements the full end-to-end processing pipeline:
  1. Query Router → classify intent
  2. Entity Resolver → resolve via CoinGecko
  3. Asset Classifier → determine applicable layers
  4. Signal Engine → compute signals (using existing scripts/services)
  5. Signal Normalizer → standardize + fallback
  6. RAG Retriever → signal-driven retrieval
  7. LLM → explanation only
  8. Output Formatter → enforce fixed schema
  9. Post-Guards → validate structure
"""

import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any, List

from backend.services.query_router import QueryRouter, QueryIntent
from backend.services.entity_resolver import EntityResolver, CanonicalAsset
from backend.services.asset_classifier import AssetClassifier, AssetType
from backend.services.signal_normalizer import SignalNormalizer, NormalizedSignals
from backend.services.output_formatter import OutputFormatter
from backend.services.post_guards import PostGuards
from backend.services.chroma_service import ChromaService
from backend.services.groq_service import GroqService
from backend.services.goplus_service import GoPlusService
from backend.utils.embeddings import BGEEmbeddings
from backend.prompts.assistant_prompts import (
    FACTS_ONLY_SYSTEM_PROMPT,
    RAG_PROMPT_TEMPLATE,
    RAG_PROMPT_NO_CONTEXT,
)

logger = logging.getLogger(__name__)


class RAGService:
    """
    Chain-agnostic, identity-first RAG orchestrator.
    """

    def _compress_context(self, context_blocks: List[str], max_tokens: int = 500) -> str:
        """
        Compresses retrieved context to fit within a specific token budget.
        Uses a simple word-count heuristic (1 word ~= 1.3 tokens).
        """
        compressed = []
        total_tokens = 0
        
        for block in context_blocks:
            # Clean block
            clean_block = block.strip()
            # Estimate tokens
            block_tokens = int(len(clean_block.split()) * 1.3)
            
            if total_tokens + block_tokens <= max_tokens:
                compressed.append(clean_block)
                total_tokens += block_tokens
            else:
                # Add partial block if room remains
                remaining = max_tokens - total_tokens
                if remaining > 50:
                    words = clean_block.split()
                    short_block = " ".join(words[:int(remaining / 1.3)])
                    compressed.append(short_block + "...")
                break
                
        return "\n\n".join(compressed)

    def __init__(self):
        # Pipeline components
        self.query_router = QueryRouter()
        self.entity_resolver = EntityResolver()
        self.asset_classifier = AssetClassifier()
        self.signal_normalizer = SignalNormalizer()
        self.output_formatter = OutputFormatter()
        self.post_guards = PostGuards()

        # Infrastructure services
        self.chroma = ChromaService()
        self.groq = GroqService()
        self.goplus = GoPlusService()
        self.embedder = BGEEmbeddings()

    async def answer_query(self, query: str) -> str:
        """
        Main entry point — processes a user query through the full pipeline.
        """
        logger.info(f"RAGService: Processing query — '{query[:80]}'")

        try:
            # ─── Step 1: Query Router ─────────────────────────────────────
            intent, refusal_message = self.query_router.classify(query)

            if intent != QueryIntent.FACTUAL:
                logger.info(f"RAGService: Query routed to refusal ({intent})")
                return self.output_formatter.format_refusal(refusal_message)

            # ─── Step 2: Entity Resolution ────────────────────────────────
            asset = await self.entity_resolver.resolve(query)
            logger.info(f"RAGService: Entity resolved → {asset}")

            if not asset.resolved and not asset.contract_address:
                return self.output_formatter.format_error(
                    "Asset not found in our database. Please check the spelling or search using a contract address (0x...)."
                ), {}

            # ─── Step 3: Asset Classification ─────────────────────────────
            asset_type, layer_config = self.asset_classifier.classify_and_configure(asset)
            logger.info(f"RAGService: Asset type → {asset_type}")

            # ─── Step 4: Signal Computation ───────────────────────────────
            raw_signals = await self._compute_signals(asset, asset_type, layer_config)

            # ─── Step 5: Signal Normalization ─────────────────────────────
            normalized = self.signal_normalizer.normalize_all(
                blockchain_data=raw_signals.get("blockchain"),
                market_data=raw_signals.get("market"),
                audit_data=raw_signals.get("audit"),
                regulatory_data=raw_signals.get("regulatory_list"),
                structural_applicable=layer_config.structural,
                audit_mode=layer_config.audit_mode,
                market_mode=layer_config.market_mode,
                warning_count=raw_signals.get("regulatory_warning_count", 0),
                source_url=self._determine_source_url(asset),
                chain=asset.chain,
                has_contract=bool(asset.contract_address),
                asset_metadata={
                    "asset_id": asset.asset_id,
                    "contract_address": asset.contract_address,
                }
            )

            # ─── Step 6: RAG Retrieval (Signal-Driven) ────────────────────
            retrieved_context = self._retrieve_context(normalized, asset)

            # ─── Step 7: LLM Explanation ──────────────────────────────────
            explanation = await self._generate_explanation(
                asset, asset_type, normalized, retrieved_context
            )

            # ─── Step 8: Output Formatting ────────────────────────────────
            formatted = self.output_formatter.format_response(
                signals=normalized,
                explanation=explanation,
                asset_name=asset.name,
            )

            # ─── Step 9: Post-Guards ──────────────────────────────────────
            validated = self.post_guards.enforce(formatted)

            logger.info("RAGService: Pipeline complete → response delivered")
            
            # Combine all signals for the unified risk profile
            blockchain_data = raw_signals.get("blockchain") or {}
            market_data = raw_signals.get("market") or {}
            audit_data = raw_signals.get("audit") or {}
            
            unified_profile = {**blockchain_data}
            unified_profile["token_name"] = market_data.get("token_name_found")
            unified_profile["token_symbol"] = market_data.get("token_symbol_found")
            unified_profile["market_cap"] = market_data.get("market_cap")
            unified_profile["market_cap_rank"] = market_data.get("market_cap_rank")
            unified_profile["exchanges_count"] = market_data.get("exchange_count")
            unified_profile["asset_type"] = asset_type
            unified_profile["contract_address"] = asset.contract_address
            
            # Merge audit and regulatory data
            unified_profile["is_audited"] = audit_data.get("is_audited", False)
            unified_profile["audit_providers"] = audit_data.get("audit_providers", [])
            unified_profile["is_open_source"] = blockchain_data.get("is_open_source", False) if blockchain_data else False
            unified_profile["regulatory_warning_count"] = raw_signals.get("regulatory_warning_count", 0)
            unified_profile["source_url"] = normalized.source_url
            
            return validated, unified_profile

        except Exception as e:
            logger.error(f"RAGService: Pipeline error — {str(e)}")
            return self.output_formatter.format_error(
                f"An error occurred while processing the query. Error: {str(e)}"
            ), {}

    # ─── Step 4 Implementation: Signal Computation ────────────────────────────

    async def _compute_signals(
        self,
        asset: CanonicalAsset,
        asset_type: str,
        layer_config,
    ) -> Dict[str, Any]:
        """
        Compute raw signals from stored data and direct lookups.
        Uses ChromaDB for pre-computed signals when available.
        """
        signals = {
            "blockchain": None,
            "market": None,
            "audit": None,
            "regulatory_list": None,
            "regulatory_warning_count": 0,
        }

        # Try to load pre-computed signals from ChromaDB
        entry_id = None
        if asset.contract_address:
            entry_id = f"signal_{asset.contract_address}"
        elif asset.asset_id:
            entry_id = f"signal_{asset.asset_id}"
        elif asset.symbol:
            entry_id = f"signal_{asset.symbol.lower()}"

        stored_signals = None
        if entry_id:
            try:
                res = self.chroma.get_signals(
                    "risk_signals",
                    ids=[entry_id],
                )
                if res and res.get("metadatas") and res["metadatas"]:
                    meta = res["metadatas"][0] if res["metadatas"] else None
                    if meta and isinstance(meta, dict):
                        stored_signals = meta
                        logger.info(f"RAGService: Found pre-computed signals for {entry_id}")
            except Exception as e:
                logger.warning(f"RAGService: Could not load stored signals — {e}")

        # Parse stored signals into layer-specific data
        if stored_signals:
            # Blockchain / Structural
            if layer_config.structural:
                signals["blockchain"] = {
                    "contract_age_days": stored_signals.get("contract_age_days"),
                    "is_new_contract": stored_signals.get("is_new_contract"),
                    "creation_date": stored_signals.get("creation_date"),
                    "total_supply": stored_signals.get("total_supply"),
                    "wallet_concentration_risk": stored_signals.get("wallet_concentration_risk"),
                    "is_honeypot": stored_signals.get("is_honeypot"),
                    "is_mintable": stored_signals.get("is_mintable"),
                    "is_proxy": stored_signals.get("is_proxy"),
                    "buy_tax": stored_signals.get("buy_tax"),
                    "sell_tax": stored_signals.get("sell_tax"),
                }

            # Market
            signals["market"] = {
                "is_listed": stored_signals.get("is_listed", False),
                "market_cap_rank": stored_signals.get("market_cap_rank") or stored_signals.get("market_rank", "unknown"),
                "market_cap": stored_signals.get("market_cap") or asset.market_cap,
                "exchange_count": stored_signals.get("exchange_count") or asset.exchange_count,
                "token_name_found": stored_signals.get("token_name_found") or asset.name,
                "token_symbol_found": stored_signals.get("token_symbol_found") or asset.symbol,
                "market_source": stored_signals.get("market_source", "CoinGecko"),
            }

            # Audit
            signals["audit"] = {
                "is_audited": stored_signals.get("is_audited", False),
                "audit_providers": self._parse_list(stored_signals.get("audit_providers", "[]")),
            }

            # Regulatory
            signals["regulatory_warning_count"] = stored_signals.get("regulatory_warning_count", 0)

        # No stored signals found or stale? — Build market signals + fetch GoPlus
        if not stored_signals or not signals.get("market"):
            if asset.resolved:
                signals["market"] = {
                    "is_listed": True,
                    "market_cap_rank": asset.market_cap_rank if asset.market_cap_rank else "unknown",
                    "market_cap": asset.market_cap,
                    "exchange_count": asset.exchange_count,
                    "market_presence": asset.market_presence,
                    "token_name_found": asset.name,
                    "token_symbol_found": asset.symbol,
                    "market_source": "CoinGecko",
                }
            else:
                signals["market"] = {
                    "is_listed": False,
                    "market_rank": "unknown",
                }

        # --- GO PLUS INTEGRATION (On-the-run + Cache) ---
        if asset.contract_address and asset.chain:
            # Only fetch if not already in stored_signals (or add TTL check later)
            if not stored_signals or "is_honeypot" not in stored_signals:
                logger.info(f"RAGService: Fetching live security signals from GoPlus for {asset.symbol}")
                raw_goplus = await self.goplus.get_token_security(asset.chain, asset.contract_address)
                if raw_goplus:
                    gp_signals = self.goplus.extract_signals(raw_goplus)
                    
                    # Merge into audit layer
                    signals["audit"] = {
                        "is_audited": gp_signals["is_audited"],
                        "audit_providers": [gp_signals["audit_provider"]] if gp_signals["audit_provider"] else [],
                        "source": "GoPlus Security"
                    }
                    
                    # Merge into structural layer
                    if not signals["blockchain"]: signals["blockchain"] = {}
                    signals["blockchain"].update({
                        "is_honeypot": gp_signals["is_honeypot"],
                        "is_mintable": gp_signals["is_mintable"],
                        "is_proxy": gp_signals["is_proxy"],
                        "buy_tax": gp_signals["buy_tax"],
                        "sell_tax": gp_signals["sell_tax"],
                    })
                    
                    # CACHE in ChromaDB
                    if entry_id:
                        self.chroma.add_signals(
                            "risk_signals",
                            ids=[entry_id],
                            documents=[f"Security signals for {asset.name} via GoPlus."],
                            metadatas=[{**gp_signals, "last_updated": datetime.utcnow().isoformat()}]
                        )

        return signals

    # ─── Step 6 Implementation: Signal-Driven Retrieval ───────────────────────

    def _retrieve_context(
        self,
        signals: NormalizedSignals,
        asset: CanonicalAsset,
    ) -> str:
        """
        Construct signal-driven retrieval queries and fetch from knowledge base.
        Queries are based on DETECTED signals, not raw user input.
        """
        # Build retrieval query from the most relevant signals
        query_parts = []

        for signal in signals.structural:
            if "not applicable" not in signal.lower():
                query_parts.append(signal)

        for signal in signals.audit:
            if "no audit found" in signal.lower():
                query_parts.append("risks of unaudited smart contracts")
            elif "audited" in signal.lower():
                query_parts.append("smart contract audit verification")

        for signal in signals.regulatory:
            if "warning" in signal.lower() or "alert" in signal.lower():
                query_parts.append("regulatory warning implications crypto")

        if not query_parts:
            # Minimal context for clean assets
            query_parts.append(f"crypto risk assessment {asset.name or asset.raw_input}")

        retrieval_query = ". ".join(query_parts[:3])  # Limit to top 3 for token efficiency

        try:
            kb_results = self.chroma.query_signals(
                "knowledge_base",
                query_text=retrieval_query,
                n_results=3,
                embedding_function=self.embedder,
            )

            if kb_results and kb_results.get("documents") and kb_results["documents"]:
                docs = kb_results["documents"][0] if isinstance(kb_results["documents"][0], list) else kb_results["documents"]
                if docs:
                    return self._compress_context(docs, max_tokens=500)
                    
        except Exception as e:
            logger.warning(f"RAGService: Knowledge base retrieval failed — {e}")

        return "No additional reference material available."

    # ─── Step 7 Implementation: LLM Explanation ───────────────────────────────

    async def _generate_explanation(
        self,
        asset: CanonicalAsset,
        asset_type: str,
        signals: NormalizedSignals,
        retrieved_context: str,
    ) -> str:
        """
        Generate a 2-3 sentence explanation using the LLM.
        The LLM explains signals — it does not generate them.
        """
        # Choose template based on context availability
        has_context = retrieved_context and "no additional" not in retrieved_context.lower()
        template = RAG_PROMPT_TEMPLATE if has_context else RAG_PROMPT_NO_CONTEXT

        prompt = template.format(
            asset_name=asset.name or asset.raw_input,
            asset_symbol=asset.symbol or "N/A",
            asset_type=signals.asset_type,
            data_coverage=signals.data_coverage,
            structural_signals="; ".join(signals.structural),
            market_signals="; ".join(signals.market),
            audit_signals="; ".join(signals.audit),
            regulatory_signals="; ".join(signals.regulatory),
            retrieved_context=retrieved_context if has_context else "",
        )

        logger.info("RAGService: Generating LLM explanation...")
        explanation = await self.groq.generate_response(
            prompt=prompt,
            system_instruction=FACTS_ONLY_SYSTEM_PROMPT,
        )

        return explanation

    # ─── Utility Methods ──────────────────────────────────────────────────────

    def _determine_source_url(self, asset: CanonicalAsset) -> str:
        """Determine the most relevant source URL for the asset."""
        if asset.contract_address:
            # Platform-specific explorers
            chain_explorers = {
                "ethereum": "https://etherscan.io/token/",
                "binance-smart-chain": "https://bscscan.com/token/",
                "polygon-pos": "https://polygonscan.com/token/",
                "arbitrum-one": "https://arbiscan.io/token/",
                "base": "https://basescan.org/token/",
                "solana": "https://solscan.io/token/",
            }
            
            base_url = chain_explorers.get(asset.chain)
            if base_url:
                return f"{base_url}{asset.contract_address}"
            
            # Fallback for other chains or native assets
            if asset.asset_id:
                return f"https://www.coingecko.com/en/coins/{asset.asset_id}"
            
            return f"https://etherscan.io/token/{asset.contract_address}"

        if asset.asset_id:
            return f"https://www.coingecko.com/en/coins/{asset.asset_id}"

        return "https://www.coingecko.com"

    def _parse_list(self, value) -> list:
        """Parse a stringified list back to a Python list."""
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                import ast
                return ast.literal_eval(value)
            except (ValueError, SyntaxError):
                return [value] if value else []
        return []
