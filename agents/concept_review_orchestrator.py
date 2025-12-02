"""
Concept Review Orchestrator Agent - Multi-Phase Flow

This module orchestrates the concept review pipeline through 4 interactive phases,
each producing structured data and phase-specific "thinking logs".

Phases:
  1. Sector Profile, Benchmarks & KPIs
  2. Sustainability Assessment
  3. Market Data & Financial Options
  4. Concept Note Draft

DEMO NOTE: This is a demo multi-phase orchestrated agent flow, not production logic.
"""

from typing import Dict, List, Any, Optional
import json
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


# =============================================================================
# DEMO-ONLY MOCK DEFAULTS
# =============================================================================
MOCK_DEFAULTS = {
    "fleet_total": 320,
    "diesel_buses": 300,
    "hybrid_buses": 20,
    "electric_buses": 0,
    "depots": 6,
    "daily_ridership": 240_000,
    "annual_opex_usd": 12_500_000,
    "annual_co2_tons": 18_200,
}


def _fallback(value: Any, key: str) -> Any:
    """
    Returns value if it is non-null. Otherwise, returns a mock default.
    Only replaces None values, not zeros.
    """
    if value is None:
        return MOCK_DEFAULTS.get(key)
    return value


def _build_gap_analysis_with_benchmarks(
    sector_data: Dict[str, Any],
    benchmarks: List[Dict[str, Any]],
    country: str
) -> List[Dict[str, Any]]:
    """Build gap analysis items comparing local data to international benchmarks."""
    gap_items = []
    
    fleet_total = sector_data.get("fleet_total") or 0
    fleet_electric = sector_data.get("fleet_electric") or 0
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
    
    local_opex = sector_data.get("annual_opex_usd") or 0
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
    
    local_ridership = sector_data.get("daily_ridership") or 0
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


