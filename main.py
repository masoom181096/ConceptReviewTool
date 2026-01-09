from fastapi import FastAPI, Request, Depends, Form, HTTPException, Response, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import markdown
import json

from database import engine, get_db, Base
from models import (
    Case, CaseDocuments, SectorProfile, GapAnalysisItem,
    BaselineKPI, FinancialOption, SustainabilityProfile, ConceptNote
)
from agents import parse_need_assessment
from agents.concept_review_orchestrator import (
    run_concept_review_for_case,
    format_thinking_log_markdown,
    run_phase1_sectors_and_kpis,
    run_phase2_sustainability,
    run_phase3_financial_options,
    run_phase4_concept_note,
    format_phase_thinking_json,
    SECTOR_PROFILE_VERIFICATION_SOURCES,
    GAP_ANALYSIS_VERIFICATION_SOURCES,
    KPI_VERIFICATION_SOURCES,
    SUSTAINABILITY_VERIFICATION_SOURCES,
    MARKET_DATA_VERIFICATION_SOURCES,
    CONCEPT_NOTE_VERIFICATION_SOURCES,
)
from utils.document_parsing import extract_text_from_upload

Base.metadata.create_all(bind=engine)

app = FastAPI(title="EBRD Concept Review Tool")


class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["X-Frame-Options"] = "ALLOWALL"
        response.headers["Content-Security-Policy"] = "frame-ancestors *"
        return response


