import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import os

# Import our utility client
try:
    from scripts.utils.client import RateLimitedClient
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.client import RateLimitedClient

logger = logging.getLogger(__name__)

class RegulatoryScraper:
    """
    Scraper for high-trust regulatory warning lists (FCA, MAS, SEC).
    """
    SOURCES = {
        "FCA": "https://www.fca.org.uk/scamsmart/warning-list",
        "MAS": "https://www.mas.gov.sg/investor-alert-list",
        "SEC": "https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins"
    }

    def __init__(self):
        self.client = RateLimitedClient(rate_limit_ms=1000)

    async def scrape_fca(self) -> List[Dict[str, Any]]:
        """
        Scrapes the FCA Warning List (ScamSmart).
        Note: Exact selectors may need adjustments based on real-time site changes.
        """
        logger.info("Scraping FCA Warning List...")
        response = await self.client.get(self.SOURCES["FCA"])
        warnings = []
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Placeholder logic: FCA often uses specific cards or table rows for warnings
            # We will look for common patterns in warning lists
            items = soup.select('.warning-list-item') or soup.select('.search-result')
            for item in items:
                name = item.select_one('h3').get_text(strip=True) if item.select_one('h3') else "Unknown"
                reason = item.get_text(strip=True)
                warnings.append({
                    "source": "FCA",
                    "entity_name": name,
                    "reason": reason,
                    "url": self.SOURCES["FCA"]
                })
        return warnings

    async def scrape_mas(self) -> List[Dict[str, Any]]:
        """
        Scrapes the MAS Investor Alert List.
        """
        logger.info("Scraping MAS Investor Alert List...")
        response = await self.client.get(self.SOURCES["MAS"])
        warnings = []
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            # MAS typically has a table-based alert list
            rows = soup.select('table tr')
            for row in rows[1:]: # Skip header
                cols = row.select('td')
                if len(cols) >= 1:
                    name = cols[0].get_text(strip=True)
                    warnings.append({
                        "source": "MAS",
                        "entity_name": name,
                        "reason": "Listed on MAS Investor Alert List",
                        "url": self.SOURCES["MAS"]
                    })
        return warnings

    async def scrape_sec(self) -> List[Dict[str, Any]]:
        """
        Scrapes the SEC Investor Alerts & Bulletins.
        """
        logger.info("Scraping SEC Investor Alerts & Bulletins...")
        response = await self.client.get(self.SOURCES["SEC"])
        warnings = []
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            # SEC alerts are usually in a list or view-content div
            items = soup.select('.views-row') or soup.find_all('div', class_='field-content')
            for item in items:
                link = item.find('a')
                if link:
                    name = link.get_text(strip=True)
                    warnings.append({
                        "source": "SEC",
                        "entity_name": name,
                        "reason": "Listed on SEC Investor Alert/Bulletin list",
                        "url": self.SOURCES["SEC"]
                    })
        return warnings

    async def close(self):
        await self.client.close()
