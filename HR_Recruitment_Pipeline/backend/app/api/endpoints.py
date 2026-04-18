from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models, schemas

router = APIRouter()

@router.post("/upload-resume", response_model=schemas.CandidateResponse)
async def upload_resume(
    name: str = Form(...),
    email: str = Form(...),
    job_role: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    text = await file.read()
    # In a real app we parse PDF to text here. For MVP we decode if text.
    try:
        resume_content = text.decode("utf-8", errors="ignore")
    except:
        resume_content = str(text)
    
    # Run ATS Agent...
    # For now, placeholder
    ats_score = 85.0
    pass_screening = ats_score >= 80.0
    
    new_candidate = models.Candidate(
        name=name,
        email=email,
        job_role=job_role,
        resume_text=resume_content,
        ats_score=ats_score,
        pipeline_stage="Technical Interview" if pass_screening else "Rejected"
    )
    db.add(new_candidate)
    db.commit()
    db.refresh(new_candidate)
    return new_candidate

@router.get("/dashboard", response_model=list[schemas.CandidateResponse])
def get_dashboard(db: Session = Depends(get_db)):
    candidates = db.query(models.Candidate).all()
    return candidates

# Placeholder for websocket endpoints
@router.websocket("/interview/{candidate_id}")
async def interview_endpoint(websocket: WebSocket, candidate_id: int):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        pass
