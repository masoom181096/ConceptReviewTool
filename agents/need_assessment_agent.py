import re
from typing import Optional


def parse_need_assessment(text: str) -> dict:
    """
    Parse need assessment text to extract key project information.
    
    This is a deterministic parser that uses regex and heuristics.
    TODO: Replace with LLM-based extraction for production use.
    
    Args:
        text: Raw need assessment text (email/MoM content)
        
    Returns:
        Dictionary with project_name, country, problem_summary, requested_amount_usd
    """
    result = {
        "project_name": None,
        "country": None,
        "problem_summary": None,
        "requested_amount_usd": None
    }
    
    if not text or not text.strip():
        return result
    
    amount_patterns = [
        r'\$\s*([\d,]+(?:\.\d+)?)\s*(?:million|m\b|M\b)',
        r'USD\s*([\d,]+(?:\.\d+)?)\s*(?:million|m\b|M\b)',
        r'([\d,]+(?:\.\d+)?)\s*(?:million|m\b|M\b)\s*(?:USD|dollars?)',
        r'\$\s*([\d,]+(?:\.\d+)?)\s*(?:billion|b\b|B\b)',
        r'([\d,]+(?:\.\d+)?)\s*(?:billion|b\b|B\b)\s*(?:USD|dollars?)',
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(",", "")
            amount = float(amount_str)
            if "billion" in pattern.lower() or "b\\b" in pattern.lower():
                amount *= 1_000_000_000
            else:
                amount *= 1_000_000
            result["requested_amount_usd"] = amount
            break
    
    countries = [
        "Kenya", "Nigeria", "South Africa", "Egypt", "Morocco", "Ghana",
        "Ethiopia", "Tanzania", "Uganda", "Rwanda", "Senegal", "Ivory Coast",
        "Poland", "Romania", "Bulgaria", "Ukraine", "Turkey", "Kazakhstan",
        "Uzbekistan", "Georgia", "Armenia", "Azerbaijan", "Mongolia",
        "Jordan", "Lebanon", "Tunisia", "Albania", "Serbia", "Montenegro",
        "North Macedonia", "Bosnia", "Kosovo", "Moldova", "Belarus",
        "Tajikistan", "Kyrgyzstan", "Turkmenistan"
    ]
    
    for country in countries:
        if country.lower() in text.lower():
            result["country"] = country
            break
    
    project_patterns = [
        r'(?:project|programme|program)[\s:]+["\']?([^"\'\n.]{10,80})["\']?',
        r'(?:titled?|named?|called)[\s:]+["\']?([^"\'\n.]{10,80})["\']?',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:E-Bus|Electric Bus|Fleet|Transport|Infrastructure)\s*(?:Project|Programme|Program)?)',
    ]
    
    for pattern in project_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["project_name"] = match.group(1).strip()[:100]
            break
    
    sentences = re.split(r'[.!?]+', text)
    clean_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    if clean_sentences:
        summary_sentences = clean_sentences[:3]
        result["problem_summary"] = ". ".join(summary_sentences)
        if not result["problem_summary"].endswith("."):
            result["problem_summary"] += "."
    
    return result
