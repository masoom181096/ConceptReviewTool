import re
from typing import Dict, Any, Optional


def build_sustainability_profile(text: str, baseline_co2: float = 0) -> Dict[str, Any]:
    """
    Build sustainability/ESG profile from project documentation.
    
    Parses sustainability text and derives environmental and social metrics.
    TODO: Replace with LLM-based ESG analysis for production.
    
    Args:
        text: Raw sustainability/ESG documentation text
        baseline_co2: Baseline CO2 emissions in tons/year for calculating reduction
        
    Returns:
        Dictionary matching SustainabilityProfile model fields
    """
    result = {
        "category": "B",
        "co2_reduction_tons": None,
        "pm25_reduction": None,
        "accessibility_notes": None,
        "policy_alignment_notes": None,
        "key_risks": None,
        "mitigations": None
    }
    
    result["category"] = _determine_category(text)
    
    if baseline_co2 > 0:
        reduction_pct = _extract_reduction_target(text)
        result["co2_reduction_tons"] = baseline_co2 * (reduction_pct / 100)
    
    result["pm25_reduction"] = _extract_pm25_reduction(text)
    
    result["accessibility_notes"] = _build_accessibility_notes(text)
    
    result["policy_alignment_notes"] = _build_policy_notes(text)
    
    result["key_risks"] = _identify_risks(text)
    
    result["mitigations"] = _identify_mitigations(text)
    
    return result


def _determine_category(text: str) -> str:
    """
    Determine EBRD environmental/social category (A, B, or C).
    Category A: Significant adverse impacts
    Category B: Moderate impacts
    Category C: Minimal or no impacts
    """
    text_lower = text.lower() if text else ""
    
    high_risk_keywords = [
        "resettlement", "displacement", "indigenous", "protected area",
        "critical habitat", "cultural heritage", "large scale", "significant impact"
    ]
    
    low_risk_keywords = [
        "minimal impact", "no displacement", "existing infrastructure",
        "brownfield", "rehabilitation", "upgrade only"
    ]
    
    high_risk_count = sum(1 for kw in high_risk_keywords if kw in text_lower)
    low_risk_count = sum(1 for kw in low_risk_keywords if kw in text_lower)
    
    if high_risk_count >= 2:
        return "A"
    elif low_risk_count >= 2:
        return "C"
    else:
        return "B"


def _extract_reduction_target(text: str) -> float:
    """Extract CO2 reduction target percentage from text."""
    if not text:
        return 35.0
    
    patterns = [
        r'(\d+(?:\.\d+)?)\s*%?\s*(?:reduction|decrease|cut)\s*(?:in\s+)?(?:CO2|carbon|emissions?)',
        r'(?:reduce|decrease|cut)\s*(?:CO2|carbon|emissions?)?\s*(?:by\s+)?(\d+(?:\.\d+)?)\s*%',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    
    return 35.0


def _extract_pm25_reduction(text: str) -> str:
    """Extract PM2.5 reduction estimate from text."""
    if not text:
        return "Estimated 25-40% reduction in local PM2.5 emissions from fleet electrification"
    
    patterns = [
        r'PM2?\.?5\s*(?:reduction|decrease)?\s*(?:of\s+)?(\d+(?:\.\d+)?)\s*%',
        r'(\d+(?:\.\d+)?)\s*%\s*(?:reduction|decrease)\s*(?:in\s+)?PM2?\.?5',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"{match.group(1)}% reduction in PM2.5 emissions"
    
    return "Estimated 25-40% reduction in local PM2.5 emissions from fleet electrification"


def _build_accessibility_notes(text: str) -> str:
    """Build accessibility and social inclusion notes."""
    notes = []
    
    keywords_found = {
        "low-floor": "Low-floor buses improve accessibility for elderly and disabled passengers",
        "wheelchair": "Wheelchair-accessible vehicles included in fleet specifications",
        "audio": "Audio announcements enhance accessibility for visually impaired",
        "women": "Women's safety features considered in design",
        "affordable": "Fare structure maintains affordability for low-income users",
    }
    
    text_lower = text.lower() if text else ""
    
    for keyword, note in keywords_found.items():
        if keyword in text_lower:
            notes.append(note)
    
    if not notes:
        notes = [
            "New electric buses will include low-floor design for accessibility",
            "Route planning to prioritize underserved communities",
            "Fare integration to maintain affordability"
        ]
    
    return "; ".join(notes[:3])


def _build_policy_notes(text: str) -> str:
    """Build policy alignment notes."""
    alignments = [
        "Aligned with National Climate Action Plan and NDC commitments",
        "Supports Kenya Vision 2030 sustainable transport objectives",
        "Consistent with EBRD Green Economy Transition approach"
    ]
    
    text_lower = text.lower() if text else ""
    
    if "paris" in text_lower:
        alignments.append("Contributes to Paris Agreement goals")
    if "sdg" in text_lower or "sustainable development" in text_lower:
        alignments.append("Advances SDG 11 (Sustainable Cities) and SDG 13 (Climate Action)")
    
    return "; ".join(alignments[:4])


def _identify_risks(text: str) -> str:
    """Identify key ESG risks from text."""
    default_risks = [
        "Grid capacity constraints may limit charging infrastructure deployment",
        "Foreign exchange risk on USD-denominated repayments",
        "Technology obsolescence risk for early-generation e-buses",
        "Labor transition risk for diesel maintenance workforce"
    ]
    
    text_lower = text.lower() if text else ""
    risks = []
    
    risk_mapping = {
        "land acquisition": "Land acquisition delays for depot expansion",
        "procurement": "Procurement complexity for e-bus technology",
        "capacity": "Institutional capacity constraints for project management",
        "tariff": "Electricity tariff volatility affecting operating costs",
        "supply chain": "Supply chain risks for battery and component sourcing"
    }
    
    for keyword, risk in risk_mapping.items():
        if keyword in text_lower:
            risks.append(risk)
    
    if not risks:
        risks = default_risks
    
    return "; ".join(risks[:4])


def _identify_mitigations(text: str) -> str:
    """Identify risk mitigation measures."""
    default_mitigations = [
        "Technical assistance for grid capacity assessment and planning",
        "Phased deployment approach to manage technology risk",
        "Capacity building program for city transport authority",
        "Worker retraining program for diesel mechanics to EV maintenance"
    ]
    
    text_lower = text.lower() if text else ""
    mitigations = []
    
    mitigation_mapping = {
        "training": "Comprehensive training program for operators and maintenance staff",
        "pilot": "Pilot phase to test technology before full deployment",
        "guarantee": "Performance guarantees from equipment suppliers",
        "insurance": "Insurance coverage for key operational risks",
        "monitoring": "Robust M&E framework with clear KPIs"
    }
    
    for keyword, mitigation in mitigation_mapping.items():
        if keyword in text_lower:
            mitigations.append(mitigation)
    
    if not mitigations:
        mitigations = default_mitigations
    
    return "; ".join(mitigations[:4])