app.add_middleware(NoCacheMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/favicon.ico")
async def favicon():
    return Response(content="", media_type="image/x-icon")


@app.get("/", response_class=HTMLResponse)
async def root_page(request: Request):
    """Redirect to intake page."""
    return RedirectResponse(url="/intake", status_code=302)


@app.get("/intake", response_class=HTMLResponse)
async def intake_page(request: Request):
    """Display the email-first intake page."""
    return templates.TemplateResponse(
        "intake.html",
        {"request": request}
    )


@app.post("/intake", response_class=HTMLResponse)
async def process_intake(
    request: Request,
    email_text: str = Form(...),
    db: Session = Depends(get_db)
):
    """Process email text, create case, and redirect to setup page."""
    result = parse_need_assessment(email_text)
    
    case = Case(
        name=result.get("project_name", "New Project"),
        country=result.get("country", ""),
        sector="Urban Transport",
        status="DRAFT"
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    
    docs = CaseDocuments(
        case_id=case.id,
        need_assessment_text=email_text
    )
    db.add(docs)
    db.commit()
    
    return RedirectResponse(url=f"/cases/{case.id}/setup", status_code=302)


@app.post("/cases/create_from_intake", response_class=HTMLResponse)
async def create_case_from_intake(
    request: Request,
    name: str = Form(...),
    country: str = Form(...),
    sector: str = Form(...),
    email_text: str = Form(""),
    db: Session = Depends(get_db)
):
    """Create a new case from intake with need assessment pre-filled."""
    case = Case(
        name=name,
        country=country,
        sector=sector,
        status="IN_REVIEW"
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    
    docs = CaseDocuments(
        case_id=case.id,
        need_assessment_text=email_text
    )
    db.add(docs)
    db.commit()
    
    return RedirectResponse(url=f"/cases/{case.id}", status_code=302)


@app.get("/cases", response_class=HTMLResponse)
async def list_cases(request: Request, db: Session = Depends(get_db)):
    """Display list of all cases."""
    cases = db.query(Case).order_by(Case.created_at.desc()).all()
    return templates.TemplateResponse(
        "cases_list.html",
        {"request": request, "cases": cases}
    )


@app.post("/cases/{case_id}/delete", response_class=HTMLResponse)
async def delete_case(case_id: int, db: Session = Depends(get_db)):
    """Delete a case and all its related data."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    db.query(CaseDocuments).filter(CaseDocuments.case_id == case_id).delete()
    db.query(SectorProfile).filter(SectorProfile.case_id == case_id).delete()
    db.query(GapAnalysisItem).filter(GapAnalysisItem.case_id == case_id).delete()
    db.query(BaselineKPI).filter(BaselineKPI.case_id == case_id).delete()
    db.query(FinancialOption).filter(FinancialOption.case_id == case_id).delete()
    db.query(SustainabilityProfile).filter(SustainabilityProfile.case_id == case_id).delete()
    db.query(ConceptNote).filter(ConceptNote.case_id == case_id).delete()
    db.delete(case)
    db.commit()
    
    return RedirectResponse(url="/cases", status_code=302)


@app.get("/cases/new", response_class=HTMLResponse)
async def new_case_form(request: Request):
    """Display form to create new case (blank, secondary path)."""
    return templates.TemplateResponse(
        "case_new.html",
        {"request": request}
    )


@app.post("/cases", response_class=HTMLResponse)
async def create_case(
    request: Request,
    name: str = Form(...),
    country: str = Form(...),
    sector: str = Form(...),
    db: Session = Depends(get_db)
):
    """Create a new case and empty documents."""
    case = Case(
        name=name,
        country=country,
        sector=sector,
        status="IN_REVIEW"
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    
    docs = CaseDocuments(case_id=case.id)
    db.add(docs)
    db.commit()
    
    return RedirectResponse(url=f"/cases/{case.id}", status_code=302)


@app.get("/cases/{case_id}", response_class=HTMLResponse)
async def case_detail(request: Request, case_id: int, db: Session = Depends(get_db)):
    """Display case detail dashboard."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    docs = db.query(CaseDocuments).filter(CaseDocuments.case_id == case_id).first()
    sector_profile = db.query(SectorProfile).filter(SectorProfile.case_id == case_id).first()
    gap_items = db.query(GapAnalysisItem).filter(GapAnalysisItem.case_id == case_id).all()
    kpis = db.query(BaselineKPI).filter(BaselineKPI.case_id == case_id).all()
    financial_options = db.query(FinancialOption).filter(
        FinancialOption.case_id == case_id
    ).order_by(FinancialOption.total_score.desc()).all()
    sustainability = db.query(SustainabilityProfile).filter(
        SustainabilityProfile.case_id == case_id
    ).first()
    concept_note = db.query(ConceptNote).filter(ConceptNote.case_id == case_id).first()
    
    thinking_steps = None
    if case.agent_thinking_log:
        try:
            thinking_steps = json.loads(case.agent_thinking_log)
        except json.JSONDecodeError:
            thinking_steps = None
    
    return templates.TemplateResponse(
        "case_detail.html",
        {
            "request": request,
            "case": case,
            "docs": docs or CaseDocuments(),
            "sector_profile": sector_profile,
            "gap_items": gap_items,
            "kpis": kpis,
            "financial_options": financial_options,
            "sustainability": sustainability,
            "concept_note": concept_note,
            "thinking_steps": thinking_steps
        }
    )


@app.post("/cases/{case_id}/update_docs", response_class=HTMLResponse)
async def update_documents(
    request: Request,
    case_id: int,
    sector_profile_text: str = Form(""),
    sustainability_text: str = Form(""),
    sector_profile_file: Optional[UploadFile] = File(None),
    sustainability_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Update case documents - only Sector Profile and Sustainability."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    docs = db.query(CaseDocuments).filter(CaseDocuments.case_id == case_id).first()
    if not docs:
        docs = CaseDocuments(case_id=case_id)
        db.add(docs)
    
    if sector_profile_file and sector_profile_file.filename:
        docs.sector_profile_text = extract_text_from_upload(sector_profile_file)
        docs.sector_profile_filename = sector_profile_file.filename
    else:
        docs.sector_profile_text = sector_profile_text
    
    if sustainability_file and sustainability_file.filename:
        docs.sustainability_text = extract_text_from_upload(sustainability_file)
        docs.sustainability_filename = sustainability_file.filename
    else:
        docs.sustainability_text = sustainability_text
    
    db.commit()
    
    return RedirectResponse(url=f"/cases/{case_id}", status_code=302)


@app.get("/cases/{case_id}/setup", response_class=HTMLResponse)
async def case_setup_page(
    request: Request,
    case_id: int,
    db: Session = Depends(get_db)
):
    """Display the case setup page (Screen 2) for uploading documents."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    docs = db.query(CaseDocuments).filter(CaseDocuments.case_id == case_id).first()
    
    return templates.TemplateResponse(
        "case_setup.html",
        {
            "request": request,
            "case": case,
            "docs": docs or CaseDocuments()
        }
    )


@app.post("/cases/{case_id}/setup", response_class=HTMLResponse)
async def submit_case_setup(
    request: Request,
    case_id: int,
    name: str = Form(...),
    country: str = Form(...),
    sector: str = Form(...),
    sector_profile_file: Optional[UploadFile] = File(None),
    sustainability_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Process case setup form and redirect to review page."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case.name = name
    case.country = country
    case.sector = sector
    case.status = "READY_FOR_ANALYSIS"
    
    docs = db.query(CaseDocuments).filter(CaseDocuments.case_id == case_id).first()
    if not docs:
        docs = CaseDocuments(case_id=case_id)
        db.add(docs)
    
    if sector_profile_file and sector_profile_file.filename:
        docs.sector_profile_text = extract_text_from_upload(sector_profile_file)
        docs.sector_profile_filename = sector_profile_file.filename
    
    if sustainability_file and sustainability_file.filename:
        docs.sustainability_text = extract_text_from_upload(sustainability_file)
        docs.sustainability_filename = sustainability_file.filename
    
    db.commit()
    
    return RedirectResponse(url=f"/cases/{case.id}/review", status_code=302)


def _persist_concept_review_results(case_id: int, result: dict, db: Session):
    """
    Helper function to persist concept review results to the database.
    Used by both the HTML and JSON API endpoints.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    
    db.query(SectorProfile).filter(SectorProfile.case_id == case_id).delete()
    db.query(GapAnalysisItem).filter(GapAnalysisItem.case_id == case_id).delete()
    db.query(BaselineKPI).filter(BaselineKPI.case_id == case_id).delete()
    db.query(FinancialOption).filter(FinancialOption.case_id == case_id).delete()
    db.query(SustainabilityProfile).filter(SustainabilityProfile.case_id == case_id).delete()
    db.query(ConceptNote).filter(ConceptNote.case_id == case_id).delete()
    db.commit()
    
    sector_profile = SectorProfile(case_id=case_id, **result["sector_profile"])
    db.add(sector_profile)
    
    for gap in result["gap_items"]:
        gap_item = GapAnalysisItem(case_id=case_id, **gap)
        db.add(gap_item)
    
    for kpi in result["kpis"]:
        kpi_item = BaselineKPI(case_id=case_id, **kpi)
        db.add(kpi_item)
    
    for opt in result["financial_options"]:
        option = FinancialOption(case_id=case_id, **opt)
        db.add(option)
    
    sustainability = SustainabilityProfile(case_id=case_id, **result["sustainability_profile"])
    db.add(sustainability)
    
    concept_note = ConceptNote(case_id=case_id, content_markdown=result["concept_note_content"])
    db.add(concept_note)
    
    case.agent_thinking_log = json.dumps(result["thinking_steps"])
    
    db.commit()


@app.post("/api/cases/{case_id}/run_concept_review")
async def api_run_concept_review(case_id: int, db: Session = Depends(get_db)):
    """
    JSON API endpoint: Run the Concept Review orchestrator and return:
      - thinking_steps (list of dicts with step, title, description)
      - concept_note_markdown (string)
      - success (boolean)
    
    Also persists all structured entities (SectorProfile, GapAnalysisItem, 
    BaselineKPI, FinancialOption, SustainabilityProfile, ConceptNote) to the DB.
    
    This endpoint is designed for use with JavaScript fetch() to enable
    streaming-style thinking animation in the frontend.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Case not found"}
        )
    
    docs = db.query(CaseDocuments).filter(CaseDocuments.case_id == case_id).first()
    if not docs:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "No documents found for this case"}
        )
    
    try:
        result = run_concept_review_for_case(case, docs)
        _persist_concept_review_results(case_id, result, db)
        
        return JSONResponse(content={
            "success": True,
            "thinking_steps": result["thinking_steps"],
            "concept_note_markdown": result["concept_note_content"]
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/cases/{case_id}/run_concept_review", response_class=HTMLResponse)
async def run_concept_review(request: Request, case_id: int, db: Session = Depends(get_db)):
    """
    Run the full Concept Review Agent pipeline (form-based, redirects to case page).
    
    This orchestrates all agents and produces:
    - Structured data (SectorProfile, GapAnalysis, KPIs, etc.)
    - A thinking log showing the agent's reasoning
    - A Concept Note draft
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    docs = db.query(CaseDocuments).filter(CaseDocuments.case_id == case_id).first()
    if not docs:
        raise HTTPException(status_code=400, detail="No documents found for this case")
    
    result = run_concept_review_for_case(case, docs)
    _persist_concept_review_results(case_id, result, db)
    
    return RedirectResponse(url=f"/cases/{case_id}", status_code=302)


@app.get("/cases/{case_id}/concept_note", response_class=HTMLResponse)
async def view_concept_note(request: Request, case_id: int, db: Session = Depends(get_db)):
    """Display rendered concept note."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    concept_note = db.query(ConceptNote).filter(ConceptNote.case_id == case_id).first()
    if not concept_note:
        raise HTTPException(status_code=404, detail="Concept note not generated yet")
    
    content_html = markdown.markdown(
        concept_note.content_markdown or "",
        extensions=["tables", "fenced_code"]
    )
    
    return templates.TemplateResponse(
        "concept_note.html",
        {
            "request": request,
            "case": case,
            "concept_note": concept_note,
            "content_html": content_html
        }
    )


@app.post("/cases/{case_id}/decision", response_class=HTMLResponse)
async def submit_decision(
    request: Request,
    case_id: int,
    decision: str = Form(...),
    db: Session = Depends(get_db)
):
    """Process OPSCOMM decision on case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if decision == "approve":
        case.status = "APPROVED"
    elif decision == "reject":
        case.status = "REJECTED"
    else:
        raise HTTPException(status_code=400, detail="Invalid decision")
    
    db.commit()
    
    return RedirectResponse(url=f"/cases/{case_id}", status_code=302)


@app.get("/cases/{case_id}/review", response_class=HTMLResponse)
async def unified_review_page(
    request: Request,
    case_id: int,
    error_message: str = None,
    db: Session = Depends(get_db)
):
    """
    Unified review page (Screen 3) that shows all phases and allows approval.
    Auto-runs phases sequentially if status is READY_FOR_ANALYSIS.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    docs = db.query(CaseDocuments).filter(CaseDocuments.case_id == case_id).first()
    sector_profile = db.query(SectorProfile).filter(SectorProfile.case_id == case_id).first()
    gap_items = db.query(GapAnalysisItem).filter(GapAnalysisItem.case_id == case_id).all()
    kpis = db.query(BaselineKPI).filter(BaselineKPI.case_id == case_id).all()
    financial_options = db.query(FinancialOption).filter(
        FinancialOption.case_id == case_id
    ).order_by(FinancialOption.total_score.desc()).all()
    sustainability = db.query(SustainabilityProfile).filter(
        SustainabilityProfile.case_id == case_id
    ).first()
    concept_note = db.query(ConceptNote).filter(ConceptNote.case_id == case_id).first()
    
    concept_note_html = None
    if concept_note and concept_note.content_markdown:
        concept_note_html = markdown.markdown(
            concept_note.content_markdown,
            extensions=["tables", "fenced_code"]
        )
    
    from services.stub_international_benchmarks import get_market_rates
    market_data = get_market_rates()
    
    phase_thinking = {}
    for phase_no in [1, 2, 3, 4]:
        thinking_field = getattr(case, f"phase{phase_no}_thinking", None)
        if thinking_field:
            try:
                phase_thinking[phase_no] = json.loads(thinking_field)
            except json.JSONDecodeError:
                phase_thinking[phase_no] = None
    
    return templates.TemplateResponse(
        "case_review.html",
        {
            "request": request,
            "case": case,
            "docs": docs or CaseDocuments(),
            "sector_profile": sector_profile,
            "gap_items": gap_items,
            "kpis": kpis,
            "financial_options": financial_options,
            "sustainability": sustainability,
            "concept_note": concept_note,
            "concept_note_html": concept_note_html,
            "market_data": market_data,
            "phase_thinking": phase_thinking,
            "error_message": error_message,
            "sector_profile_sources": SECTOR_PROFILE_VERIFICATION_SOURCES,
            "gap_analysis_sources": GAP_ANALYSIS_VERIFICATION_SOURCES,
            "kpi_sources": KPI_VERIFICATION_SOURCES,
            "sustainability_sources": SUSTAINABILITY_VERIFICATION_SOURCES,
            "market_data_sources": MARKET_DATA_VERIFICATION_SOURCES,
            "concept_note_sources": CONCEPT_NOTE_VERIFICATION_SOURCES,
        }
    )


@app.post("/cases/{case_id}/review/decision", response_class=HTMLResponse)
async def review_decision(
    request: Request,
    case_id: int,
    decision: str = Form(...),
    selected_option_id: int = Form(None),
    db: Session = Depends(get_db)
):
    """
    Handle approval/rejection from the unified review page.
    Approval requires a selected financial option.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if decision == "approve":
        if selected_option_id is None:
            return RedirectResponse(
                url=f"/cases/{case_id}/review?error_message=Please+select+a+financial+instrument+before+approving.",
                status_code=302
            )
        
        selected_option = db.query(FinancialOption).filter(
            FinancialOption.id == selected_option_id,
            FinancialOption.case_id == case_id
        ).first()
        
        if not selected_option:
            raise HTTPException(status_code=400, detail="Invalid financial option selected")
        
        case.selected_financial_option_id = selected_option_id
        case.status = "APPROVED"
    
    elif decision == "reject":
        case.status = "REJECTED"
    
    else:
        raise HTTPException(status_code=400, detail="Invalid decision")
    
    db.commit()
    
    return RedirectResponse(url="/cases", status_code=302)


# =============================================================================
# MULTI-PHASE CONCEPT REVIEW ROUTES
# =============================================================================

PHASE_INFO = {
    1: {"title": "Sector Profile, Benchmarks & KPIs", "short": "Sector & KPIs"},
    2: {"title": "Sustainability Assessment", "short": "Sustainability"},
    3: {"title": "Market Data & Financial Options", "short": "Financial Options"},
    4: {"title": "Concept Note Draft", "short": "Concept Note"},
}


@app.get("/cases/{case_id}/phases/{phase_no}", response_class=HTMLResponse)
async def view_phase(
    request: Request,
    case_id: int,
    phase_no: int,
    db: Session = Depends(get_db)
):
    """
    Render the phase screen (1..4) for the given case.
    Shows progress bar, relevant outputs (if already run), Run Phase button,
    and Proceed to next/back navigation buttons.
    """
    if phase_no < 1 or phase_no > 4:
        raise HTTPException(status_code=404, detail="Invalid phase number")
    
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    docs = db.query(CaseDocuments).filter(CaseDocuments.case_id == case_id).first()
    
    sector_profile = db.query(SectorProfile).filter(SectorProfile.case_id == case_id).first()
    gap_items = db.query(GapAnalysisItem).filter(GapAnalysisItem.case_id == case_id).all()
    kpis = db.query(BaselineKPI).filter(BaselineKPI.case_id == case_id).all()
    sustainability = db.query(SustainabilityProfile).filter(
        SustainabilityProfile.case_id == case_id
    ).first()
    financial_options = db.query(FinancialOption).filter(
        FinancialOption.case_id == case_id
    ).order_by(FinancialOption.total_score.desc()).all()
    concept_note = db.query(ConceptNote).filter(ConceptNote.case_id == case_id).first()
    
    thinking_steps = None
    phase_thinking_field = getattr(case, f"phase{phase_no}_thinking", None)
    if phase_thinking_field:
        try:
            thinking_steps = json.loads(phase_thinking_field)
        except json.JSONDecodeError:
            thinking_steps = None
    
    concept_note_html = None
    if concept_note and concept_note.content_markdown:
        concept_note_html = markdown.markdown(
            concept_note.content_markdown,
            extensions=["tables", "fenced_code"]
        )
    
    market_data = None
    if phase_no == 3:
        from services.stub_international_benchmarks import get_market_rates
        market_data = get_market_rates()
    
    # Determine completion status for this phase
    phase_completed_flags = {
        1: case.phase1_completed,
        2: case.phase2_completed,
        3: case.phase3_completed,
        4: case.phase4_completed,
    }
    current_phase_completed = bool(phase_completed_flags.get(phase_no, False))
    
    # Auto-run logic: if phase not completed -> auto_run_phase = True
    auto_run_phase = not current_phase_completed
    
    return templates.TemplateResponse(
        "phase.html",
        {
            "request": request,
            "case": case,
            "docs": docs or CaseDocuments(),
            "phase_no": phase_no,
            "phase_info": PHASE_INFO,
            "sector_profile": sector_profile,
            "gap_items": gap_items,
            "kpis": kpis,
            "sustainability": sustainability,
            "financial_options": financial_options,
            "concept_note": concept_note,
            "concept_note_html": concept_note_html,
            "thinking_steps": thinking_steps,
            "market_data": market_data,
            "phase_completed": current_phase_completed,
            "auto_run_phase": auto_run_phase,
            "sector_profile_sources": SECTOR_PROFILE_VERIFICATION_SOURCES,
            "gap_analysis_sources": GAP_ANALYSIS_VERIFICATION_SOURCES,
            "kpi_sources": KPI_VERIFICATION_SOURCES,
            "sustainability_sources": SUSTAINABILITY_VERIFICATION_SOURCES,
            "market_data_sources": MARKET_DATA_VERIFICATION_SOURCES,
            "concept_note_sources": CONCEPT_NOTE_VERIFICATION_SOURCES,
        }
    )


def _persist_phase1_results(case_id: int, result: dict, db: Session):
    """Persist Phase 1 results to database."""
    db.query(SectorProfile).filter(SectorProfile.case_id == case_id).delete()
    db.query(GapAnalysisItem).filter(GapAnalysisItem.case_id == case_id).delete()
    db.query(BaselineKPI).filter(BaselineKPI.case_id == case_id).delete()
    
    sector_profile = SectorProfile(case_id=case_id, **result["sector_profile"])
    db.add(sector_profile)
    
    for gap in result["gap_items"]:
        gap_item = GapAnalysisItem(case_id=case_id, **gap)
        db.add(gap_item)
    
    for kpi in result["kpis"]:
        kpi_item = BaselineKPI(case_id=case_id, **kpi)
        db.add(kpi_item)
    
    case = db.query(Case).filter(Case.id == case_id).first()
    case.phase1_thinking = format_phase_thinking_json(result["thinking_steps"])
    case.phase1_completed = True
    
    db.commit()


def _persist_phase2_results(case_id: int, result: dict, db: Session):
    """Persist Phase 2 results to database."""
    db.query(SustainabilityProfile).filter(SustainabilityProfile.case_id == case_id).delete()
    
    sustainability = SustainabilityProfile(case_id=case_id, **result["sustainability_profile"])
    db.add(sustainability)
    
    case = db.query(Case).filter(Case.id == case_id).first()
    case.phase2_thinking = format_phase_thinking_json(result["thinking_steps"])
    case.phase2_completed = True
    
    db.commit()


def _persist_phase3_results(case_id: int, result: dict, db: Session):
    """Persist Phase 3 results to database."""
    db.query(FinancialOption).filter(FinancialOption.case_id == case_id).delete()
    
    for opt in result["financial_options"]:
        option = FinancialOption(case_id=case_id, **opt)
        db.add(option)
    
    case = db.query(Case).filter(Case.id == case_id).first()
    case.phase3_thinking = format_phase_thinking_json(result["thinking_steps"])
    case.phase3_completed = True
    
    db.commit()


def _persist_phase4_results(case_id: int, result: dict, db: Session):
    """Persist Phase 4 results to database."""
    db.query(ConceptNote).filter(ConceptNote.case_id == case_id).delete()
    
    concept_note = ConceptNote(case_id=case_id, content_markdown=result["concept_note_content"])
    db.add(concept_note)
    
    case = db.query(Case).filter(Case.id == case_id).first()
    case.phase4_thinking = format_phase_thinking_json(result["thinking_steps"])
    case.phase4_completed = True
    
    db.commit()


@app.post("/cases/{case_id}/phases/{phase_no}/run")
async def run_phase(
    case_id: int,
    phase_no: int,
    db: Session = Depends(get_db)
):
    """
    Execute only the requested phase, persist results, and redirect back 
    to the same phase screen.
    """
    if phase_no < 1 or phase_no > 4:
        raise HTTPException(status_code=400, detail="Invalid phase number")
    
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    docs = db.query(CaseDocuments).filter(CaseDocuments.case_id == case_id).first()
    if not docs:
        raise HTTPException(status_code=400, detail="No documents found for this case")
    
    try:
        if phase_no == 1:
            result = run_phase1_sectors_and_kpis(case, docs)
            _persist_phase1_results(case_id, result, db)
        
        elif phase_no == 2:
            if not case.phase1_completed:
                raise HTTPException(status_code=400, detail="Phase 1 must be completed first")
            result = run_phase2_sustainability(case, docs)
            _persist_phase2_results(case_id, result, db)
        
        elif phase_no == 3:
            if not case.phase2_completed:
                raise HTTPException(status_code=400, detail="Phase 2 must be completed first")
            result = run_phase3_financial_options(case, docs)
            _persist_phase3_results(case_id, result, db)
        
        elif phase_no == 4:
            if not case.phase3_completed:
                raise HTTPException(status_code=400, detail="Phase 3 must be completed first")
            
            sector_profile = db.query(SectorProfile).filter(SectorProfile.case_id == case_id).first()
            gap_items = db.query(GapAnalysisItem).filter(GapAnalysisItem.case_id == case_id).all()
            kpis = db.query(BaselineKPI).filter(BaselineKPI.case_id == case_id).all()
            financial_options = db.query(FinancialOption).filter(
                FinancialOption.case_id == case_id
            ).all()
            sustainability = db.query(SustainabilityProfile).filter(
                SustainabilityProfile.case_id == case_id
            ).first()
            
            sector_data = {
                "fleet_total": sector_profile.fleet_total if sector_profile else None,
                "fleet_diesel": sector_profile.fleet_diesel if sector_profile else None,
                "fleet_hybrid": sector_profile.fleet_hybrid if sector_profile else None,
                "fleet_electric": sector_profile.fleet_electric if sector_profile else None,
                "depots": sector_profile.depots if sector_profile else None,
                "daily_ridership": sector_profile.daily_ridership if sector_profile else None,
                "annual_opex_usd": sector_profile.annual_opex_usd if sector_profile else None,
                "annual_co2_tons": sector_profile.annual_co2_tons if sector_profile else None,
            }
            
            gap_items_list = [{
                "indicator": g.indicator,
                "kenya_value": g.kenya_value,
                "benchmark_city": g.benchmark_city,
                "benchmark_value": g.benchmark_value,
                "gap_delta": g.gap_delta,
                "comparability": g.comparability,
                "comment": g.comment,
            } for g in gap_items]
            
            kpis_list = [{
                "name": k.name,
                "baseline_value": k.baseline_value,
                "unit": k.unit,
                "target_value": k.target_value,
                "category": k.category,
                "notes": k.notes,
            } for k in kpis]
            
            options_list = [{
                "name": o.name,
                "instrument_type": o.instrument_type,
                "currency": o.currency,
                "tenor_years": o.tenor_years,
                "grace_period_years": o.grace_period_years,
                "all_in_rate_bps": o.all_in_rate_bps,
                "principal_amount_usd": o.principal_amount_usd,
                "repayment_score": o.repayment_score,
                "rate_score": o.rate_score,
                "total_score": o.total_score,
                "pros": o.pros,
                "cons": o.cons,
            } for o in financial_options]
            
            sustainability_data = {
                "category": sustainability.category if sustainability else None,
                "co2_reduction_tons": sustainability.co2_reduction_tons if sustainability else None,
                "pm25_reduction": sustainability.pm25_reduction if sustainability else None,
                "accessibility_notes": sustainability.accessibility_notes if sustainability else None,
                "policy_alignment_notes": sustainability.policy_alignment_notes if sustainability else None,
                "key_risks": sustainability.key_risks if sustainability else None,
                "mitigations": sustainability.mitigations if sustainability else None,
            }
            
            result = run_phase4_concept_note(
                case, docs,
                sector_data, gap_items_list, kpis_list,
                options_list, sustainability_data
            )
            _persist_phase4_results(case_id, result, db)
        
        return RedirectResponse(url=f"/cases/{case_id}/phases/{phase_no}", status_code=302)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cases/{case_id}/reset_phases")
async def reset_phases(case_id: int, db: Session = Depends(get_db)):
    """Reset all phases for a case to allow re-running."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case.phase1_completed = False
    case.phase2_completed = False
    case.phase3_completed = False
    case.phase4_completed = False
    case.phase1_thinking = None
    case.phase2_thinking = None
    case.phase3_thinking = None
    case.phase4_thinking = None
    
    db.query(SectorProfile).filter(SectorProfile.case_id == case_id).delete()
    db.query(GapAnalysisItem).filter(GapAnalysisItem.case_id == case_id).delete()
    db.query(BaselineKPI).filter(BaselineKPI.case_id == case_id).delete()
    db.query(FinancialOption).filter(FinancialOption.case_id == case_id).delete()
    db.query(SustainabilityProfile).filter(SustainabilityProfile.case_id == case_id).delete()
    db.query(ConceptNote).filter(ConceptNote.case_id == case_id).delete()
    
    db.commit()
    
    return RedirectResponse(url=f"/cases/{case_id}?reset=1", status_code=303)


@app.post("/api/cases/{case_id}/phases/{phase_no}/run")
async def api_run_phase(
    case_id: int,
    phase_no: int,
    db: Session = Depends(get_db)
):
    """
    JSON API endpoint to execute a phase and return thinking steps.
    Returns JSON with thinking_steps for frontend streaming animation.
    """
    if phase_no < 1 or phase_no > 4:
        return JSONResponse({"status": "error", "detail": "Invalid phase number"}, status_code=400)
    
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return JSONResponse({"status": "error", "detail": "Case not found"}, status_code=404)
    
    docs = db.query(CaseDocuments).filter(CaseDocuments.case_id == case_id).first()
    if not docs:
        return JSONResponse({"status": "error", "detail": "No documents found for this case"}, status_code=400)
    
    try:
        if phase_no == 1:
            result = run_phase1_sectors_and_kpis(case, docs)
            _persist_phase1_results(case_id, result, db)
        
        elif phase_no == 2:
            if not case.phase1_completed:
                return JSONResponse({"status": "error", "detail": "Phase 1 must be completed first"}, status_code=400)
            result = run_phase2_sustainability(case, docs)
            _persist_phase2_results(case_id, result, db)
        
        elif phase_no == 3:
            if not case.phase2_completed:
                return JSONResponse({"status": "error", "detail": "Phase 2 must be completed first"}, status_code=400)
            result = run_phase3_financial_options(case, docs)
            _persist_phase3_results(case_id, result, db)
        
        elif phase_no == 4:
            if not case.phase3_completed:
                return JSONResponse({"status": "error", "detail": "Phase 3 must be completed first"}, status_code=400)
            
            sector_profile = db.query(SectorProfile).filter(SectorProfile.case_id == case_id).first()
            gap_items = db.query(GapAnalysisItem).filter(GapAnalysisItem.case_id == case_id).all()
            kpis = db.query(BaselineKPI).filter(BaselineKPI.case_id == case_id).all()
            financial_options = db.query(FinancialOption).filter(
                FinancialOption.case_id == case_id
            ).all()
            sustainability = db.query(SustainabilityProfile).filter(
                SustainabilityProfile.case_id == case_id
            ).first()
            
            sector_data = {
                "fleet_total": sector_profile.fleet_total if sector_profile else None,
                "fleet_diesel": sector_profile.fleet_diesel if sector_profile else None,
                "fleet_hybrid": sector_profile.fleet_hybrid if sector_profile else None,
                "fleet_electric": sector_profile.fleet_electric if sector_profile else None,
                "depots": sector_profile.depots if sector_profile else None,
                "daily_ridership": sector_profile.daily_ridership if sector_profile else None,
                "annual_opex_usd": sector_profile.annual_opex_usd if sector_profile else None,
                "annual_co2_tons": sector_profile.annual_co2_tons if sector_profile else None,
            }
            
            gap_items_list = [{
                "indicator": g.indicator,
                "kenya_value": g.kenya_value,
                "benchmark_city": g.benchmark_city,
                "benchmark_value": g.benchmark_value,
                "gap_delta": g.gap_delta,
                "comparability": g.comparability,
                "comment": g.comment,
            } for g in gap_items]
            
            kpis_list = [{
                "name": k.name,
                "baseline_value": k.baseline_value,
                "unit": k.unit,
                "target_value": k.target_value,
                "category": k.category,
                "notes": k.notes,
            } for k in kpis]
            
            options_list = [{
                "name": o.name,
                "instrument_type": o.instrument_type,
                "currency": o.currency,
                "tenor_years": o.tenor_years,
                "grace_period_years": o.grace_period_years,
                "all_in_rate_bps": o.all_in_rate_bps,
                "principal_amount_usd": o.principal_amount_usd,
                "repayment_score": o.repayment_score,
                "rate_score": o.rate_score,
                "total_score": o.total_score,
                "pros": o.pros,
                "cons": o.cons,
            } for o in financial_options]
            
            sustainability_data = {
                "category": sustainability.category if sustainability else None,
                "co2_reduction_tons": sustainability.co2_reduction_tons if sustainability else None,
                "pm25_reduction": sustainability.pm25_reduction if sustainability else None,
                "accessibility_notes": sustainability.accessibility_notes if sustainability else None,
                "policy_alignment_notes": sustainability.policy_alignment_notes if sustainability else None,
                "key_risks": sustainability.key_risks if sustainability else None,
                "mitigations": sustainability.mitigations if sustainability else None,
            }
            
            result = run_phase4_concept_note(
                case, docs,
                sector_data, gap_items_list, kpis_list,
                options_list, sustainability_data
            )
            _persist_phase4_results(case_id, result, db)
        
        return JSONResponse({
            "status": "ok",
            "thinking_steps": result.get("thinking_steps", []),
            "phase_no": phase_no
        })
    
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
