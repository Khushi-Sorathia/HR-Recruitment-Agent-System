from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class CandidateCreate(BaseModel):
    name: str
    email: EmailStr
    job_role: str
    resume_text: str

class CandidateResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    job_role: str
    ats_score: float
    pipeline_stage: str
    
    class Config:
        orm_mode = True

class ATSníkaResponse(BaseModel):
    score: float
    reasoning: str
    pass_screening: bool

class InterviewQuestion(BaseModel):
    questionText: str
    stage: str

class InterviewAnswer(BaseModel):
    questionId: Optional[int] = None
    answerText: str
    
class GradingResponse(BaseModel):
    score: float
    reasoning: str

class ScreeningInfo(BaseModel):
    notice_period: str
    joining_date: str
    additional_notes: str
