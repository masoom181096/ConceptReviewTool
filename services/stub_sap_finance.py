"""
Stub module for SAP/financial data integration.

This module returns mock financial indicators for repayment analysis.
TODO: Replace with real SAP API calls for production use.
"""

from typing import Dict, Any


def get_repayment_indicators() -> Dict[str, Any]:
    """
    Get repayment capacity indicators for financial scoring.
    
    In production, this would query SAP for actual government
    and municipal financial data.
    
    Returns:
        Dictionary with financial indicators for scoring
    """
    return {
        "sovereign_dscr": 1.8,
        "sovereign_fx_risk": "medium",
        "sovereign_debt_ratio": 0.55,
        "sovereign_budget_balance_pct": -4.2,
        "sovereign_reserves_months": 4.5,
        
        "city_dscr": 1.4,
        "city_fx_risk": "high",
        "city_debt_ratio": 0.35,
        "city_own_revenue_ratio": 0.45,
        "city_transfer_dependency": 0.55,
        
        "assessment_date": "2024-01-15",
        "data_source": "Ministry of Finance / City Authority"
    }


def get_fiscal_projections(country: str = "Kenya") -> Dict[str, Any]:
    """
    Get fiscal projections for the country.
    
    In production, this would query SAP/Monarch for IMF
    and government projections.
    
    Args:
        country: Country name
        
    Returns:
        Dictionary with fiscal projection data
    """
    return {
        "country": country,
        "gdp_growth_2024": 5.2,
        "gdp_growth_2025": 5.5,
        "gdp_growth_2026": 5.7,
        "inflation_2024": 6.8,
        "inflation_2025": 5.5,
        "debt_to_gdp_2024": 68.5,
        "debt_to_gdp_2025": 66.0,
        "primary_balance_2024": -1.2,
        "primary_balance_2025": -0.5,
        "source": "IMF WEO October 2023 + Staff Projections"
    }


def get_debt_sustainability_analysis(country: str = "Kenya") -> Dict[str, Any]:
    """
    Get debt sustainability analysis summary.
    
    In production, this would pull from SAP/Monarch with
    latest IMF DSA results.
    
    Args:
        country: Country name
        
    Returns:
        Dictionary with DSA summary
    """
    return {
        "country": country,
        "dsa_rating": "Moderate",
        "pv_debt_to_gdp": 52.3,
        "pv_debt_to_exports": 185.0,
        "debt_service_to_revenue": 28.5,
        "stress_test_breaches": 1,
        "key_risks": [
            "Exchange rate depreciation shock",
            "Contingent liabilities from SOEs"
        ],
        "last_update": "2023-09-01",
        "source": "IMF DSA - September 2023"
    }


def get_project_cashflow_model(
    principal: float,
    tenor: int,
    grace: int,
    rate_bps: float
) -> Dict[str, Any]:
    """
    Generate simplified cashflow model for the project.
    
    Args:
        principal: Loan principal in USD
        tenor: Loan tenor in years
        grace: Grace period in years
        rate_bps: Interest rate in basis points
        
    Returns:
        Dictionary with cashflow projections
    """
    rate = rate_bps / 10000
    
    repayment_years = tenor - grace
    annual_principal = principal / repayment_years if repayment_years > 0 else 0
    
    cashflows = []
    outstanding = principal
    
    for year in range(1, tenor + 1):
        interest = outstanding * rate
        
        if year <= grace:
            principal_payment = 0
        else:
            principal_payment = annual_principal
            outstanding -= principal_payment
        
        total_payment = interest + principal_payment
        
        cashflows.append({
            "year": year,
            "principal_payment": round(principal_payment, 2),
            "interest_payment": round(interest, 2),
            "total_payment": round(total_payment, 2),
            "outstanding_balance": round(max(0, outstanding), 2)
        })
    
    total_interest = sum(cf["interest_payment"] for cf in cashflows)
    total_repayment = principal + total_interest
    
    return {
        "principal": principal,
        "tenor_years": tenor,
        "grace_years": grace,
        "rate_bps": rate_bps,
        "total_interest": round(total_interest, 2),
        "total_repayment": round(total_repayment, 2),
        "annual_cashflows": cashflows
    }
