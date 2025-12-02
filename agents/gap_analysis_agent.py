from typing import List, Dict, Any, Optional


BENCHMARK_DATA = {
    "Shenzhen": {
        "electrification_pct": 100.0,
        "depot_coverage_per_100_buses": 2.5,
        "opex_per_bus_usd": 45000,
        "comparability": "strong"
    },
    "London": {
        "electrification_pct": 35.0,
        "depot_coverage_per_100_buses": 1.8,
        "opex_per_bus_usd": 85000,
        "comparability": "strong"
    },
    "Santiago": {
        "electrification_pct": 20.0,
        "depot_coverage_per_100_buses": 1.5,
        "opex_per_bus_usd": 38000,
        "comparability": "illustrative"
    },
    "Bogota": {
        "electrification_pct": 15.0,
        "depot_coverage_per_100_buses": 1.2,
        "opex_per_bus_usd": 32000,
        "comparability": "illustrative"
    }
}


def build_gap_analysis(sector_profile: dict, benchmarks_text: str = "") -> List[Dict[str, Any]]:
    """
    Build gap analysis comparing project metrics against international benchmarks.
    
    Uses hard-coded benchmark data for Shenzhen, London, Santiago, Bogota.
    TODO: Replace with dynamic benchmark retrieval and LLM analysis for production.
    
    Args:
        sector_profile: Dictionary with sector profile data (from SectorProfile model)
        benchmarks_text: Optional raw text with additional benchmark info (currently unused)
        
    Returns:
        List of dictionaries matching GapAnalysisItem model fields
    """
    gaps = []
    
    fleet_total = sector_profile.get("fleet_total") or 0
    fleet_electric = sector_profile.get("fleet_electric") or 0
    depots = sector_profile.get("depots") or 0
    annual_opex = sector_profile.get("annual_opex_usd") or 0
    
    if fleet_total > 0:
        kenya_electrification = (fleet_electric / fleet_total) * 100
    else:
        kenya_electrification = 0
    
    if fleet_total > 0:
        kenya_depot_coverage = (depots / fleet_total) * 100
    else:
        kenya_depot_coverage = 0
    
    if fleet_total > 0 and annual_opex > 0:
        kenya_opex_per_bus = annual_opex / fleet_total
    else:
        kenya_opex_per_bus = 0
    
    for city, data in BENCHMARK_DATA.items():
        electrification_gap = data["electrification_pct"] - kenya_electrification
        gaps.append({
            "indicator": "Fleet Electrification %",
            "kenya_value": f"{kenya_electrification:.1f}%",
            "benchmark_city": city,
            "benchmark_value": f"{data['electrification_pct']:.1f}%",
            "gap_delta": f"{electrification_gap:+.1f}pp",
            "comparability": data["comparability"],
            "comment": _get_electrification_comment(electrification_gap, city)
        })
    
    primary_cities = ["Shenzhen", "London"]
    for city in primary_cities:
        data = BENCHMARK_DATA[city]
        depot_gap = data["depot_coverage_per_100_buses"] - (kenya_depot_coverage * 100)
        gaps.append({
            "indicator": "Depot Coverage (per 100 buses)",
            "kenya_value": f"{kenya_depot_coverage * 100:.2f}",
            "benchmark_city": city,
            "benchmark_value": f"{data['depot_coverage_per_100_buses']:.1f}",
            "gap_delta": f"{depot_gap:+.2f}",
            "comparability": data["comparability"],
            "comment": _get_depot_comment(depot_gap)
        })
    
    if kenya_opex_per_bus > 0:
        for city in ["Santiago", "London"]:
            data = BENCHMARK_DATA[city]
            opex_gap = kenya_opex_per_bus - data["opex_per_bus_usd"]
            opex_gap_pct = (opex_gap / data["opex_per_bus_usd"]) * 100 if data["opex_per_bus_usd"] > 0 else 0
            gaps.append({
                "indicator": "Operating Cost per Bus (USD/year)",
                "kenya_value": f"${kenya_opex_per_bus:,.0f}",
                "benchmark_city": city,
                "benchmark_value": f"${data['opex_per_bus_usd']:,}",
                "gap_delta": f"{opex_gap_pct:+.1f}%",
                "comparability": data["comparability"],
                "comment": _get_opex_comment(opex_gap_pct, city)
            })
    
    return gaps


def _get_electrification_comment(gap: float, city: str) -> str:
    """Generate contextual comment for electrification gap."""
    if gap > 80:
        return f"Significant gap vs {city}'s world-leading fleet. Full electrification is a long-term goal."
    elif gap > 30:
        return f"Moderate gap vs {city}. Phased electrification program recommended."
    elif gap > 0:
        return f"Small gap vs {city}. On track with regional peers."
    else:
        return f"Ahead of {city} benchmark. Strong progress on electrification."


def _get_depot_comment(gap: float) -> str:
    """Generate contextual comment for depot coverage gap."""
    if gap > 1.0:
        return "Significant infrastructure gap. New depot construction needed for fleet expansion."
    elif gap > 0:
        return "Minor infrastructure gap. Depot upgrades may suffice."
    else:
        return "Adequate depot coverage for current fleet size."


def _get_opex_comment(gap_pct: float, city: str) -> str:
    """Generate contextual comment for operating cost gap."""
    if gap_pct > 20:
        return f"Higher costs than {city}. Efficiency improvements and electrification could reduce OPEX."
    elif gap_pct > 0:
        return f"Slightly higher than {city}. Generally competitive for the region."
    else:
        return f"Lower costs than {city}. Favorable operating environment."
