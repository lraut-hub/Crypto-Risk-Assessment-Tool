import logging
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
import os

# Import our utility client
try:
    from scripts.utils.client import RateLimitedClient
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.client import RateLimitedClient

logger = logging.getLogger(__name__)

class AuditScraper:
    """
    Scraper for audit platforms (CertiK, Hacken) to verify audit status.
    """
    SOURCES = {
        "CertiK": "https://www.certik.com/projects",
        "Hacken": "https://hacken.io/audits/"
    }

    def __init__(self):
        self.client = RateLimitedClient(rate_limit_ms=2000) # Audits need more polite scraping

    async def check_certik(self, project_name: str) -> Optional[Dict[str, Any]]:
        """
        Checks if a project exists on CertiK's platform.
        """
        logger.info(f"Checking CertiK for {project_name}...")
        # CertiK often uses dynamic list/search. We will simulate a basic search check.
        # This is a simplified scraper; real production might need Playwright for SPAs
        url = f"{self.SOURCES['CertiK']}?q={project_name}"
        response = await self.client.get(url)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Look for project name in result set
            found = soup.find(text=lambda t: project_name.lower() in t.lower())
            if found:
                return {
                    "provider": "CertiK",
                    "status": "Found",
                    "url": url
                }
        return None

    async def check_hacken(self, project_name: str) -> Optional[Dict[str, Any]]:
        """
        Checks if an audit exists on Hacken's platform.
        """
        logger.info(f"Checking Hacken for {project_name}...")
        url = f"{self.SOURCES['Hacken']}?s={project_name}"
        response = await self.client.get(url)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Hacken typically lists audits in cards or list items
            if project_name.lower() in response.text.lower():
                return {
                    "provider": "Hacken",
                    "status": "Found",
                    "url": url
                }
        return None

    async def close(self):
        await self.client.close()
