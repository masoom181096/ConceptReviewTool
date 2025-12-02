from typing import Dict, Any, List, Optional
from datetime import datetime


def generate_concept_note(
    case: Dict[str, Any],
    need_summary: Dict[str, Any],
    sector_profile: Dict[str, Any],
    gaps: List[Dict[str, Any]],
    kpis: List[Dict[str, Any]],
    options: List[Dict[str, Any]],
    sustainability: Dict[str, Any]
) -> str:
    """
    Generate a complete Concept Note in Markdown format.
    
    Assembles all analyzed data into a structured document for OPSCOMM review.
    TODO: Replace template-based generation with LLM-assisted drafting for production.
    
    Args:
        case: Case information (name, country, sector)
        need_summary: Parsed need assessment data
        sector_profile: Sector profile metrics
        gaps: Gap analysis items
        kpis: Baseline KPI list
        options: Financial structuring options
        sustainability: Sustainability profile data
        
    Returns:
        Markdown-formatted Concept Note string
    """
    sections = []
    
    sections.append(_build_header(case))
    sections.append(_build_executive_summary(case, need_summary, options))
    sections.append(_build_need_assessment(need_summary))
    sections.append(_build_sector_profile(sector_profile))
    sections.append(_build_gap_analysis(gaps))
    sections.append(_build_kpis(kpis))
    sections.append(_build_financial_options(options))
    sections.append(_build_sustainability(sustainability))
    sections.append(_build_recommendation(options))
    
    return "\n\n".join(sections)


def _build_header(case: Dict[str, Any]) -> str:
    """Build document header."""
    date_str = datetime.utcnow().strftime("%B %d, %Y")
    return f"""# EBRD Concept Note

**Project:** {case.get('name', 'Untitled Project')}  
**Country:** {case.get('country', 'Not specified')}  
**Sector:** {case.get('sector', 'Not specified')}  
**Date:** {date_str}  
**Status:** Concept Review Phase

---"""


def _build_executive_summary(case: Dict, need: Dict, options: List[Dict]) -> str:
    """Build executive summary section."""
    project_name = case.get('name', 'the proposed project')
    country = case.get('country', 'the country')
    
    principal = options[0].get('principal_amount_usd') if options else 0
    principal = principal or 0
    principal_str = f"${principal/1e6:.0f} million" if principal > 0 else "amount to be determined"
    
    best_option = max(options, key=lambda x: x.get('total_score', 0)) if options else None
    best_option_name = best_option.get('name', 'to be determined') if best_option else 'to be determined'
    
    problem = need.get('problem_summary', 'addressing urban transport modernization needs')
    
    return f"""## 1. Executive Summary

This Concept Note presents **{project_name}** in **{country}** for EBRD consideration.

**Financing Request:** {principal_str}

**Project Objective:** {problem}

**Recommended Financing Structure:** Based on the 60/40 scoring methodology (60% repayment capacity, 40% rate competitiveness), the analysis indicates **{best_option_name}** as the preferred option.

This project aligns with EBRD's Green Economy Transition mandate and supports the country's climate commitments."""


def _build_need_assessment(need: Dict) -> str:
    """Build need assessment section."""
    problem = need.get('problem_summary', 'The project addresses critical urban transport infrastructure needs.')
    amount = need.get('requested_amount_usd') or 0
    amount_str = f"${amount/1e6:.0f} million" if amount > 0 else "To be determined"
    
    return f"""## 2. Need Assessment

### 2.1 Problem Statement
{problem}

### 2.2 Requested Financing
**Amount:** {amount_str}

### 2.3 Expected Outcomes
- Modernization of urban bus fleet
- Reduction in carbon emissions and local air pollution  
- Improved public transport service quality
- Enhanced financial sustainability of transport operations"""


def _build_sector_profile(profile: Dict) -> str:
    """Build sector profile section."""
    fleet_total = profile.get('fleet_total') or 'N/A'
    fleet_diesel = profile.get('fleet_diesel') or 'N/A'
    fleet_hybrid = profile.get('fleet_hybrid') or 'N/A'
    fleet_electric = profile.get('fleet_electric')
    fleet_electric = fleet_electric if fleet_electric is not None else 'N/A'
    depots = profile.get('depots') or 'N/A'
    ridership = profile.get('daily_ridership')
    ridership_str = f"{ridership:,}" if ridership else "N/A"
    opex = profile.get('annual_opex_usd') or 0
    opex_str = f"${opex/1e6:.1f}M" if opex and opex > 0 else "N/A"
    co2 = profile.get('annual_co2_tons')
    co2_str = f"{co2:,}" if co2 else "N/A"
    notes = profile.get('notes', '')
    
    return f"""## 3. Sector Profile - Baseline

### 3.1 Fleet Composition

| Metric | Current Value |
|--------|---------------|
| Total Fleet | {fleet_total} buses |
| Diesel Buses | {fleet_diesel} |
| Hybrid Buses | {fleet_hybrid} |
| Electric Buses | {fleet_electric} |
| Depots | {depots} |

### 3.2 Operational Metrics

| Metric | Current Value |
|--------|---------------|
| Daily Ridership | {ridership_str} passengers | 
| Annual OPEX | {opex_str} |
| Annual CO2 Emissions | {co2_str} tons |

### 3.3 Key Observations
{notes if notes else 'Fleet requires significant modernization to meet climate targets and service quality standards.'}"""