# =============================================================================
# PHASE 1: Sector Profile, Benchmarks & KPIs
# =============================================================================
def run_phase1_sectors_and_kpis(case: Case, case_docs: CaseDocuments) -> Dict[str, Any]:
    """
    Phase 1: Parse Sector Profile, compare with international benchmarks, create baseline KPIs.
    
    Returns:
        {
            "sector_profile": dict,
            "gap_items": list,
            "kpis": list,
            "thinking_steps": list,
        }
    """
    thinking_steps = []
    
    sector_data = build_sector_profile(case_docs.sector_profile_text or "")
    
    sector_data["fleet_total"] = _fallback(sector_data.get("fleet_total"), "fleet_total")
    sector_data["fleet_diesel"] = _fallback(sector_data.get("fleet_diesel"), "diesel_buses")
    sector_data["fleet_hybrid"] = _fallback(sector_data.get("fleet_hybrid"), "hybrid_buses")
    sector_data["fleet_electric"] = _fallback(sector_data.get("fleet_electric"), "electric_buses")
    sector_data["depots"] = _fallback(sector_data.get("depots"), "depots")
    sector_data["daily_ridership"] = _fallback(sector_data.get("daily_ridership"), "daily_ridership")
    sector_data["annual_opex_usd"] = _fallback(sector_data.get("annual_opex_usd"), "annual_opex_usd")
    sector_data["annual_co2_tons"] = _fallback(sector_data.get("annual_co2_tons"), "annual_co2_tons")
    
    fleet_total = sector_data.get("fleet_total") or 0
    fleet_diesel = sector_data.get("fleet_diesel") or 0
    fleet_hybrid = sector_data.get("fleet_hybrid") or 0
    fleet_electric = sector_data.get("fleet_electric") or 0
    depots = sector_data.get("depots") or 0
    daily_ridership = sector_data.get("daily_ridership") or 0
    annual_opex = sector_data.get("annual_opex_usd") or 0
    annual_co2 = sector_data.get("annual_co2_tons") or 0
    
    step1_lines = [
        "I started by analysing the Sector Profile document to reconstruct how Nairobi's bus system looks today."
    ]
    
    details = []
    if fleet_total:
        details.append(f"- I identified a total fleet of **{fleet_total:,} buses**.")
    if fleet_diesel:
        details.append(f"- Approximately **{fleet_diesel:,}** of these are conventional diesel buses.")
    if fleet_hybrid:
        details.append(f"- Around **{fleet_hybrid:,}** buses operate as hybrids (diesel-electric).")
    if fleet_electric is not None:
        if fleet_electric == 0:
            details.append(f"- Currently **{fleet_electric}** buses are fully electric, indicating no electrification yet.")
        else:
            details.append(f"- Only **{fleet_electric:,}** buses are fully electric, indicating a small pilot-scale deployment.")
    if depots:
        details.append(f"- I noted around **{depots} depots** supporting the network.")
    if daily_ridership:
        details.append(f"- The system carries roughly **{daily_ridership:,} passenger trips per day**.")
    if annual_opex:
        details.append(f"- Annual operating expenditure is about **${annual_opex:,.0f}**, dominated by fuel and maintenance.")
    if annual_co2:
        details.append(f"- Baseline emissions are approximately **{annual_co2:,.0f} tCO₂ per year** from the current fleet.")
    
    if details:
        step1_lines.append("From this, the key baseline figures I rely on later are:")
        step1_lines.extend(details)
    else:
        step1_lines.append(
            "The document did not expose clear numeric values, so I kept a primarily qualitative picture."
        )
    
    step1_lines.append(
        "These baseline metrics are the starting point for the gap analysis and KPIs."
    )
    
    thinking_steps.append({
        "step": 1,
        "title": "Parsing the Sector Profile document",
        "description": "\n".join(step1_lines),
    })
    
    benchmarks = get_international_benchmarks()
    gap_items = _build_gap_analysis_with_benchmarks(sector_data, benchmarks, case.country)
    
    step2_lines = [
        "Next, I compared Nairobi's indicators against international benchmarks from cities such as Shenzhen, London and Santiago."
    ]
    
    if gap_items:
        electrification_gaps = [g for g in gap_items if "electrification" in (g.get("indicator") or "").lower()]
        cost_per_bus_gaps = [g for g in gap_items if "operating cost per bus" in (g.get("indicator") or "").lower()]
        
        if electrification_gaps:
            g = electrification_gaps[0]
            step2_lines.append(
                f"- For **{g['indicator']}**, Nairobi is at **{g['kenya_value']}**, compared with **{g['benchmark_value']}** in {g['benchmark_city']} "
                f"(classified as a **{g['comparability']}** benchmark). This confirms a large gap in electrification."
            )
        
        if cost_per_bus_gaps:
            g = cost_per_bus_gaps[0]
            step2_lines.append(
                f"- For **{g['indicator']}**, Nairobi's value of **{g['kenya_value']}** vs **{g['benchmark_value']}** in {g['benchmark_city']} "
                "shows that operating costs per bus are higher than in peer systems."
            )
        
        step2_lines.append(
            "Using these comparisons, I tagged indicators as **HIGH**, **MEDIUM** or **LOW** priority gaps."
        )
    
    thinking_steps.append({
        "step": 2,
        "title": "Comparing with international benchmarks",
        "description": "\n".join(step2_lines),
    })
    
    kpis = build_baseline_kpis("", sector_data)
    
    step3_lines = ["Then I translated the baseline and gaps into Key Performance Indicators (KPIs) for the pilot."]
    
    if kpis:
        for kpi in kpis[:3]:
            baseline = kpi.get("baseline_value", "—")
            target = kpi.get("target_value", "—")
            unit = kpi.get("unit", "")
            step3_lines.append(
                f"- I defined **{kpi['name']}** with a baseline of **{baseline} {unit}** and a target of **{target} {unit}**."
            )
        step3_lines.append(
            "Together, these KPIs capture emissions, cost efficiency and service quality."
        )
    
    thinking_steps.append({
        "step": 3,
        "title": "Baselining KPIs",
        "description": "\n".join(step3_lines),
    })
    
    return {
        "sector_profile": sector_data,
        "gap_items": gap_items,
        "kpis": kpis,
        "thinking_steps": thinking_steps,
    }


