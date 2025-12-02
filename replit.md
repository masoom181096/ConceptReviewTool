# EBRD Concept Review Tool

## Overview
A web application prototyping EBRD's Concept Review Phase automation for large-institution loan requests. This tool implements a happy-path workflow with a simple internal "agentic" architecture where each "agent" is a Python module/function.

## Current State
- **Status**: Fully functional prototype
- **Stack**: Python + FastAPI + SQLite + Jinja2 templates

## Project Structure
```
main.py                 # FastAPI entrypoint, router setup, DB init
database.py             # SQLAlchemy engine/session and Base
models.py               # SQLAlchemy models (8 tables)
schemas.py              # Pydantic models for API I/O

agents/                 # Python agents for data processing
  __init__.py
  need_assessment_agent.py      # Parse need assessment text
  sector_profile_agent.py       # Build sector profile from docs
  gap_analysis_agent.py         # Compare against benchmarks
  baseline_kpi_agent.py         # Derive baseline KPIs
  financial_structuring_agent.py # Build financial options (60/40 scoring)
  sustainability_agent.py       # Build sustainability profile
  concept_note_agent.py         # Generate Markdown concept note

services/               # Stub services for external integrations
  stub_market_data.py   # Mock Bloomberg + peer deals data
  stub_sap_finance.py   # Mock repayment/fiscal metrics

templates/              # Jinja2 HTML templates
  base.html
  cases_list.html
  case_new.html
  case_detail.html
  concept_note.html

static/
  styles.css            # CSS styling
```

## Data Model
1. **Case** - Main project entity (name, country, sector, status)
2. **CaseDocuments** - Raw text inputs for each document type
3. **SectorProfile** - Parsed fleet and operational metrics
4. **GapAnalysisItem** - Comparison against international benchmarks
5. **BaselineKPI** - Key performance indicators with targets
6. **FinancialOption** - Financing structures with 60/40 scoring
7. **SustainabilityProfile** - ESG category and environmental metrics
8. **ConceptNote** - Generated Markdown document

## Workflow
1. Create a Case (name, country, sector)
2. Input raw text for each document category
3. Click "Run Agents & Generate Concept Note"
4. Review parsed data tables and Concept Note
5. Submit OPSCOMM decision (Approve/Reject)

## Financial Scoring (60/40 Rule)
- **60%**: Repayment capacity (DSCR, FX risk, debt ratios)
- **40%**: Rate competitiveness vs peer median

## Key Features
- Case management with status tracking (NEW, IN_REVIEW, APPROVED, ARCHIVED)
- Multi-stage document input forms
- Automated agent pipeline for data extraction
- Gap analysis against international cities (Shenzhen, London, Santiago, Bogota)
- Three financial options: Sovereign Loan, Guaranteed City Loan, Blended Co-Financing
- Markdown-based Concept Note generation
- OPSCOMM decision workflow

## Future Enhancements
- Replace deterministic agents with LLM integration
- Add real Bloomberg/SAP API connections
- Implement user authentication
- Add document upload for PDF/Word
- Export functionality (PDF, Excel)