def _build_gap_analysis(gaps: List[Dict]) -> str:
    """Build gap analysis section with table."""
    if not gaps:
        return """## 4. Gap Analysis

*Gap analysis pending - requires sector profile data.*"""
    
    rows = []
    for gap in gaps:
        indicator = gap.get('indicator', '')
        kenya = gap.get('kenya_value', '')
        city = gap.get('benchmark_city', '')
        benchmark = gap.get('benchmark_value', '')
        delta = gap.get('gap_delta', '')
        comp = gap.get('comparability', '')
        rows.append(f"| {indicator} | {kenya} | {city} | {benchmark} | {delta} | {comp} |")
    
    table = "\n".join(rows)
    
    return f"""## 4. Gap Analysis

Comparison with international peer cities to identify improvement opportunities.

| Indicator | Kenya Value | Benchmark City | Benchmark Value | Gap | Comparability |
|-----------|-------------|----------------|-----------------|-----|---------------|
{table}

### 4.1 Key Findings
- Significant electrification gap compared to leading cities
- Opportunity to leapfrog to zero-emission technology
- Infrastructure gaps addressable through project investments"""


def _build_kpis(kpis: List[Dict]) -> str:
    """Build baseline KPIs section."""
    if not kpis:
        return """## 5. Baseline KPIs

*KPI analysis pending - requires operational data.*"""
    
    rows = []
    for kpi in kpis:
        name = kpi.get('name', '')
        baseline = kpi.get('baseline_value', '')
        unit = kpi.get('unit', '')
        target = kpi.get('target_value', '')
        category = kpi.get('category', '')
        rows.append(f"| {name} | {baseline} | {unit} | {target} | {category} |")
    
    table = "\n".join(rows)
    
    return f"""## 5. Baseline KPIs

Key performance indicators for project monitoring and evaluation.

| KPI | Baseline | Unit | Target | Category |
|-----|----------|------|--------|----------|
{table}

### 5.1 Monitoring Framework
Progress against targets will be monitored through:
- Quarterly operational reports
- Annual environmental audits  
- Mid-term and completion evaluations"""


