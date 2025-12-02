"""
Stub module for Bloomberg/market data integration.

This module returns mock market data for financial analysis.
TODO: Replace with real Bloomberg API calls for production use.
"""

from typing import Dict, List, Any


def get_peer_median_rates() -> Dict[str, Any]:
    """
    Get median interest rates for peer transactions.
    
    In production, this would query Bloomberg for recent comparable
    transactions in the region and sector.
    
    Returns:
        Dictionary with median rates in basis points for different instruments
    """
    return {
        "sovereign_median": 175,
        "subnational_median": 280,
        "blended_median": 200,
        "commercial_median": 450,
        "benchmark_date": "2024-01-15",
        "region": "Sub-Saharan Africa",
        "sector": "Urban Transport"
    }


def get_peer_deal_structures() -> List[Dict[str, Any]]:
    """
    Get comparable deal structures from peer transactions.
    
    In production, this would query a deals database for recent
    similar transactions.
    
    Returns:
        List of comparable deal summaries
    """
    return [
        {
            "deal_name": "Lagos BRT Modernization",
            "country": "Nigeria",
            "year": 2023,
            "amount_usd": 200_000_000,
            "instrument": "sovereign_loan",
            "tenor_years": 20,
            "grace_years": 5,
            "rate_bps": 185,
            "lender": "AfDB"
        },
        {
            "deal_name": "Addis Ababa Light Rail Extension",
            "country": "Ethiopia",
            "year": 2022,
            "amount_usd": 150_000_000,
            "instrument": "sovereign_loan",
            "tenor_years": 25,
            "grace_years": 7,
            "rate_bps": 165,
            "lender": "World Bank"
        },
        {
            "deal_name": "Cape Town MyCiTi Fleet",
            "country": "South Africa",
            "year": 2023,
            "amount_usd": 100_000_000,
            "instrument": "municipal_bond",
            "tenor_years": 15,
            "grace_years": 3,
            "rate_bps": 320,
            "lender": "Development Bank of Southern Africa"
        },
        {
            "deal_name": "Cairo E-Bus Pilot",
            "country": "Egypt",
            "year": 2024,
            "amount_usd": 75_000_000,
            "instrument": "blended_finance",
            "tenor_years": 18,
            "grace_years": 4,
            "rate_bps": 210,
            "lender": "EBRD + GCF"
        }
    ]


def get_currency_forecasts(currency_pair: str = "USD/KES") -> Dict[str, Any]:
    """
    Get currency forecasts for FX risk assessment.
    
    In production, this would query market data providers for
    forward curves and volatility data.
    
    Args:
        currency_pair: Currency pair code (e.g., "USD/KES")
        
    Returns:
        Dictionary with currency forecast data
    """
    return {
        "pair": currency_pair,
        "spot_rate": 153.50,
        "forecast_1y": 162.00,
        "forecast_3y": 178.00,
        "forecast_5y": 195.00,
        "volatility_1y": 12.5,
        "depreciation_risk": "moderate",
        "hedge_cost_bps": 180
    }


def get_commodity_prices() -> Dict[str, Any]:
    """
    Get relevant commodity prices for cost analysis.
    
    Returns:
        Dictionary with commodity price data
    """
    return {
        "diesel_usd_liter": 1.15,
        "electricity_usd_kwh": 0.12,
        "lithium_carbonate_usd_ton": 25000,
        "steel_usd_ton": 750,
        "as_of_date": "2024-01-15"
    }
