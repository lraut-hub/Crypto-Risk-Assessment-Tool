"""
Phase 9: End-to-End Validation Test Suite

This script verifies the entire crypto risk pipeline:
1. Entity Resolution (CoinGecko free API)
2. Asset Classification
3. Signal Generation
4. Normalization
5. RAG Retrieval
6. LLM Explanation (Groq)
7. Output Formatting
8. Post-Guard Validation

Test Cases:
- EVM Token Address (Full Pipeline)
- Native Asset (No Structural Layer)
- Unknown Token (Fallback Handler)
- Advisory Query (Query Router / Refusal)
- Out-of-Scope Query (Query Router / Refusal)
"""

import asyncio
import logging
import os
import sys
import json
from typing import Dict, Any

# Ensure backend can be imported
sys.path.append(os.getcwd())

from backend.services.rag_service import RAGService

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger("VERIFIER")

class PipelineVerifier:
    def __init__(self):
        self.rag = RAGService()
        self.results = []

    async def run_test(self, name: str, query: str, expected_behavior: str):
        print(f"\n[TEST] {name}")
        print(f"Query: {query}")
        print(f"Expected: {expected_behavior}")
        print("-" * 40)

        try:
            response = await self.rag.answer_query(query)
            
            # Basic validation
            passed = True
            failures = []
            
            # Handle Refusals separately
            if response.startswith("⚠️"):
                print("[INFO] Refusal detected (expected for Advisory/Intent)")
                if "Refusal" in expected_behavior or "strictly factual" in expected_behavior:
                    print("[PASS] Refusal handler triggered correctly")
                else:
                    failures.append("Unexpected refusal for factual query")
                self.results.append({"name": name, "passed": not bool(failures), "failures": failures})
                return

            # 1. Check for Precision Intelligence Block
            if "Asset Type:" not in response:
                failures.append("Missing mandatory 'Asset Type:' intelligence field")
            if "Data Coverage:" not in response:
                failures.append("Missing mandatory 'Data Coverage:' intelligence field")

            # 2. Check for Signal Category structure
            categories = ["Structural:", "Market:", "Audit:", "Regulatory:"]
            if "Signal Summary:" not in response:
                failures.append("Missing 'Signal Summary:' header")
            
            for cat in categories:
                if cat not in response:
                    failures.append(f"Missing category: {cat}")

            # 3. Check for Factual Summary replacing Explanation
            if "Explanation:" in response:
                failures.append("OUTDATED: 'Explanation:' header detected (should be 'Factual Summary:')")
            if "Factual Summary:" not in response:
                failures.append("Missing 'Factual Summary:' section")

            # 4. Strict Language Validation (No vague verbs)
            forbidden_verbs = ["suggests", "indicates", "appears", "likely", "potential", "could", "might"]
            for word in forbidden_verbs:
                if f" {word} " in response.lower():
                    failures.append(f"STRICTNESS FAILURE: Detected forbidden vague verb '{word}'")

            # 5. Financial Advice check
            forbidden_advice = ["buy", "sell", "invest", "recommendation", "suggest you"]
            for word in forbidden_advice:
                if f" {word} " in response.lower():
                    failures.append(f"ADVICE FAILURE: Detected forbidden financial word '{word}'")

            # 6. Metadata check
            if "Source:" not in response:
                failures.append("Missing 'Source:' section")
            if "Last Updated:" not in response:
                failures.append("Missing 'Last Updated:' section")

            if failures:
                print(f"[FAIL] {', '.join(failures)}")
                passed = False
            else:
                print("[PASS] Precision Schema & Language constraints validated")
            
            print(f"\nPreview Header:\n{response[:150]}...")
            print(f"\nFactual Summary Check:\n{response[response.find('Factual Summary:'):][:150]}...")
            
            self.results.append({"name": name, "passed": passed, "failures": failures})

        except Exception as e:
            print(f"[CRASH] {e}")
            self.results.append({"name": name, "passed": False, "failures": [str(e)]})

    def print_summary(self):
        print("\n" + "="*50)
        print("VERIFICATION SUMMARY")
        print("="*50)
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        
        for r in self.results:
            status = "[PASS]" if r["passed"] else "[FAIL]"
            print(f"{status} {r['name']}")
            if r["failures"]:
                for f in r["failures"]:
                    print(f"   L {f}")
        
        print("-" * 50)
        print(f"OVERALL: {passed}/{total} Passed")
        print("="*50)

async def main():
    verifier = PipelineVerifier()

    # 1. EVM Token (Uniswap)
    await verifier.run_test(
        "EVM Token Address",
        "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
        "Full 4-layer resolution with structural signals"
    )

    # 2. Native Asset (Bitcoin)
    await verifier.run_test(
        "Native Asset",
        "bitcoin",
        "Market + Regulatory + Audit Fallback"
    )

    # 3. Low Data Asset
    await verifier.run_test(
        "Fallback Handler",
        "NonExistentTokenXYZ_123",
        "Minimal signals with 'Asset not found' labels"
    )

    # 4. Advisory Query
    await verifier.run_test(
        "Advisory Check",
        "Should I invest in Ethereum today?",
        "Refusal or strictly factual response with NO advice"
    )

    # 5. Out-of-Scope
    await verifier.run_test(
        "Intent Routing",
        "What is the weather in London?",
        "Clean refusal stating out-of-scope"
    )

    verifier.print_summary()

if __name__ == "__main__":
    asyncio.run(main())
