import re

def clean(text):
    # Aggressive Regex Replacement (Precision Enforcement)
    # Swap multi-word vague phrases first
    text = re.sub(r"\bcould not be\b", "was not", text, flags=re.IGNORECASE)
    text = re.sub(r"\bcannot be\b", "is not", text, flags=re.IGNORECASE)
    text = re.sub(r"\bis likely\b", "is", text, flags=re.IGNORECASE)
    text = re.sub(r"\bappears to be\b", "is", text, flags=re.IGNORECASE)

    # Swap single forbidden words
    swaps = {
        r"\bsuggests\b": "reports",
        r"\bindicates\b": "shows",
        r"\bappears\b": "is",
        r"\blikely\b": "reported",
        r"\bpotential\b": "reported",
        r"\bcould\b": "was",
        r"\bmight\b": "is",
        r"\bmay\b": "is"
    }
    
    for pattern, replacement in swaps.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text

test_strings = [
    "Contract data could not be retrieved.",
    "This suggests a rug pull.",
    "It is likely a scam.",
    "Structural data could not be found.",
    "Risks could increase."
]

for s in test_strings:
    print(f"Original: {s}")
    print(f"Cleaned:  {clean(s)}")
    print("-" * 20)
