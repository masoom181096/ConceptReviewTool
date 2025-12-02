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
    format_thinking_log_markdown
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
async def intake_page(request: Request):
    """Display the email-first intake page."""
    return templates.TemplateResponse(
        "intake.html",
        {"request": request}
    )


@app.post("/intake", response_class=HTMLResponse)
async def process_intake(
    request: Request,
    email_text: str = Form(...)
):
    """Process email text and show pre-filled case creation form."""
    result = parse_need_assessment(email_text)
    
    return templates.TemplateResponse(
        "case_new_from_intake.html",
        {
            "request": request,
            "email_text": email_text,
            "project_name": result.get("project_name"),
            "country": result.get("country"),
            "sector": "Urban Transport",
            "requested_amount": result.get("requested_amount_usd"),
            "problem_summary": result.get("problem_summary")
        }
    )


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
        case.status = "ARCHIVED"
    else:
        raise HTTPException(status_code=400, detail="Invalid decision")
    
    db.commit()
    
    return RedirectResponse(url=f"/cases/{case_id}", status_code=302)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
