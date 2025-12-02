from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CaseCreate(BaseModel):
    name: str
    country: str
    sector: str


class CaseUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    sector: Optional[str] = None
    status: Optional[str] = None


class CaseDocumentsUpdate(BaseModel):
    need_assessment_text: Optional[str] = ""
    sector_profile_text: Optional[str] = ""
    benchmark_text: Optional[str] = ""
    ops_fleet_text: Optional[str] = ""
    financial_data_text: Optional[str] = ""
    sustainability_text: Optional[str] = ""


class SectorProfileSchema(BaseModel):
    fleet_total: Optional[int] = None
    fleet_diesel: Optional[int] = None
    fleet_hybrid: Optional[int] = None
    fleet_electric: Optional[int] = None
    depots: Optional[int] = None
    daily_ridership: Optional[int] = None
    annual_opex_usd: Optional[float] = None
    annual_co2_tons: Optional[float] = None
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class GapAnalysisItemSchema(BaseModel):
    indicator: str
    kenya_value: Optional[str] = None
    benchmark_city: Optional[str] = None
    benchmark_value: Optional[str] = None
    gap_delta: Optional[str] = None
    comparability: Optional[str] = None
    comment: Optional[str] = None
    
    class Config:
        from_attributes = True


class BaselineKPISchema(BaseModel):
    name: str
    baseline_value: Optional[str] = None
    unit: Optional[str] = None
    target_value: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class FinancialOptionSchema(BaseModel):
    name: str
    instrument_type: Optional[str] = None
    currency: str = "USD"
    tenor_years: Optional[int] = None
    grace_period_years: Optional[int] = None
    all_in_rate_bps: Optional[float] = None
    principal_amount_usd: Optional[float] = None
    repayment_score: Optional[float] = None
    rate_score: Optional[float] = None
    total_score: Optional[float] = None
    pros: Optional[str] = None
    cons: Optional[str] = None
    
    class Config:
        from_attributes = True


class SustainabilityProfileSchema(BaseModel):
    category: str = "B"
    co2_reduction_tons: Optional[float] = None
    pm25_reduction: Optional[str] = None
    accessibility_notes: Optional[str] = None
    policy_alignment_notes: Optional[str] = None
    key_risks: Optional[str] = None
    mitigations: Optional[str] = None
    
    class Config:
        from_attributes = True


class NeedAssessmentResult(BaseModel):
    project_name: Optional[str] = None
    country: Optional[str] = None
    problem_summary: Optional[str] = None
    requested_amount_usd: Optional[float] = None


class DecisionInput(BaseModel):
    decision: str
