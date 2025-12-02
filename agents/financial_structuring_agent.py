import re
from typing import List, Dict, Any
from services.stub_market_data import get_peer_median_rates, get_peer_deal_structures
from services.stub_sap_finance import get_repayment_indicators


def build_financial_options(text: str, principal_hint: float = 50_000_000) -> List[Dict[str, Any]]:
    """
    Build financial structuring options with 60/40 scoring rule.
    
    Generates three financing options and scores them based on:
    - 60% weight: Repayment capacity score
    - 40% weight: Rate competitiveness score
    
    Uses stub services for market data and repayment indicators.
    TODO: Replace stubs with real Bloomberg/SAP API calls for production.
    
    Args:
        text: Raw financial data text (used to hint at principal amount)
        principal_hint: Default principal amount in USD
        
    Returns:
        List of dictionaries matching FinancialOption model fields
    """
    
    principal = _extract_principal(text, principal_hint)
    
    peer_rates = get_peer_median_rates()
    repayment_data = get_repayment_indicators()
    
    options = []
    
    option_a = _build_sovereign_loan(principal, peer_rates, repayment_data)
    options.append(option_a)
    
    option_b = _build_guaranteed_loan(principal, peer_rates, repayment_data)
    options.append(option_b)
    
    option_c = _build_blended_finance(principal, peer_rates, repayment_data)
    options.append(option_c)
    
    return options


def _extract_principal(text: str, default: float) -> float:
    """Extract principal amount from text if mentioned."""
    if not text:
        return default
    
    patterns = [
        r'\$\s*([\d,]+(?:\.\d+)?)\s*(?:million|m\b|M\b)',
        r'USD\s*([\d,]+(?:\.\d+)?)\s*(?:million|m\b|M\b)',
        r'([\d,]+(?:\.\d+)?)\s*(?:million|m\b|M\b)\s*(?:USD|dollars?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(",", "")
            return float(amount_str) * 1_000_000
    
    return default


def _calculate_rate_score(rate_bps: float, peer_median: float) -> float:
    """
    Calculate rate score based on difference from peer median.
    Best rate (lowest) gets ~100, worst (highest) gets ~0.
    """
    spread = rate_bps - peer_median
    
    if spread <= -50:
        return 100.0
    elif spread >= 150:
        return 0.0
    else:
        return 100.0 - ((spread + 50) / 200) * 100


def _calculate_repayment_score(dscr: float, fx_risk: str, debt_ratio: float) -> float:
    """
    Calculate repayment capacity score based on key indicators.
    """
    score = 50.0
    
    if dscr >= 2.0:
        score += 30
    elif dscr >= 1.5:
        score += 20
    elif dscr >= 1.2:
        score += 10
    else:
        score -= 10
    
    if fx_risk == "low":
        score += 15
    elif fx_risk == "medium":
        score += 5
    else:
        score -= 10
    
    if debt_ratio < 0.4:
        score += 15
    elif debt_ratio < 0.6:
        score += 5
    else:
        score -= 5
    
    return max(0, min(100, score))


def _build_sovereign_loan(principal: float, peer_rates: dict, repayment: dict) -> dict:
    """Build Option A: Direct Sovereign Loan structure."""
    tenor = 20
    grace = 5
    rate_bps = 180
    
    rate_score = _calculate_rate_score(rate_bps, peer_rates["sovereign_median"])
    repayment_score = _calculate_repayment_score(
        repayment["sovereign_dscr"],
        repayment["sovereign_fx_risk"],
        repayment["sovereign_debt_ratio"]
    )
    total_score = 0.6 * repayment_score + 0.4 * rate_score
    
    return {
        "name": "Option A - Sovereign Loan",
        "instrument_type": "sovereign_loan",
        "currency": "USD",
        "tenor_years": tenor,
        "grace_period_years": grace,
        "all_in_rate_bps": rate_bps,
        "principal_amount_usd": principal,
        "repayment_score": round(repayment_score, 1),
        "rate_score": round(rate_score, 1),
        "total_score": round(total_score, 1),
        "pros": "Lowest cost of capital; Strong sovereign backing; Long tenor with grace period; Preferred creditor status for EBRD",
        "cons": "Requires sovereign guarantee process; Subject to national debt ceiling; May face parliamentary approval requirements"
    }


def _build_guaranteed_loan(principal: float, peer_rates: dict, repayment: dict) -> dict:
    """Build Option B: Sovereign-Guaranteed Loan to City Authority."""
    tenor = 15
    grace = 3
    rate_bps = 250
    
    rate_score = _calculate_rate_score(rate_bps, peer_rates["subnational_median"])
    repayment_score = _calculate_repayment_score(
        repayment["city_dscr"],
        repayment["city_fx_risk"],
        repayment["city_debt_ratio"]
    )
    total_score = 0.6 * repayment_score + 0.4 * rate_score
    
    return {
        "name": "Option B - Sovereign-Guaranteed City Loan",
        "instrument_type": "guaranteed_subnational",
        "currency": "USD",
        "tenor_years": tenor,
        "grace_period_years": grace,
        "all_in_rate_bps": rate_bps,
        "principal_amount_usd": principal,
        "repayment_score": round(repayment_score, 1),
        "rate_score": round(rate_score, 1),
        "total_score": round(total_score, 1),
        "pros": "Builds city capacity for future borrowing; Faster disbursement; Direct accountability to beneficiary; Supports decentralization agenda",
        "cons": "Higher interest rate; Shorter tenor; Requires sovereign guarantee; City revenue may be volatile"
    }


def _build_blended_finance(principal: float, peer_rates: dict, repayment: dict) -> dict:
    """Build Option C: Blended/Co-financing Structure."""
    tenor = 18
    grace = 4
    rate_bps = 210
    
    blended_principal = principal * 0.6
    
    avg_rate = (rate_bps + 150) / 2
    rate_score = _calculate_rate_score(avg_rate, peer_rates["blended_median"])
    
    blended_dscr = (repayment["sovereign_dscr"] + repayment["city_dscr"]) / 2
    repayment_score = _calculate_repayment_score(
        blended_dscr,
        "medium",
        (repayment["sovereign_debt_ratio"] + repayment["city_debt_ratio"]) / 2
    )
    total_score = 0.6 * repayment_score + 0.4 * rate_score
    
    return {
        "name": "Option C - Blended Co-Financing",
        "instrument_type": "co_financing",
        "currency": "USD",
        "tenor_years": tenor,
        "grace_period_years": grace,
        "all_in_rate_bps": rate_bps,
        "principal_amount_usd": principal,
        "repayment_score": round(repayment_score, 1),
        "rate_score": round(rate_score, 1),
        "total_score": round(total_score, 1),
        "pros": f"Reduces EBRD exposure to ${blended_principal/1e6:.0f}M; Brings in concessional funding; Demonstrates donor coordination; Can unlock grant components for TA",
        "cons": "Complex structuring and coordination; Multiple approval processes; Potential misalignment of conditions; Longer preparation time"
    }
