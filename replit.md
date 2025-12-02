# EBRD Concept Review Tool

## Overview
A web application prototyping EBRD's Concept Review Phase automation for large-institution loan requests. This tool implements a happy-path workflow with a simple internal "agentic" architecture where each "agent" is a Python module/function.

## Current State
- **Status**: Fully functional prototype with email-first intake flow
- **Stack**: Python + FastAPI + SQLite + Jinja2 templates

## Project Structure
```
main.py                 # FastAPI entrypoint, router setup, DB init
database.py             # SQLAlchemy engine/session and Base
models.py               # SQLAlchemy models (8 tables)
schemas.py              # Pydantic models for API I/O

agents/                 # Python agents for data processing
  __init__.py
  need_assessment_agent.py          # Parse need assessment text
  sector_profile_agent.py           # Build sector profile from docs
  gap_analysis_agent.py             # Compare against benchmarks
  baseline_kpi_agent.py             # Derive baseline KPIs
  financial_structuring_agent.py    # Build financial options (60/40 scoring)
  sustainability_agent.py           # Build sustainability profile
  concept_note_agent.py             # Generate Markdown concept note
  concept_review_orchestrator.py    # Orchestrate full agent pipeline

services/               # Stub services for external integrations
  stub_market_data.py               # Mock Bloomberg + peer deals data
  stub_sap_finance.py               # Mock repayment/fiscal metrics
  stub_international_benchmarks.py  # IEA benchmark data (Shenzhen, London, etc.)

utils/                  # Utility modules
  document_parsing.py   # Extract text from .docx and .txt uploads

templates/              # Jinja2 HTML templates
  base.html
  intake.html                # Email-first intake page
  case_new.html              # Blank case creation
  case_new_from_intake.html  # Case creation from parsed email
  cases_list.html
  case_detail.html
  concept_note.html

static/
  styles.css            # CSS styling
```

## Data Model
1. **Case** - Main project entity (name, country, sector, status, agent_thinking_log)
2. **CaseDocuments** - Raw text inputs for each document type
3. **SectorProfile** - Parsed fleet and operational metrics
4. **GapAnalysisItem** - Comparison against international benchmarks
5. **BaselineKPI** - Key performance indicators with targets
6. **FinancialOption** - Financing structures with 60/40 scoring
7. **SustainabilityProfile** - ESG category and environmental metrics
8. **ConceptNote** - Generated Markdown document

## Workflow
1. **Email-First Intake**: Paste client email/MoM on the home page
2. **Pre-filled Case Creation**: System extracts project name, country from email
3. **Upload Documents**: Only Sector Profile + Sustainability docs required
4. **Run Concept Review Agent**: Single button triggers full pipeline
5. **Review Agent Thinking**: See step-by-step reasoning log
6. **Review Results**: Sector Profile, Gap Analysis, KPIs, Financial Options
7. **View Concept Note**: Generated Markdown document
8. **OPSCOMM Decision**: Approve or reject the case

## Financial Scoring (60/40 Rule)
- **60%**: Repayment capacity (DSCR, FX risk, debt ratios)
- **40%**: Rate competitiveness vs peer median

## International Benchmarks (IEA Data)
- Shenzhen: 100% electric, $32k/bus
- London: 35% electric, $45k/bus
- Santiago: 20% electric, $38k/bus
- Bogota: 14% electric, $36k/bus

## Market Data (Stubbed Bloomberg)
- EUR_SWAP_10Y = 2.0%
- GREEN_BOND_SPREAD_10Y = 0.6%
- All-in 10-year green rate = 2.6%

## Key Features
- **Email-First Intake**: Start reviews by pasting client communication
- **Streaming Agent Thinking**: Animated step-by-step reasoning with typing effect
- **Document Upload**: Upload .docx or .txt files (Sector Profile + Sustainability)
- **Automated Agent Pipeline**: Concept Review Orchestrator runs all agents
- **Gap Analysis**: Automatic comparison against IEA benchmark cities
- **Three Financial Options**: Sovereign Loan, Guaranteed City Loan, Blended Co-Financing
- **Financial Trade-offs Table**: Side-by-side comparison of all options with pros/cons
- **Markdown Concept Note**: Auto-generated with all structured data
- **OPSCOMM Decision Workflow**: Approve/Reject cases
- **Local-Runnable**: No external APIs or Replit-specific code

## Recent Changes (Dec 2024)
- Added email-first intake flow with need assessment parsing
- Simplified document uploads to only Sector Profile + Sustainability
- Created Concept Review Orchestrator for full agent pipeline
- Added Agent Thinking Log with predetermined templated steps
- Added international benchmarks stub service with IEA data
- Added README.md with local setup instructions
- **Streaming-style Agent Thinking UI**: JavaScript fetch-based animation with typing effects
  - New JSON API endpoint `/api/cases/{case_id}/run_concept_review`
  - Steps appear one-by-one with fade-in animation (300ms delay)
  - Text types in character-by-character (15ms per character)
  - 800ms pause between steps for dramatic effect
  - CSS animations for blinking cursor during typing
- **Enhanced Concept Note with Trade-offs Table**:
  - Summary comparison table with all 3 financial options
  - Decision Framework section explaining trade-offs narratively
  - Each option shows: Structure, Tenor/Grace, Rate, Score, Benefits, Trade-offs

## Future Enhancements
- Replace deterministic agents with LLM integration
- Add real Bloomberg/SAP API connections
- Implement user authentication
- Add PDF document parsing
- Export functionality (PDF, Excel)
