from datetime import datetime, timedelta
import re
from typing import Optional

class SignalNormalizer:
    """
    Utility for standardizing raw data into consistent risk signals.
    """
    
    @staticmethod
    def parse_etherscan_date(timestamp: str) -> Optional[datetime]:
        """
        Parses Etherscan timestamp (often an integer string) into a datetime object.
        """
        try:
            return datetime.fromtimestamp(int(timestamp))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def calculate_days_ago(dt: datetime) -> int:
        """
        Calculates the number of days between the given datetime and now.
        """
        now = datetime.utcnow()
        delta = now - dt
        return delta.days

    @staticmethod
    def format_percentage(value: float, decimals: int = 2) -> float:
        """
        Ensures percentages are rounded consistently.
        """
        return round(value, decimals)

    @staticmethod
    def extract_address(text: str) -> Optional[str]:
        """
        Extracts an Ethereum address from a string using regex.
        """
        pattern = r'0x[a-fA-F0-9]{40}'
        match = re.search(pattern, text)
        return match.group(0) if match else None
