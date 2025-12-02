# EBRD Concept Review Tool

A web application prototyping EBRD's Concept Review Phase automation for large-institution loan requests (e.g., Kenya e-bus project). This tool implements a happy-path workflow with a simple internal "agentic" architecture where each "agent" is a Python module/function.

## Features

- **Email-First Intake**: Start a new review by pasting client email/Minutes of Meeting
- **Document Upload**: Upload .docx or .txt files for Sector Profile and Sustainability documents
- **Automated Agent Pipeline**: 7 specialized agents for data processing
- **International Benchmarks**: Automatic comparison against IEA benchmark cities (Shenzhen, London, Santiago, Bogota)
- **Financial Scoring**: 60/40 rule (60% repayment capacity, 40% rate competitiveness)
- **Agent Thinking Log**: Transparent display of agent reasoning steps
- **Concept Note Generation**: Automated Markdown-based concept note

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ebrd-concept-review-tool
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
uvicorn main:app --reload
```

5. Open your browser and navigate to:
```
http://127.0.0.1:8000
```

## Usage Workflow

1. **Start a Review**: Go to the home page and paste the client email or meeting notes
2. **Create Case**: Review extracted project details and confirm case creation
3. **Upload Documents**: 
   - Sector Profile Document (government/master plan data)
   - Sustainability Document (ESG/environmental data)
4. **Run Concept Review Agent**: Click the button to process all documents
5. **Review Results**: 
   - View the Agent Thinking log to see reasoning steps
   - Review Sector Profile, Gap Analysis, KPIs, Financial Options
   - View the generated Concept Note
6. **OPSCOMM Decision**: Approve or reject the case

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
  concept_review_orchestrator.py # Orchestrate full agent pipeline

services/               # Stub services for external integrations
  stub_market_data.py           # Mock Bloomberg + peer deals data
  stub_sap_finance.py           # Mock repayment/fiscal metrics
  stub_international_benchmarks.py # IEA benchmark data

utils/                  # Utility modules
  document_parsing.py   # Extract text from .docx and .txt uploads

templates/              # Jinja2 HTML templates
  base.html
  intake.html
  case_new.html
  case_new_from_intake.html
  cases_list.html
  case_detail.html
  concept_note.html

static/
  styles.css            # CSS styling
```

## Technical Details

### Data Model

1. **Case** - Main project entity (name, country, sector, status, agent_thinking_log)
2. **CaseDocuments** - Raw text inputs for each document type
3. **SectorProfile** - Parsed fleet and operational metrics
4. **GapAnalysisItem** - Comparison against international benchmarks
5. **BaselineKPI** - Key performance indicators with targets
6. **FinancialOption** - Financing structures with 60/40 scoring
7. **SustainabilityProfile** - ESG category and environmental metrics
8. **ConceptNote** - Generated Markdown document

### Financial Scoring (60/40 Rule)

- **60%**: Repayment capacity (DSCR, FX risk, debt ratios)
- **40%**: Rate competitiveness vs peer median

### International Benchmarks

Comparison cities from IEA data:
- Shenzhen (100% electric fleet)
- London (35% electric fleet)
- Santiago (20% electric fleet)
- Bogota (14% electric fleet)

### Market Data (Stubbed)

- EUR_SWAP_10Y = 2.0%
- GREEN_BOND_SPREAD_10Y = 0.6%
- All-in 10-year green rate = 2.6%

## Important Notes

- All "external data" (benchmarks, Bloomberg, SAP) are mock/stub modules
- No external APIs are called - everything runs locally
- The database uses SQLite stored in `./ebrd_concept_review.db`
- File uploads are processed in memory (no persistent file storage)
- No environment variables required to run in basic mode

## Future Enhancements

- Replace deterministic agents with LLM integration
- Add real Bloomberg/SAP API connections
- Implement user authentication
- Add PDF document parsing
- Export functionality (PDF, Excel)
- Real-time collaboration features

## License

Prototype - Internal Use Only
