# EBRD Concept Review Tool

## Overview
A web application prototyping EBRD's Concept Review Phase automation for large-institution loan requests. This tool implements a happy-path workflow with a simple internal "agentic" architecture where each "agent" is a Python module/function.

## Current State
- **Status**: Fully functional prototype with multi-phase concept review workflow
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
  case_detail.html           # Case overview with phased workflow entry
  phase.html                 # Multi-phase review screen (all 4 phases)
  _progress_bar.html         # Progress bar macro for phase tracking
  concept_note.html
  review_concept_note.html   # Review & approve concept note

static/
  styles.css            # CSS styling
```

## Data Model
1. **Case** - Main project entity with phase tracking:
   - name, country, sector, status
   - phase1_completed through phase4_completed (Boolean flags)
   - phase1_thinking through phase4_thinking (JSON agent reasoning)
   - selected_financial_option_id
2. **CaseDocuments** - Raw text inputs for each document type
3. **SectorProfile** - Parsed fleet and operational metrics
4. **GapAnalysisItem** - Comparison against international benchmarks
5. **BaselineKPI** - Key performance indicators with targets
6. **FinancialOption** - Financing structures with 60/40 scoring
7. **SustainabilityProfile** - ESG category and environmental metrics
8. **ConceptNote** - Generated Markdown document

## Workflow (4-Phase Sequential)
1. **Email-First Intake**: Paste client email/MoM on the home page
2. **Pre-filled Case Creation**: System extracts project name, country from email
3. **Upload Documents**: Only Sector Profile + Sustainability docs required
4. **Multi-Phase Concept Review**:
   - **Phase 1 - Sector & KPIs**: Parse sector profile, compare benchmarks, generate KPIs
   - **Phase 2 - Sustainability**: Assess E&S category, emissions reduction, risk analysis
   - **Phase 3 - Financial Options**: Generate 3 financing structures with 60/40 scoring
   - **Phase 4 - Concept Note**: Assemble comprehensive draft document
5. **Review & Approve**: Select financial option and approve/reject case

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
- **Multi-Phase Workflow**: 4 sequential phases with progress tracking
- **Two-Column Layout**: Sidebar with vertical progress bar + case summary card
- **Tabbed Interface**: Agent Thinking vs Outputs tabs for cleaner UX
- **Wizard Navigation Footer**: Always-visible navigation at bottom of phase pages
- **Interactive Financial Table**: Clickable rows with detail drawer showing pros/cons
- **Toast Notifications**: Visual feedback on phase completion
- **Clickable Progress Bar**: Navigate to completed phases directly
- **Per-Phase Agent Thinking**: Each phase shows detailed reasoning steps with typewriter animation
- **Document Upload**: Upload .docx or .txt files (Sector Profile + Sustainability)
- **Gap Analysis**: Automatic comparison against IEA benchmark cities
- **Three Financial Options**: Sovereign Loan, Guaranteed City Loan, Blended Co-Financing
- **Financial Trade-offs Table**: Side-by-side comparison of all options with pros/cons
- **Markdown Concept Note**: Auto-generated with all structured data
- **OPSCOMM Decision Workflow**: Approve/Reject cases
- **Phase Reset**: Reset all phases to re-run the analysis
- **Responsive Design**: Mobile-friendly with stacked layout at 900px
- **Local-Runnable**: No external APIs or Replit-specific code

## Recent Changes (Dec 2024)
- **Multi-Phase Workflow Implementation**:
  - Refactored single-shot orchestrator into 4 separate phase functions
  - Added phase completion flags and thinking logs to Case model
  - Created new phase routes (GET/POST for phases 1-4) with sequential validation
  - Built progress bar component and comprehensive phase template
  - Updated case detail page to link to phased flow
  - Phase 1: Sector Profile, Benchmarks & KPIs
  - Phase 2: Sustainability Assessment
  - Phase 3: Market Data & Financial Options
  - Phase 4: Concept Note Draft
  - Reset functionality to re-run all phases
  - Note: Schema changes require database recreation (rm concept_review.db)
- Added email-first intake flow with need assessment parsing
- Simplified document uploads to only Sector Profile + Sustainability
- Created Concept Review Orchestrator for full agent pipeline
- Added Agent Thinking Log with predetermined templated steps
- Added international benchmarks stub service with IEA data
- Added README.md with local setup instructions
- **Streaming-style Agent Thinking UI**: JavaScript fetch-based animation with typewriter effect
  - JSON API endpoint `/api/cases/{case_id}/phases/{phase_no}/run` for async phase execution
  - Returns `{status, phase_completed, thinking_steps}` JSON payload
  - JS-driven DOM manipulation creates thinking step elements dynamically
  - Word-by-word typewriter animation (50ms per word) for LLM-like streaming feel
  - Blinking cursor during typing that disappears when step completes
  - Steps appear sequentially with 800ms delays and CSS fade-in transitions
  - `white-space: pre-line` for proper newline handling without HTML injection
  - Status messages show running/complete/error states
  - Page auto-refreshes after streaming completes to show phase results
- **Enhanced Concept Note with Trade-offs Table**:
  - Summary comparison table with all 3 financial options
  - Decision Framework section explaining trade-offs narratively
  - Each option shows: Structure, Tenor/Grace, Rate, Score, Benefits, Trade-offs
- **Delete Case functionality**:
  - Delete button on All Cases page with confirmation modal
  - Removes all related data (documents, profiles, analysis items, etc.)
- **Review & Approve Workflow**:
  - New "Proceed to Review" button after agent thinking completes
  - Review page displays full concept note with radio button selection for financial instrument
  - Users must select one of three financial options (A, B, or C) before approval
  - Approve button disabled until selection made (client-side validation)
  - Server-side validation prevents approval without selection
  - Case status transitions: In Review → Approved or Rejected
  - Financial instrument names stored clean (e.g., "Sovereign Loan"); Option A/B/C labels added in presentation layer only
- **Richer Agent Thinking Steps**:
  - Multi-line descriptions with bullet points converted to `<br>` tags
  - Data-aware content referencing actual parsed values (fleet counts, CO2 emissions, ridership, rates, scores)
  - 800ms pause between steps for readability
- **MOCK_DEFAULTS for Demo Realism**:
  - Fallback values when parsing fails (DEMO-ONLY feature)
  - _fallback() helper only replaces None values, preserves legitimate zeros
  - Clearly documented as non-production code
- **Sector Profile Parsing Fixes**:
  - Regex pattern fix: `[ \t]+` instead of `\s+` to avoid matching across newlines
  - Zero-value handling: `if val is not None:` instead of `if val:` to preserve 0 values
- **display_val Jinja Macro**:
  - Graceful handling of 0/N/A values in templates
  - allow_zero parameter for fields like fleet_electric where 0 is meaningful
  - Formats numbers with thousands separators

## Future Enhancements
- Replace deterministic agents with LLM integration
- Add real Bloomberg/SAP API connections
- Implement user authentication
- Add PDF document parsing
- Export functionality (PDF, Excel)