def _build_financial_options(options: List[Dict]) -> str:
    """Build financial options section with comprehensive comparison table and trade-offs."""
    if not options:
        return """## 6. Financing Options and Trade-offs

*Financial analysis pending - requires input data.*"""
    
    sorted_options = sorted(options, key=lambda x: x.get('total_score', 0), reverse=True)
    
    table_rows = []
    for idx, opt in enumerate(sorted_options):
        label = chr(ord('A') + idx)
        name = opt.get('name', 'Unknown Instrument')
        tenor = opt.get('tenor_years', 'N/A')
        grace = opt.get('grace_period_years', 'N/A')
        rate_bps = opt.get('all_in_rate_bps', 0)
        rate_pct = f"{rate_bps/100:.2f}%" if rate_bps else "N/A"
        total = opt.get('total_score', 0)
        pros = opt.get('pros', 'N/A')
        cons = opt.get('cons', 'N/A')
        
        table_rows.append(
            f"| {label} | {name} | {tenor}y / {grace}y grace | {rate_pct} | {total:.1f} | {pros} | {cons} |"
        )
    
    summary_table = "\n".join(table_rows)
    
    best_label = "A"
    best_name = sorted_options[0].get('name', 'the preferred option') if sorted_options else 'the preferred option'
    
    option_narratives = []
    for idx, opt in enumerate(sorted_options):
        label = chr(ord('A') + idx)
        name = opt.get('name', 'Unknown Instrument')
        pros_short = opt.get('pros', '').split(';')[0] if opt.get('pros') else ''
        cons_short = opt.get('cons', '').split(';')[0] if opt.get('cons') else ''
        option_narratives.append(f"- **Option {label}** ({name}): {pros_short}. Trade-off: {cons_short}.")
    
    narratives_text = "\n".join(option_narratives)
    
    detail_sections = []
    for idx, opt in enumerate(sorted_options):
        label = chr(ord('A') + idx)
        name = opt.get('name', 'Unknown Instrument')
        instrument = opt.get('instrument_type', 'N/A')
        principal = opt.get('principal_amount_usd') or 0
        principal_str = f"${principal/1e6:.0f}M" if principal > 0 else "N/A"
        tenor = opt.get('tenor_years', 'N/A')
        grace = opt.get('grace_period_years', 'N/A')
        rate = opt.get('all_in_rate_bps', 'N/A')
        rate_score = opt.get('rate_score', 'N/A')
        repay_score = opt.get('repayment_score', 'N/A')
        total = opt.get('total_score', 'N/A')
        pros = opt.get('pros', 'N/A')
        cons = opt.get('cons', 'N/A')
        
        detail_sections.append(f"""### 6.{idx+2} Option {label}: {name}

| Parameter | Value |
|-----------|-------|
| Instrument Type | {instrument} |
| Principal Amount | {principal_str} |
| Tenor | {tenor} years |
| Grace Period | {grace} years |
| All-in Rate | {rate} bps |

**Scoring (60% Repayment / 40% Rate):**
- Repayment Score: **{repay_score}**/100
- Rate Score: **{rate_score}**/100
- **Total Score: {total}/100**

**Key Benefits:** {pros}

**Key Trade-offs:** {cons}""")
    
    return f"""## 6. Financing Options and Trade-offs

The following financing structures have been identified for this project. Scores are based on a 60/40 weighting of repayment capacity (60%) and interest rate attractiveness (40%).

### 6.1 Summary Comparison

| Option | Instrument | Tenor / Grace | All-in Rate | Total Score | Key Benefits | Key Trade-offs |
|--------|------------|---------------|-------------|-------------|--------------|----------------|
{summary_table}

### Decision Framework

Based on the scoring, **{best_name}** currently ranks highest. However, the choice involves important trade-offs:

{narratives_text}

**OPSCOMM is invited to select the most appropriate option or request a variation based on policy and risk considerations.**

{chr(10).join(detail_sections)}"""


def _build_sustainability(sustainability: Dict) -> str:
    """Build sustainability and ESG section."""
    category = sustainability.get('category', 'B')
    co2_reduction = sustainability.get('co2_reduction_tons', 0)
    co2_str = f"{co2_reduction:,.0f} tons/year" if co2_reduction else "To be quantified"
    pm25 = sustainability.get('pm25_reduction', 'To be quantified')
    accessibility = sustainability.get('accessibility_notes', 'To be assessed')
    policy = sustainability.get('policy_alignment_notes', 'To be assessed')
    risks = sustainability.get('key_risks', 'To be assessed')
    mitigations = sustainability.get('mitigations', 'To be developed')
    
    return f"""## 7. Sustainability & ESG

### 7.1 Environmental & Social Category
**Category {category}** - {'Significant potential impacts requiring comprehensive assessment' if category == 'A' else 'Moderate impacts, manageable through standard mitigation measures' if category == 'B' else 'Minimal or no adverse impacts'}

### 7.2 Environmental Benefits

| Impact Area | Expected Outcome |
|-------------|------------------|
| CO2 Reduction | {co2_str} |
| Air Quality (PM2.5) | {pm25} |

### 7.3 Social Impact
{accessibility}

### 7.4 Policy Alignment
{policy}

### 7.5 Key Risks
{risks}

### 7.6 Mitigation Measures
{mitigations}"""


def _build_recommendation(options: List[Dict]) -> str:
    """Build recommendation section."""
    if not options:
        best_option = "the preferred financing structure (pending analysis)"
    else:
        sorted_options = sorted(options, key=lambda x: x.get('total_score', 0), reverse=True)
        best_option = sorted_options[0].get('name', 'the highest-scoring option')
        best_score = sorted_options[0].get('total_score', 'N/A')
    
    return f"""## 8. Recommendation

### 8.1 Preferred Option
Based on the 60/40 scoring analysis, **{best_option}** achieves the highest combined score and is recommended for further development.

### 8.2 Next Steps
1. OPSCOMM review and decision
2. If approved, proceed to detailed appraisal phase
3. Engage with government counterparts on preferred structure
4. Initiate due diligence and environmental assessment

### 8.3 Decision Required
**OPSCOMM to choose one of the presented options or propose an alternative structure.**

---

*This Concept Note was generated by the EBRD Concept Review Tool. All figures are preliminary and subject to verification during appraisal.*"""
