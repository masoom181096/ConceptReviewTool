from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Case(Base):
    """
    Main case entity for EBRD Concept Review.
    
    Phase completion flags track progress through the 4-phase agent workflow:
    - Phase 1: Sector Profile, Benchmarks & KPIs
    - Phase 2: Sustainability Assessment
    - Phase 3: Market Data & Financial Options
    - Phase 4: Concept Note Draft
    """
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)
    sector = Column(String(100), nullable=False)
    status = Column(String(20), default="NEW")
    agent_thinking_log = Column(Text, nullable=True)
    selected_financial_option_id = Column(Integer, ForeignKey("financial_options.id"), nullable=True)
    
    phase1_completed = Column(Boolean, default=False)
    phase2_completed = Column(Boolean, default=False)
    phase3_completed = Column(Boolean, default=False)
    phase4_completed = Column(Boolean, default=False)
    phase1_thinking = Column(Text, nullable=True)
    phase2_thinking = Column(Text, nullable=True)
    phase3_thinking = Column(Text, nullable=True)
    phase4_thinking = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    documents = relationship("CaseDocuments", back_populates="case", uselist=False, cascade="all, delete-orphan")
    sector_profile = relationship("SectorProfile", back_populates="case", uselist=False, cascade="all, delete-orphan")
    gap_analysis_items = relationship("GapAnalysisItem", back_populates="case", cascade="all, delete-orphan")
    baseline_kpis = relationship("BaselineKPI", back_populates="case", cascade="all, delete-orphan")
    financial_options = relationship("FinancialOption", back_populates="case", foreign_keys="FinancialOption.case_id", cascade="all, delete-orphan")
    sustainability_profile = relationship("SustainabilityProfile", back_populates="case", uselist=False, cascade="all, delete-orphan")
    concept_note = relationship("ConceptNote", back_populates="case", uselist=False, cascade="all, delete-orphan")
    selected_financial_option = relationship("FinancialOption", foreign_keys=[selected_financial_option_id], uselist=False)


class CaseDocuments(Base):
    __tablename__ = "case_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    need_assessment_text = Column(Text, default="")
    sector_profile_text = Column(Text, default="")
    benchmark_text = Column(Text, default="")
    ops_fleet_text = Column(Text, default="")
    financial_data_text = Column(Text, default="")
    sustainability_text = Column(Text, default="")
    need_assessment_filename = Column(String(255), nullable=True)
    sector_profile_filename = Column(String(255), nullable=True)
    benchmark_filename = Column(String(255), nullable=True)
    ops_fleet_filename = Column(String(255), nullable=True)
    financial_data_filename = Column(String(255), nullable=True)
    sustainability_filename = Column(String(255), nullable=True)
    
    case = relationship("Case", back_populates="documents")


class SectorProfile(Base):
    __tablename__ = "sector_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    fleet_total = Column(Integer, nullable=True)
    fleet_diesel = Column(Integer, nullable=True)
    fleet_hybrid = Column(Integer, nullable=True)
    fleet_electric = Column(Integer, nullable=True)
    depots = Column(Integer, nullable=True)
    daily_ridership = Column(Integer, nullable=True)
    annual_opex_usd = Column(Float, nullable=True)
    annual_co2_tons = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    
    case = relationship("Case", back_populates="sector_profile")


class GapAnalysisItem(Base):
    __tablename__ = "gap_analysis_items"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    indicator = Column(String(255), nullable=False)
    kenya_value = Column(String(100), nullable=True)
    benchmark_city = Column(String(100), nullable=True)
    benchmark_value = Column(String(100), nullable=True)
    gap_delta = Column(String(100), nullable=True)
    comparability = Column(String(50), nullable=True)
    comment = Column(Text, nullable=True)
    
    case = relationship("Case", back_populates="gap_analysis_items")


class BaselineKPI(Base):
    __tablename__ = "baseline_kpis"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    name = Column(String(255), nullable=False)
    baseline_value = Column(String(100), nullable=True)
    unit = Column(String(50), nullable=True)
    target_value = Column(String(100), nullable=True)
    category = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    
    case = relationship("Case", back_populates="baseline_kpis")


class FinancialOption(Base):
    __tablename__ = "financial_options"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    name = Column(String(255), nullable=False)
    instrument_type = Column(String(100), nullable=True)
    currency = Column(String(10), default="USD")
    tenor_years = Column(Integer, nullable=True)
    grace_period_years = Column(Integer, nullable=True)
    all_in_rate_bps = Column(Float, nullable=True)
    principal_amount_usd = Column(Float, nullable=True)
    repayment_score = Column(Float, nullable=True)
    rate_score = Column(Float, nullable=True)
    total_score = Column(Float, nullable=True)
    pros = Column(Text, nullable=True)
    cons = Column(Text, nullable=True)
    
    case = relationship("Case", back_populates="financial_options", foreign_keys=[case_id])


class SustainabilityProfile(Base):
    __tablename__ = "sustainability_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    category = Column(String(10), default="B")
    co2_reduction_tons = Column(Float, nullable=True)
    pm25_reduction = Column(String(100), nullable=True)
    accessibility_notes = Column(Text, nullable=True)
    policy_alignment_notes = Column(Text, nullable=True)
    key_risks = Column(Text, nullable=True)
    mitigations = Column(Text, nullable=True)
    
    case = relationship("Case", back_populates="sustainability_profile")


class ConceptNote(Base):
    __tablename__ = "concept_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    content_markdown = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    case = relationship("Case", back_populates="concept_note")
