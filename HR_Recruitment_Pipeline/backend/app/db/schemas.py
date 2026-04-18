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
    email: str
    job_role: str
    ats_score: float
    total_score: float
    pipeline_stage: str
    created_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ATSResponse(BaseModel):
    score: float
    reasoning: str
    pass_screening: bool


class ResumeUploadResponse(BaseModel):
    candidate: CandidateResponse
    ats_result: ATSResponse


class InterviewQuestion(BaseModel):
    questionText: str
    stage: str


class InterviewAnswer(BaseModel):
    questionId: Optional[int] = None
    answerText: str


class GradingResponse(BaseModel):
    score: float
    reasoning: str


class ScreeningQuestionsResponse(BaseModel):
    candidate_id: int
    questions: List[str]


class ScreeningSubmitRequest(BaseModel):
    questions: List[str]
    answers: List[str]


class ScreeningSubmitResponse(BaseModel):
    candidate_id: int
    evaluation: str
    pipeline_stage: str


class ScheduleRequest(BaseModel):
    availability: str


class ScheduleResponse(BaseModel):
    candidate_id: int
    meeting_link: str
    email_status: str
    pipeline_stage: str