# =============================================================================
# PHASE 2: Sustainability Assessment
# =============================================================================
def run_phase2_sustainability(case: Case, case_docs: CaseDocuments) -> Dict[str, Any]:
    """
    Phase 2: Assess project sustainability using the Sustainability document.
    
    Returns:
        {
            "sustainability_profile": dict,
            "thinking_steps": list,
        }
    """
    thinking_steps = []
    
    sector_data = build_sector_profile(case_docs.sector_profile_text or "")
    sector_data["annual_co2_tons"] = _fallback(sector_data.get("annual_co2_tons"), "annual_co2_tons")
    baseline_co2 = sector_data.get("annual_co2_tons") or 0
    
    sustainability_data = build_sustainability_profile(
        case_docs.sustainability_text or "",
        baseline_co2
    )
    
    step_lines = ["I assessed the project's sustainability characteristics using the uploaded project document."]
    
    esg_category = sustainability_data.get("category")
    co2_reduction = sustainability_data.get("co2_reduction_tons")
    pm_reduction = sustainability_data.get("pm25_reduction")
    access_notes = sustainability_data.get("accessibility_notes")
    policy_notes = sustainability_data.get("policy_alignment_notes")
    risks = sustainability_data.get("key_risks")
    mitigations = sustainability_data.get("mitigations")
    
    if esg_category:
        step_lines.append(f"- I classified the project as **Category {esg_category}** under E&S screening.")
    if co2_reduction:
        step_lines.append(f"- Based on the baseline, the pilot is expected to reduce emissions by roughly **{co2_reduction:,.0f} tCO₂ per year**.")
    if pm_reduction:
        step_lines.append(f"- I captured indicative **PM₂.₅** reductions as **{pm_reduction}**, improving local air quality.")
    if access_notes:
        step_lines.append(f"- Accessibility: {access_notes}")
    if policy_notes:
        step_lines.append(f"- Policy alignment: {policy_notes}")
    if risks:
        step_lines.append(f"- Key E&S risks include: {risks}")
    if mitigations:
        step_lines.append(f"- Proposed mitigations: {mitigations}")
    
    if not (esg_category or co2_reduction or pm_reduction):
        step_lines.append("The document did not map cleanly to my ESG template, so I captured a qualitative note about environmental intentions.")
    
    thinking_steps.append({
        "step": 1,
        "title": "Assessing project sustainability",
        "description": "\n".join(step_lines),
    })
    
    return {
        "sustainability_profile": sustainability_data,
        "thinking_steps": thinking_steps,
    }


# =============================================================================
# PHASE 3: Market Data & Financial Options
# =============================================================================
def run_phase3_financial_options(case: Case, case_docs: CaseDocuments) -> Dict[str, Any]:
    """
    Phase 3: Retrieve stub market data and generate financial options with scores.
    
    Returns:
        {
            "financial_options": list,
            "market_data": dict,
            "thinking_steps": list,
        }
    """
    thinking_steps = []
    
    market_rates = get_market_rates()
    all_in_rate = market_rates["all_in_green_rate_pct"]
    
    financial_options = build_financial_options(case_docs.need_assessment_text or "")
    
    step_lines = [
        "I looked at market data and proposed financing structures for the project."
    ]
    
    try:
        from services.stub_market_data import get_all_in_10y_green_rate
        base_rate = get_all_in_10y_green_rate() * 100
        step_lines.append(
            f"- Using stubbed Bloomberg data (EUR 10Y swap + green spread), I derived a base 10-year green rate of around **{base_rate:.2f}%**."
        )
    except Exception:
        step_lines.append(
            f"- Using stubbed market data, I derived a base 10-year green rate of around **{all_in_rate:.1f}%**."
        )
    
    if financial_options:
        for idx, opt in enumerate(financial_options):
            label = chr(ord("A") + idx)
            rate_pct = (opt.get("all_in_rate_bps") or 0) / 100.0
            repayment_score = opt.get("repayment_score") or 0
            rate_score = opt.get("rate_score") or 0
            total_score = opt.get("total_score") or 0
            step_lines.append(
                f"- **Option {label} – {opt['name']}**: all-in rate ~**{rate_pct:.2f}%**, "
                f"repayment score **{repayment_score:.1f}**, rate score **{rate_score:.1f}**, total score **{total_score:.1f}**."
            )
        step_lines.append(
            "I ranked these options using the 60/40 rule (60% repayment capacity, 40% rate competitiveness)."
        )
    
    thinking_steps.append({
        "step": 1,
        "title": "Retrieving market data and proposing financial options",
        "description": "\n".join(step_lines),
    })
    
    return {
        "financial_options": financial_options,
        "market_data": market_rates,
        "thinking_steps": thinking_steps,
    }


