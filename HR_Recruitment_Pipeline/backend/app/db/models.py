from sqlalchemy import Column, Integer, String, Float, Text, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    resume_text = Column(Text)
    job_role = Column(String, index=True)
    ats_score = Column(Float, default=0.0)
    total_score = Column(Float, default=0.0)
    pipeline_stage = Column(String, default="Resume Ingestion") # e.g. Resume Ingestion, Rejected, Technical Interview, HR Screening, Scheduling, Offer
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)

class InterviewQA(Base):
    __tablename__ = "interview_qas"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    question_text = Column(Text)
    answer_text = Column(Text, nullable=True)
    score = Column(Float, default=0.0)
    reasoning = Column(Text, nullable=True)
    stage = Column(String) # 'Technical' vs 'HR_Screening'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
