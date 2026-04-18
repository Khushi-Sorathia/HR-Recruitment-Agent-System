from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models, schemas
from app.agents.ats_agent import run_ats_pipeline
from app.agents.screening_agent import run_screening_generator, run_screening_evaluation
from app.agents.scheduling_email_agent import run_scheduling_pipeline
from typing import Optional
import PyPDF2
import io

router = APIRouter()


# ── Resume Ingestion ────────────────────────────────────────────────────

@router.post("/upload-resume", response_model=schemas.ResumeUploadResponse)
async def upload_resume(
    name: str = Form(...),
    email: str = Form(...),
    job_role: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a resume PDF, parse it, score with ATS agent, and persist the candidate."""

    # Check for duplicate email
    existing = db.query(models.Candidate).filter(models.Candidate.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="A candidate with this email already exists.")

    # Read and parse the PDF
    file_bytes = await file.read()
    resume_content = ""

    if file.filename and file.filename.lower().endswith(".pdf"):
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    resume_content += page_text + "\n"
        except Exception:
            # Fallback: try raw decode
            resume_content = file_bytes.decode("utf-8", errors="ignore")
    else:
        # Non-PDF: try text decode
        resume_content = file_bytes.decode("utf-8", errors="ignore")

    if not resume_content.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from the uploaded file.")

    # Run ATS Agent (real LLM scoring)
    try:
        ats_result = run_ats_pipeline(resume_content, job_role)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Agent Error: {str(e)}")

    ats_score = ats_result["score"]
    pass_screening = ats_result["pass_screening"]
    reasoning = ats_result["reasoning"]

    pipeline_stage = "Technical Interview" if pass_screening else "Rejected"

    # Persist candidate
    new_candidate = models.Candidate(
        name=name,
        email=email,
        job_role=job_role,
        resume_text=resume_content,
        ats_score=ats_score,
        pipeline_stage=pipeline_stage,
        notes=reasoning,
    )
    db.add(new_candidate)
    db.commit()
    db.refresh(new_candidate)

    return schemas.ResumeUploadResponse(
        candidate=schemas.CandidateResponse.model_validate(new_candidate),
        ats_result=schemas.ATSResponse(
            score=ats_score,
            reasoning=reasoning,
            pass_screening=pass_screening,
        ),
    )


# ── Dashboard ───────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=list[schemas.CandidateResponse])
def get_dashboard(
    role: Optional[str] = Query(None, description="Filter by job role"),
    stage: Optional[str] = Query(None, description="Filter by pipeline stage"),
    db: Session = Depends(get_db),
):
    """Retrieve all candidates with optional role and stage filtering."""
    query = db.query(models.Candidate)

    if role:
        query = query.filter(models.Candidate.job_role.ilike(f"%{role}%"))
    if stage:
        query = query.filter(models.Candidate.pipeline_stage == stage)

    candidates = query.order_by(models.Candidate.created_at.desc()).all()
    return candidates


# ── Single Candidate ────────────────────────────────────────────────────

@router.get("/candidates/{candidate_id}", response_model=schemas.CandidateResponse)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Retrieve a single candidate by ID."""
    candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return candidate


# ── HR Screening ────────────────────────────────────────────────────────

@router.get("/screening/{candidate_id}/questions", response_model=schemas.ScreeningQuestionsResponse)
def get_screening_questions(candidate_id: int, db: Session = Depends(get_db)):
    """Generate HR screening questions based on what's missing from the candidate's resume."""
    candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    questions = run_screening_generator(
        resume_text=candidate.resume_text or "",
        candidate_name=candidate.name,
        job_role=candidate.job_role,
    )

    return schemas.ScreeningQuestionsResponse(
        candidate_id=candidate_id,
        questions=questions,
    )


@router.post("/screening/{candidate_id}/submit", response_model=schemas.ScreeningSubmitResponse)
def submit_screening(
    candidate_id: int,
    body: schemas.ScreeningSubmitRequest,
    db: Session = Depends(get_db),
):
    """Submit screening answers for evaluation."""
    candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    evaluation = run_screening_evaluation(
        resume_text=candidate.resume_text or "",
        candidate_name=candidate.name,
        job_role=candidate.job_role,
        questions=body.questions,
        answers=body.answers,
    )

    # Persist Q&A to interview_qas table
    for q, a in zip(body.questions, body.answers):
        qa = models.InterviewQA(
            candidate_id=candidate_id,
            question_text=q,
            answer_text=a,
            score=0.0,
            reasoning=evaluation,
            stage="HR_Screening",
        )
        db.add(qa)

    # Advance pipeline stage
    candidate.pipeline_stage = "Scheduling"
    candidate.notes = (candidate.notes or "") + f"\n\nHR Screening Evaluation:\n{evaluation}"
    db.commit()
    db.refresh(candidate)

    return schemas.ScreeningSubmitResponse(
        candidate_id=candidate_id,
        evaluation=evaluation,
        pipeline_stage=candidate.pipeline_stage,
    )


# ── Interview Scheduling ───────────────────────────────────────────────

@router.post("/schedule/{candidate_id}", response_model=schemas.ScheduleResponse)
def schedule_interview(
    candidate_id: int,
    body: schemas.ScheduleRequest,
    db: Session = Depends(get_db),
):
    """Schedule an interview: generate meeting link and send confirmation emails."""
    candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    result = run_scheduling_pipeline(
        email=candidate.email,
        candidate_name=candidate.name,
        job_role=candidate.job_role,
        availability=body.availability,
    )

    # Update candidate stage
    candidate.pipeline_stage = "Scheduled"
    candidate.notes = (candidate.notes or "") + f"\n\nMeeting Link: {result['meeting_link']}\nEmail: {result['email_status']}"
    db.commit()
    db.refresh(candidate)

    return schemas.ScheduleResponse(
        candidate_id=candidate_id,
        meeting_link=result["meeting_link"],
        email_status=result["email_status"],
        pipeline_stage=candidate.pipeline_stage,
    )
