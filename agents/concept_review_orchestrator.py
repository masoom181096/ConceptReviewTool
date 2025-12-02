"""
Concept Review Orchestrator Agent

This module orchestrates the full concept review pipeline, running all agents
in sequence and producing both structured data and a human-readable "thinking log".
"""

from typing import Dict, List, Any
from models import Case, CaseDocuments
from agents import (
    parse_need_assessment,
    build_sector_profile,
    build_gap_analysis,
    build_baseline_kpis,
    build_financial_options,
    build_sustainability_profile,
    generate_concept_note
)
from services.stub_international_benchmarks import (
    get_international_benchmarks,
    get_market_rates
)


def run_concept_review_for_case(case: Case, case_docs: CaseDocuments) -> Dict[str, Any]:
    """
    Runs the full happy-path Concept Review flow for a case.
    
    This orchestrator executes all agents in sequence, using deterministic
    logic (no LLM calls) and produces structured data plus a thinking log.
    
    Args:
        case: The Case model instance
        case_docs: The CaseDocuments model instance with input texts
        
    Returns:
        Dictionary with keys:
          - 'sector_profile': dict of sector profile data
          - 'gap_items': list of gap analysis items
          - 'kpis': list of baseline KPIs
          - 'financial_options': list of financial options with scores
          - 'sustainability_profile': dict of sustainability data
          - 'concept_note_content': Markdown string
          - 'thinking_steps': list of step descriptions for UI
    """
    thinking_steps = []
    
    need_result = parse_need_assessment(case_docs.need_assessment_text or "")
    
    sector_data = build_sector_profile(case_docs.sector_profile_text or "")
    
    fleet_total = sector_data.get("fleet_total", 0) or 0
    annual_co2 = sector_data.get("annual_co2_tons", 0) or 0
    daily_ridership = sector_data.get("daily_ridership", 0) or 0
    annual_opex = sector_data.get("annual_opex_usd", 0) or 0
    fleet_electric = sector_data.get("fleet_electric", 0) or 0
    
    thinking_steps.append({
        "step": 1,
        "title": "Parsing Sector Profile document",
        "description": f"I extracted fleet size ({fleet_total} buses), baseline emissions "
                       f"({annual_co2:,.0f} tCO2/year), daily ridership (~{daily_ridership:,} passengers) "
                       f"and OPEX (${annual_opex:,.0f} USD) from the sector profile document."
    })
    
    benchmarks = get_international_benchmarks()
    
    electrification_pct = (fleet_electric / fleet_total * 100) if fleet_total > 0 else 0
    
    benchmark_comparison = []
    for bm in benchmarks:
        benchmark_comparison.append(f"{bm['city']} {bm['electrification_pct']:.0f}%")
    benchmark_str = ", ".join(benchmark_comparison)
    
    thinking_steps.append({
        "step": 2,
        "title": "Comparing with international benchmarks",
        "description": f"I compared {case.country}'s {electrification_pct:.0f}% electric buses "
                       f"to benchmarks ({benchmark_str}) and identified a large electrification gap "
                       f"and potential for operational cost improvements."
    })
    
    gap_items = _build_gap_analysis_with_benchmarks(sector_data, benchmarks, case.country)
    
    kpis = build_baseline_kpis("", sector_data)
    
    thinking_steps.append({
        "step": 3,
        "title": "Baselining KPIs",
        "description": f"Using the fleet and ridership data, I defined KPIs for CO2 emissions, "
                       f"operating cost per bus, and ridership per bus, and set initial targets "
                       f"such as a 30-40% reduction in emissions through fleet electrification."
    })
    
    market_rates = get_market_rates()
    all_in_rate = market_rates["all_in_green_rate_pct"]
    
    financial_options = build_financial_options(case_docs.need_assessment_text or "")
    
    thinking_steps.append({
        "step": 4,
        "title": "Retrieving market data and proposing financial options",
        "description": f"Using stubbed Bloomberg data (EUR_SWAP_10Y = {market_rates['eur_swap_10y']*100:.1f}%, "
                       f"GREEN_BOND_SPREAD_10Y = {market_rates['green_bond_spread_10y']*100:.1f}%), "
                       f"I computed a {all_in_rate:.1f}% all-in 10-year green rate and constructed "
                       f"three financing options, scoring them using a 60/40 weighting "
                       f"(repayment capacity / interest rate)."
    })
    
    baseline_co2 = sector_data.get("annual_co2_tons", 0) or 0
    sustainability_data = build_sustainability_profile(
        case_docs.sustainability_text or "",
        baseline_co2
    )
    
    thinking_steps.append({
        "step": 5,
        "title": "Assessing project sustainability",
        "description": f"I parsed the project sustainability document to capture expected CO2 "
                       f"and PM reductions, accessibility improvements, and key ESG risks and "
                       f"mitigations, and summarised alignment with EBRD's green objectives."
    })
    
    case_dict = {"name": case.name, "country": case.country, "sector": case.sector}
    sector_dict = sector_data
    
    gaps_list = gap_items
    kpis_list = kpis
    
    options_list = financial_options
    
    sustainability_dict = sustainability_data
    
    concept_note_content = generate_concept_note(
        case_dict,
        need_result,
        sector_dict,
        gaps_list,
        kpis_list,
        options_list,
        sustainability_dict
    )
    
    thinking_steps.append({
        "step": 6,
        "title": "Generating the Concept Note draft",
        "description": "I combined all structured elements (sector profile, gaps, KPIs, "
                       "financing options, and sustainability assessment) into a draft "
                       "Concept Note for OPSCOMM review."
    })
    
    return {
        "sector_profile": sector_data,
        "gap_items": gap_items,
        "kpis": kpis,
        "financial_options": financial_options,
        "sustainability_profile": sustainability_data,
        "concept_note_content": concept_note_content,
        "thinking_steps": thinking_steps
    }


