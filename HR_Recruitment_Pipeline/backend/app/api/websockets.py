from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.db.database import get_db, SessionLocal
from sqlalchemy.orm import Session
from app.db import models
from app.agents.interview_agent import init_interview_state, interview_graph
from app.agents.hr_chatbot_agent import run_chatbot_query
import json
import asyncio

router = APIRouter()


@router.websocket("/interview/{candidate_id}")
async def technical_interview(websocket: WebSocket, candidate_id: int):
    await websocket.accept()

    # Get candidate info from DB
    db = SessionLocal()
    try:
        candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
        if not candidate:
            await websocket.send_json({"type": "error", "text": "Candidate not found."})
            await websocket.close()
            return

        job_role = candidate.job_role

        # Initialize interview state
        state = init_interview_state(candidate_id, job_role)

        # Generate and send first question
        state = interview_graph.invoke(state)
        await websocket.send_json({
            "type": "question",
            "text": state["current_question"],
            "timeout": 30,
            "questionNumber": len(state["questions_asked"]),
            "totalQuestions": state["max_questions"],
        })

        while not state["is_complete"]:
            # Await answer from frontend (30s + 5s buffer)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=35.0)
                state["answers"].append(data)
            except asyncio.TimeoutError:
                state["answers"].append("NO_ANSWER_TIMEOUT")

            # Step graph forward (evaluate answer + generate next question)
            state = interview_graph.invoke(state)

            if state["is_complete"]:
                # Persist all Q&A pairs to database
                for i, (q, a) in enumerate(zip(state["questions_asked"], state["answers"])):
                    score = state["scores"][i] if i < len(state["scores"]) else 0.0
                    reasoning = state["reasonings"][i] if i < len(state["reasonings"]) else ""
                    qa = models.InterviewQA(
                        candidate_id=candidate_id,
                        question_text=q,
                        answer_text=a,
                        score=score,
                        reasoning=reasoning,
                        stage="Technical",
                    )
                    db.add(qa)

                # Update candidate total score and stage
                candidate.total_score = state["total_score"]
                candidate.pipeline_stage = "HR Screening"
                candidate.notes = (candidate.notes or "") + f"\n\nTechnical Interview Score: {state['total_score']:.1f}/100"
                db.commit()

                await websocket.send_json({
                    "type": "completion",
                    "text": f"Interview Complete! Your score: {state['total_score']:.1f}/100",
                    "score": round(state["total_score"], 1),
                    "details": [
                        {"question": q, "score": s, "reasoning": r}
                        for q, s, r in zip(
                            state["questions_asked"],
                            state["scores"],
                            state["reasonings"],
                        )
                    ],
                })
                break
            else:
                await websocket.send_json({
                    "type": "question",
                    "text": state["current_question"],
                    "timeout": 30,
                    "questionNumber": len(state["questions_asked"]),
                    "totalQuestions": state["max_questions"],
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "text": str(e)})
        except Exception:
            pass
    finally:
        db.close()


@router.websocket("/hr-chatbot")
async def hr_chatbot(websocket: WebSocket):
    await websocket.accept()
    db = SessionLocal()
    try:
        while True:
            data = await websocket.receive_text()
            response = run_chatbot_query(data, db)
            await websocket.send_text(response)
    except WebSocketDisconnect:
        pass
    finally:
        db.close()
