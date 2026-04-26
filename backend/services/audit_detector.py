import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class AuditDetector:
    """
    Deterministic audit detection engine.
    Ensures output matches strict precision requirements:
    - "Audit found (CertiK)"
    - "Audit found (Hacken)"
    - "No audit found in indexed sources"
    """

    TRUSTED_PROVIDERS = {
        "certik": "CertiK",
        "hacken": "Hacken",
        "quantstamp": "Quantstamp",
        "peckshield": "PeckShield",
        "slowmist": "SlowMist",
    }

    @classmethod
    def detect(cls, audit_data: Optional[Dict[str, Any]] = None, official_links: Optional[List[str]] = None) -> str:
        """
        Main detection logic.
        Priority: 
        1. Explicit database signal (audit_data)
        2. Pattern matching in official links
        """
        found_provider = None

        # 1. Check database signals
        if audit_data:
            providers = []
            if audit_data.get("is_audited"):
                providers = audit_data.get("audit_providers", [])
                if isinstance(providers, str):
                    # Handle stringified list from ChromaDB
                    import ast
                    try:
                        providers = ast.literal_eval(providers)
                    except Exception as e:
                        logger.warning(f"AuditDetector: Failed to parse providers string: {e}")
                        providers = [providers]
            
            if providers:
                # Check for trusted providers in the list
                for p in providers:
                    p_lower = str(p).lower()
                    for key, display in cls.TRUSTED_PROVIDERS.items():
                        if key in p_lower:
                            found_provider = display
                            break
                    if found_provider: break

        # 2. Check official links if not found in database
        if not found_provider and official_links:
            for link in official_links:
                if not link: continue
                link_lower = str(link).lower()
                for key, display in cls.TRUSTED_PROVIDERS.items():
                    if key in link_lower:
                        found_provider = display
                        break
                if found_provider: break

        # 3. Deterministic Output Formatting
        if found_provider:
            return f"Audit found ({found_provider})"
        
        return "No audit found in indexed sources"

if __name__ == "__main__":
    # Quick test
    print(AuditDetector.detect(audit_data={"is_audited": True, "audit_providers": ["CertiK Security Audit"]}))
    print(AuditDetector.detect(official_links=["https://certik.com/projects/aave"]))
    print(AuditDetector.detect())
