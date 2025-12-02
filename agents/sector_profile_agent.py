import re
from typing import Optional


def build_sector_profile(text: str) -> dict:
    """
    Parse sector profile text to extract fleet and operational metrics.
    
    This is a deterministic parser using regex patterns.
    TODO: Replace with LLM-based extraction for production use.
    
    Args:
        text: Raw sector profile text (government docs, fleet data)
        
    Returns:
        Dictionary matching SectorProfile model fields
    """
    result = {
        "fleet_total": None,
        "fleet_diesel": None,
        "fleet_hybrid": None,
        "fleet_electric": None,
        "depots": None,
        "daily_ridership": None,
        "annual_opex_usd": None,
        "annual_co2_tons": None,
        "notes": None
    }
    
    if not text or not text.strip():
        return result
    
    def extract_number(pattern: str, txt: str, multiplier: float = 1.0) -> Optional[int]:
        match = re.search(pattern, txt, re.IGNORECASE)
        if match:
            num_str = match.group(1).replace(",", "").replace(" ", "")
            try:
                return int(float(num_str) * multiplier)
            except ValueError:
                return None
        return None
    
    def extract_float(pattern: str, txt: str, multiplier: float = 1.0) -> Optional[float]:
        match = re.search(pattern, txt, re.IGNORECASE)
        if match:
            num_str = match.group(1).replace(",", "").replace(" ", "")
            try:
                return float(num_str) * multiplier
            except ValueError:
                return None
        return None
    
    fleet_patterns = [
        r'(?:total|fleet|operates?)\s*(?:of)?\s*([\d,]+)\s*(?:buses|bus|vehicles)',
        r'([\d,]+)\s*(?:buses|bus|vehicles)\s*(?:in\s+)?(?:total|fleet|operation)',
        r'fleet\s*(?:size|of)?\s*:?\s*([\d,]+)',
    ]
    for pattern in fleet_patterns:
        val = extract_number(pattern, text)
        if val is not None:
            result["fleet_total"] = val
            break
    
    diesel_patterns = [
        r'diesel\s*(?:buses|fleet)?\s*:?\s*([\d,]+)',
        r'([\d,]+)[ \t]+(?:diesel|conventional)\s*(?:buses|bus|vehicles)',
    ]
    for pattern in diesel_patterns:
        val = extract_number(pattern, text)
        if val is not None:
            result["fleet_diesel"] = val
            break
    
    hybrid_patterns = [
        r'hybrid\s*(?:buses|fleet)?\s*:?\s*([\d,]+)',
        r'([\d,]+)[ \t]+hybrid\s*(?:buses|bus|vehicles)',
    ]
    for pattern in hybrid_patterns:
        val = extract_number(pattern, text)
        if val is not None:
            result["fleet_hybrid"] = val
            break
    
    electric_patterns = [
        r'(?:electric|e-bus|EV)\s*(?:buses|fleet)?\s*:?\s*([\d,]+)',
        r'([\d,]+)[ \t]+(?:electric|e-bus|EV)\s*(?:buses|bus|vehicles)',
    ]
    for pattern in electric_patterns:
        val = extract_number(pattern, text)
        if val is not None:
            result["fleet_electric"] = val
            break
    
    depot_patterns = [
        r'(?:depots?|terminals?|garages?)\s*:?\s*([\d,]+)',
        r'([\d,]+)[ \t]+(?:depots?|terminals?|garages?)',
    ]
    for pattern in depot_patterns:
        val = extract_number(pattern, text)
        if val is not None:
            result["depots"] = val
            break
    
    ridership_patterns = [
        r'([\d,]+(?:\.\d+)?)\s*(?:million|M)\s*(?:passengers?|riders?|ridership)\s*(?:per\s+)?(?:day|daily)',
        r'(?:daily|per\s+day)\s*(?:passengers?|riders?|ridership)\s*(?:of)?\s*:?\s*([\d,]+(?:\.\d+)?)\s*(?:million|M)?',
        r'([\d,]+(?:,\d{3})*)\s*(?:passengers?|riders?)\s*(?:per\s+)?(?:day|daily)',
    ]
    for pattern in ridership_patterns:
        if "million" in pattern.lower() or "M" in pattern:
            val = extract_number(pattern, text, multiplier=1_000_000)
        else:
            val = extract_number(pattern, text)
        if val is not None:
            result["daily_ridership"] = val
            break
    
    opex_patterns = [
        r'(?:annual|yearly)\s*(?:operating|operational)?\s*(?:costs?|expenses?|opex)\s*(?:of)?\s*:?\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million|M)',
        r'\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million|M)\s*(?:annual|yearly)?\s*(?:operating|operational)?\s*(?:costs?|opex)',
        r'opex\s*:?\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million|M)?',
    ]
    for pattern in opex_patterns:
        val = extract_float(pattern, text, multiplier=1_000_000)
        if val is not None:
            result["annual_opex_usd"] = val
            break
    
    co2_patterns = [
        r'([\d,]+(?:\.\d+)?)\s*(?:tons?|tonnes?)\s*(?:of\s+)?(?:CO2|carbon)',
        r'(?:CO2|carbon)\s*(?:emissions?)?\s*(?:of)?\s*:?\s*([\d,]+(?:\.\d+)?)\s*(?:tons?|tonnes?)',
        r'(?:annual|yearly)\s*(?:CO2|carbon)\s*:?\s*([\d,]+(?:\.\d+)?)',
    ]
    for pattern in co2_patterns:
        val = extract_float(pattern, text)
        if val is not None:
            result["annual_co2_tons"] = val
            break
    
    sentences = text.split(".")
    key_notes = []
    keywords = ["challenge", "issue", "problem", "goal", "target", "plan", "upgrade", "moderniz"]
    for sentence in sentences:
        if any(kw in sentence.lower() for kw in keywords):
            clean = sentence.strip()
            if len(clean) > 20:
                key_notes.append(clean)
    if key_notes:
        result["notes"] = ". ".join(key_notes[:3])
    
    return result