# =============================================================================
# PHASE 4: Concept Note Draft
# =============================================================================
def run_phase4_concept_note(case: Case, case_docs: CaseDocuments, 
                            sector_data: Dict, gap_items: List, kpis: List,
                            financial_options: List, sustainability_data: Dict) -> Dict[str, Any]:
    """
    Phase 4: Generate the Concept Note draft combining all previous phase outputs.
    
    Returns:
        {
            "concept_note_content": str,
            "thinking_steps": list,
        }
    """
    thinking_steps = []
    
    need_result = parse_need_assessment(case_docs.need_assessment_text or "")
    
    case_dict = {"name": case.name, "country": case.country, "sector": case.sector}
    
    concept_note_content = generate_concept_note(
        case_dict,
        need_result,
        sector_data,
        gap_items,
        kpis,
        financial_options,
        sustainability_data
    )
    
    step_lines = [
        "Finally, I assembled all of this into a draft Concept Note for OPSComm.",
        "- The Note summarises the need, current sector context and gaps.",
        "- It lists the KPIs that will be tracked for the pilot.",
        "- It lays out the three financing options with their scores and trade-offs.",
        "- It concludes with the sustainability assessment and key risks.",
        "This draft is meant as a starting point for human review, not an automated approval."
    ]
    
    thinking_steps.append({
        "step": 1,
        "title": "Generating the Concept Note draft",
        "description": "\n".join(step_lines),
    })
    
    return {
        "concept_note_content": concept_note_content,
        "thinking_steps": thinking_steps,
    }


# =============================================================================
# LEGACY: Full single-shot run (for backwards compatibility)
# =============================================================================
def run_concept_review_for_case(case: Case, case_docs: CaseDocuments) -> Dict[str, Any]:
    """
    Runs the full happy-path Concept Review flow for a case (legacy single-shot mode).
    
    DEPRECATED: Use the phased approach (run_phase1, run_phase2, etc.) for interactive UI.
    """
    phase1 = run_phase1_sectors_and_kpis(case, case_docs)
    phase2 = run_phase2_sustainability(case, case_docs)
    phase3 = run_phase3_financial_options(case, case_docs)
    phase4 = run_phase4_concept_note(
        case, case_docs,
        phase1["sector_profile"],
        phase1["gap_items"],
        phase1["kpis"],
        phase3["financial_options"],
        phase2["sustainability_profile"]
    )
    
    all_thinking_steps = []
    step_counter = 1
    for phase in [phase1, phase2, phase3, phase4]:
        for step in phase.get("thinking_steps", []):
            all_thinking_steps.append({
                "step": step_counter,
                "title": step["title"],
                "description": step["description"],
            })
            step_counter += 1
    
    return {
        "sector_profile": phase1["sector_profile"],
        "gap_items": phase1["gap_items"],
        "kpis": phase1["kpis"],
        "financial_options": phase3["financial_options"],
        "sustainability_profile": phase2["sustainability_profile"],
        "concept_note_content": phase4["concept_note_content"],
        "thinking_steps": all_thinking_steps,
    }


def format_thinking_log_markdown(thinking_steps: List[Dict[str, Any]]) -> str:
    """Format thinking steps as a Markdown string for storage."""
    lines = ["# Agent Thinking Log\n"]
    
    for step in thinking_steps:
        lines.append(f"## Step {step['step']}: {step['title']}\n")
        lines.append(f"{step['description']}\n")
    
    return "\n".join(lines)


def format_phase_thinking_json(thinking_steps: List[Dict[str, Any]]) -> str:
    """Format thinking steps as JSON for phase-specific storage."""
    return json.dumps(thinking_steps, ensure_ascii=False)
