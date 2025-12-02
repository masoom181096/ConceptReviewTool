import re
from typing import List, Dict, Any


def build_baseline_kpis(ops_fleet_text: str, sector_profile: dict) -> List[Dict[str, Any]]:
    """
    Build baseline KPIs from operational text and sector profile data.
    
    Derives key performance indicators and sets target values using
    standard percentage improvements.
    TODO: Replace static targets with LLM-driven goal setting for production.
    
    Args:
        ops_fleet_text: Raw text describing operations and fleet data
        sector_profile: Dictionary with sector profile data
        
    Returns:
        List of dictionaries matching BaselineKPI model fields
    """
    kpis = []
    
    fleet_total = sector_profile.get("fleet_total") or 0
    fleet_electric = sector_profile.get("fleet_electric") or 0
    daily_ridership = sector_profile.get("daily_ridership") or 0
    annual_opex = sector_profile.get("annual_opex_usd") or 0
    annual_co2 = sector_profile.get("annual_co2_tons") or 0
    
    if annual_co2 > 0:
        target_co2 = annual_co2 * 0.65
        kpis.append({
            "name": "Annual CO2 Emissions",
            "baseline_value": f"{annual_co2:,.0f}",
            "unit": "tons/year",
            "target_value": f"{target_co2:,.0f}",
            "category": "environment",
            "notes": "Target: 35% reduction through fleet electrification"
        })
    
    if fleet_total > 0 and annual_opex > 0:
        cost_per_bus = annual_opex / fleet_total
        target_cost = cost_per_bus * 0.85
        kpis.append({
            "name": "Operating Cost per Bus",
            "baseline_value": f"{cost_per_bus:,.0f}",
            "unit": "USD/year",
            "target_value": f"{target_cost:,.0f}",
            "category": "operations",
            "notes": "Target: 15% reduction through efficiency and electrification"
        })
    
    if fleet_total > 0 and daily_ridership > 0:
        ridership_per_bus = daily_ridership / fleet_total
        target_ridership = ridership_per_bus * 1.20
        kpis.append({
            "name": "Daily Ridership per Bus",
            "baseline_value": f"{ridership_per_bus:,.0f}",
            "unit": "passengers/day",
            "target_value": f"{target_ridership:,.0f}",
            "category": "operations",
            "notes": "Target: 20% increase through improved service quality"
        })
    
    if fleet_total > 0:
        electrification_pct = (fleet_electric / fleet_total) * 100
        target_electrification = min(electrification_pct + 30, 100)
        kpis.append({
            "name": "Fleet Electrification Rate",
            "baseline_value": f"{electrification_pct:.1f}",
            "unit": "%",
            "target_value": f"{target_electrification:.1f}",
            "category": "environment",
            "notes": "Target: 30 percentage point increase over project period"
        })
    
    availability_baseline = _extract_metric(ops_fleet_text, ["availability", "uptime"], default=85.0)
    kpis.append({
        "name": "Fleet Availability",
        "baseline_value": f"{availability_baseline:.1f}",
        "unit": "%",
        "target_value": f"{min(availability_baseline + 5, 98):.1f}",
        "category": "operations",
        "notes": "Target: 5 percentage point improvement"
    })
    
    frequency_baseline = _extract_metric(ops_fleet_text, ["frequency", "headway", "minutes"], default=15)
    kpis.append({
        "name": "Average Service Frequency",
        "baseline_value": f"{frequency_baseline:.0f}",
        "unit": "minutes",
        "target_value": f"{max(frequency_baseline - 3, 5):.0f}",
        "category": "service",
        "notes": "Target: Reduce average wait time by 3 minutes"
    })
    
    if annual_co2 > 0 and daily_ridership > 0:
        annual_ridership = daily_ridership * 365
        emissions_per_1k = (annual_co2 / annual_ridership) * 1000
        target_emissions = emissions_per_1k * 0.60
        kpis.append({
            "name": "CO2 per 1000 Passengers",
            "baseline_value": f"{emissions_per_1k:.2f}",
            "unit": "tons",
            "target_value": f"{target_emissions:.2f}",
            "category": "environment",
            "notes": "Target: 40% reduction per passenger through electrification"
        })
    
    return kpis


def _extract_metric(text: str, keywords: List[str], default: float) -> float:
    """
    Try to extract a numeric metric near certain keywords from text.
    Falls back to default if not found.
    """
    if not text:
        return default
    
    for keyword in keywords:
        patterns = [
            rf'{keyword}\s*[:\-]?\s*([\d.]+)\s*%?',
            rf'([\d.]+)\s*%?\s*{keyword}',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
    
    return default
