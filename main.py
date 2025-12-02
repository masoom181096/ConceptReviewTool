from fastapi import FastAPI, Request, Depends, Form, HTTPException, Response, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import markdown

from database import engine, get_db, Base
from models import (
    Case, CaseDocuments, SectorProfile, GapAnalysisItem,
    BaselineKPI, FinancialOption, SustainabilityProfile, ConceptNote
)
from agents import (
    parse_need_assessment,
    build_sector_profile,
    build_gap_analysis,
    build_baseline_kpis,
    build_financial_options,
    build_sustainability_profile,
    generate_concept_note
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
async def root():
    """Redirect to cases list."""
    return RedirectResponse(url="/cases", status_code=302)


@app.get("/cases", response_class=HTMLResponse)
async def list_cases(request: Request, db: Session = Depends(get_db)):
    """Display list of all cases."""
    cases = db.query(Case).order_by(Case.created_at.desc()).all()
    return templates.TemplateResponse(
        "cases_list.html",
        {"request": request, "cases": cases}
    )


@app.get("/cases/new", response_class=HTMLResponse)
async def new_case_form(request: Request):
    """Display form to create new case."""
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
            "concept_note": concept_note
        }
    )


@app.post("/cases/{case_id}/update_docs", response_class=HTMLResponse)
async def update_documents(
    request: Request,
    case_id: int,
    need_assessment_text: str = Form(""),
    sector_profile_text: str = Form(""),
    benchmark_text: str = Form(""),
    ops_fleet_text: str = Form(""),
    financial_data_text: str = Form(""),
    sustainability_text: str = Form(""),
    need_assessment_file: Optional[UploadFile] = File(None),
    sector_profile_file: Optional[UploadFile] = File(None),
    benchmark_file: Optional[UploadFile] = File(None),
    ops_fleet_file: Optional[UploadFile] = File(None),
    financial_data_file: Optional[UploadFile] = File(None),
    sustainability_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Update case documents from form text or uploaded files."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    docs = db.query(CaseDocuments).filter(CaseDocuments.case_id == case_id).first()
    if not docs:
        docs = CaseDocuments(case_id=case_id)
        db.add(docs)
    
    if need_assessment_file and need_assessment_file.filename:
        docs.need_assessment_text = extract_text_from_upload(need_assessment_file)
        docs.need_assessment_filename = need_assessment_file.filename
    else:
        docs.need_assessment_text = need_assessment_text
    
    if sector_profile_file and sector_profile_file.filename:
        docs.sector_profile_text = extract_text_from_upload(sector_profile_file)
        docs.sector_profile_filename = sector_profile_file.filename
    else:
        docs.sector_profile_text = sector_profile_text
    
    if benchmark_file and benchmark_file.filename:
        docs.benchmark_text = extract_text_from_upload(benchmark_file)
        docs.benchmark_filename = benchmark_file.filename
    else:
        docs.benchmark_text = benchmark_text
    
    if ops_fleet_file and ops_fleet_file.filename:
        docs.ops_fleet_text = extract_text_from_upload(ops_fleet_file)
        docs.ops_fleet_filename = ops_fleet_file.filename
    else:
        docs.ops_fleet_text = ops_fleet_text
    
    if financial_data_file and financial_data_file.filename:
        docs.financial_data_text = extract_text_from_upload(financial_data_file)
        docs.financial_data_filename = financial_data_file.filename
    else:
        docs.financial_data_text = financial_data_text
    
    if sustainability_file and sustainability_file.filename:
        docs.sustainability_text = extract_text_from_upload(sustainability_file)
        docs.sustainability_filename = sustainability_file.filename
    else:
        docs.sustainability_text = sustainability_text
    
    db.commit()
    
    return RedirectResponse(url=f"/cases/{case_id}", status_code=302)


@app.post("/cases/{case_id}/run_agents", response_class=HTMLResponse)
async def run_agents(request: Request, case_id: int, db: Session = Depends(get_db)):
    """
    Run all agents to process documents and generate concept note.
    
    Pipeline:
    1. Parse need assessment
    2. Build sector profile
    3. Build gap analysis
    4. Build baseline KPIs
    5. Build financial options
    6. Build sustainability profile
    7. Generate concept note
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    docs = db.query(CaseDocuments).filter(CaseDocuments.case_id == case_id).first()
    if not docs:
        raise HTTPException(status_code=400, detail="No documents found for this case")
    
    db.query(SectorProfile).filter(SectorProfile.case_id == case_id).delete()
    db.query(GapAnalysisItem).filter(GapAnalysisItem.case_id == case_id).delete()
    db.query(BaselineKPI).filter(BaselineKPI.case_id == case_id).delete()
    db.query(FinancialOption).filter(FinancialOption.case_id == case_id).delete()
    db.query(SustainabilityProfile).filter(SustainabilityProfile.case_id == case_id).delete()
    db.query(ConceptNote).filter(ConceptNote.case_id == case_id).delete()
    db.commit()
    
    need_result = parse_need_assessment(docs.need_assessment_text or "")
    
    sector_data = build_sector_profile(docs.sector_profile_text or "")
    sector_profile = SectorProfile(case_id=case_id, **sector_data)
    db.add(sector_profile)
    db.commit()
    db.refresh(sector_profile)
    
    sector_dict = {
        "fleet_total": sector_profile.fleet_total,
        "fleet_diesel": sector_profile.fleet_diesel,
        "fleet_hybrid": sector_profile.fleet_hybrid,
        "fleet_electric": sector_profile.fleet_electric,
        "depots": sector_profile.depots,
        "daily_ridership": sector_profile.daily_ridership,
        "annual_opex_usd": sector_profile.annual_opex_usd,
        "annual_co2_tons": sector_profile.annual_co2_tons,
        "notes": sector_profile.notes
    }
    
    gaps_data = build_gap_analysis(sector_dict, docs.benchmark_text or "")
    for gap in gaps_data:
        gap_item = GapAnalysisItem(case_id=case_id, **gap)
        db.add(gap_item)
    db.commit()
    
    kpis_data = build_baseline_kpis(docs.ops_fleet_text or "", sector_dict)
    for kpi in kpis_data:
        kpi_item = BaselineKPI(case_id=case_id, **kpi)
        db.add(kpi_item)
    db.commit()
    
    options_data = build_financial_options(docs.financial_data_text or "")
    for opt in options_data:
        option = FinancialOption(case_id=case_id, **opt)
        db.add(option)
    db.commit()
    
    baseline_co2 = sector_profile.annual_co2_tons or 0
    sustainability_data = build_sustainability_profile(
        docs.sustainability_text or "",
        baseline_co2
    )
    sustainability = SustainabilityProfile(case_id=case_id, **sustainability_data)
    db.add(sustainability)
    db.commit()
    
    gap_items = db.query(GapAnalysisItem).filter(GapAnalysisItem.case_id == case_id).all()
    kpi_items = db.query(BaselineKPI).filter(BaselineKPI.case_id == case_id).all()
    fin_options = db.query(FinancialOption).filter(
        FinancialOption.case_id == case_id
    ).order_by(FinancialOption.total_score.desc()).all()
    
    case_dict = {"name": case.name, "country": case.country, "sector": case.sector}
    
    gaps_list = [
        {
            "indicator": g.indicator,
            "kenya_value": g.kenya_value,
            "benchmark_city": g.benchmark_city,
            "benchmark_value": g.benchmark_value,
            "gap_delta": g.gap_delta,
            "comparability": g.comparability,
            "comment": g.comment
        }
        for g in gap_items
    ]
    
    kpis_list = [
        {
            "name": k.name,
            "baseline_value": k.baseline_value,
            "unit": k.unit,
            "target_value": k.target_value,
            "category": k.category,
            "notes": k.notes
        }
        for k in kpi_items
    ]
    
    options_list = [
        {
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
            "cons": o.cons
        }
        for o in fin_options
    ]
    
    sustainability_dict = {
        "category": sustainability.category,
        "co2_reduction_tons": sustainability.co2_reduction_tons,
        "pm25_reduction": sustainability.pm25_reduction,
        "accessibility_notes": sustainability.accessibility_notes,
        "policy_alignment_notes": sustainability.policy_alignment_notes,
        "key_risks": sustainability.key_risks,
        "mitigations": sustainability.mitigations
    }
    
    concept_md = generate_concept_note(
        case_dict,
        need_result,
        sector_dict,
        gaps_list,
        kpis_list,
        options_list,
        sustainability_dict
    )
    
    concept_note = ConceptNote(case_id=case_id, content_markdown=concept_md)
    db.add(concept_note)
    db.commit()
    
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