def _build_gap_analysis_with_benchmarks(
    sector_data: Dict[str, Any],
    benchmarks: List[Dict[str, Any]],
    country: str
) -> List[Dict[str, Any]]:
    """
    Build gap analysis items comparing local data to international benchmarks.
    """
    gap_items = []
    
    fleet_total = sector_data.get("fleet_total", 0) or 0
    fleet_electric = sector_data.get("fleet_electric", 0) or 0
    local_electrification = (fleet_electric / fleet_total * 100) if fleet_total > 0 else 0
    
    for bm in benchmarks[:2]:
        gap_items.append({
            "indicator": "E-Bus Electrification Rate",
            "kenya_value": f"{local_electrification:.0f}%",
            "benchmark_city": bm["city"],
            "benchmark_value": f"{bm['electrification_pct']:.0f}%",
            "gap_delta": f"-{bm['electrification_pct'] - local_electrification:.0f}%",
            "comparability": "LOW" if bm["electrification_pct"] > 50 else "MEDIUM",
            "comment": f"{bm['city']} achieved this through aggressive policy support"
        })
    
    local_opex = sector_data.get("annual_opex_usd", 0) or 0
    local_opex_per_bus = (local_opex / fleet_total) if fleet_total > 0 else 45000
    
    for bm in benchmarks[:2]:
        gap_items.append({
            "indicator": "Operating Cost per Bus (USD/year)",
            "kenya_value": f"${local_opex_per_bus:,.0f}",
            "benchmark_city": bm["city"],
            "benchmark_value": f"${bm['cost_per_bus_usd']:,}",
            "gap_delta": f"+${local_opex_per_bus - bm['cost_per_bus_usd']:,.0f}",
            "comparability": "MEDIUM",
            "comment": "Electric buses have lower operating costs"
        })
    
    local_ridership = sector_data.get("daily_ridership", 0) or 0
    local_ridership_per_bus = (local_ridership / fleet_total) if fleet_total > 0 else 500
    
    best_ridership = max(benchmarks, key=lambda x: x["daily_ridership_per_bus"])
    gap_items.append({
        "indicator": "Daily Ridership per Bus",
        "kenya_value": f"{local_ridership_per_bus:,.0f}",
        "benchmark_city": best_ridership["city"],
        "benchmark_value": f"{best_ridership['daily_ridership_per_bus']:,}",
        "gap_delta": f"{local_ridership_per_bus - best_ridership['daily_ridership_per_bus']:+,.0f}",
        "comparability": "HIGH",
        "comment": "Ridership efficiency varies by route density"
    })
    
    return gap_items


def format_thinking_log_markdown(thinking_steps: List[Dict[str, Any]]) -> str:
    """
    Format thinking steps as a Markdown string for storage.
    """
    lines = ["# Agent Thinking Log\n"]
    
    for step in thinking_steps:
        lines.append(f"## Step {step['step']}: {step['title']}\n")
        lines.append(f"{step['description']}\n")
    
    return "\n".join(lines)
