"""
Stub module for international benchmark data.

This module provides hardcoded benchmark data derived from IEA 
and other international sources for gap analysis.
TODO: Replace with real data sources for production use.
"""

from typing import Dict, List, Any


def get_international_benchmarks() -> List[Dict[str, Any]]:
    """
    Get international benchmark data for e-bus cities.
    
    Data derived from IEA Global EV Outlook and city transport reports.
    
    Returns:
        List of city benchmark dictionaries
    """
    return [
        {
            "city": "Shenzhen",
            "country": "China",
            "fleet_total": 16359,
            "fleet_electric": 16359,
            "electrification_pct": 100.0,
            "cost_per_bus_usd": 32000,
            "annual_co2_reduction_pct": 48.0,
            "daily_ridership_per_bus": 850,
            "notes": "First major city to achieve 100% e-bus fleet (2017)"
        },
        {
            "city": "London",
            "country": "UK",
            "fleet_total": 9000,
            "fleet_electric": 3150,
            "electrification_pct": 35.0,
            "cost_per_bus_usd": 45000,
            "annual_co2_reduction_pct": 15.0,
            "daily_ridership_per_bus": 620,
            "notes": "Target: 100% zero-emission by 2034"
        },
        {
            "city": "Santiago",
            "country": "Chile",
            "fleet_total": 6800,
            "fleet_electric": 1360,
            "electrification_pct": 20.0,
            "cost_per_bus_usd": 38000,
            "annual_co2_reduction_pct": 12.0,
            "daily_ridership_per_bus": 720,
            "notes": "Largest e-bus fleet in Latin America"
        },
        {
            "city": "Bogota",
            "country": "Colombia",
            "fleet_total": 8200,
            "fleet_electric": 1148,
            "electrification_pct": 14.0,
            "cost_per_bus_usd": 36000,
            "annual_co2_reduction_pct": 8.0,
            "daily_ridership_per_bus": 680,
            "notes": "TransMilenio BRT electrification ongoing"
        }
    ]


def get_benchmark_for_indicator(indicator: str) -> Dict[str, Any]:
    """
    Get benchmark values for a specific indicator across cities.
    
    Args:
        indicator: The indicator name (e.g., 'electrification_pct')
        
    Returns:
        Dictionary mapping city names to their values
    """
    benchmarks = get_international_benchmarks()
    result = {}
    for city_data in benchmarks:
        if indicator in city_data:
            result[city_data["city"]] = city_data[indicator]
    return result


def get_best_practice_city(indicator: str, higher_is_better: bool = True) -> Dict[str, Any]:
    """
    Get the best practice city for a specific indicator.
    
    Args:
        indicator: The indicator name
        higher_is_better: If True, higher values are better
        
    Returns:
        The city data dictionary for the best performer
    """
    benchmarks = get_international_benchmarks()
    
    valid_cities = [b for b in benchmarks if indicator in b and b[indicator] is not None]
    if not valid_cities:
        return benchmarks[0]
    
    if higher_is_better:
        return max(valid_cities, key=lambda x: x[indicator])
    else:
        return min(valid_cities, key=lambda x: x[indicator])


EUR_SWAP_10Y = 0.02
GREEN_BOND_SPREAD_10Y = 0.006


def get_market_rates() -> Dict[str, float]:
    """
    Get current market rates for financial calculations.
    
    Returns:
        Dictionary with swap rates and spreads
    """
    return {
        "eur_swap_10y": EUR_SWAP_10Y,
        "green_bond_spread_10y": GREEN_BOND_SPREAD_10Y,
        "all_in_green_rate_10y": EUR_SWAP_10Y + GREEN_BOND_SPREAD_10Y,
        "all_in_green_rate_pct": (EUR_SWAP_10Y + GREEN_BOND_SPREAD_10Y) * 100
    }
