from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.agents.interview_agent import init_interview_state, interview_graph
from app.agents.hr_chatbot_agent import run_chatbot_query
import json
import asyncio

router = APIRouter()

@router.websocket("/interview/{candidate_id}")
async def technical_interview(websocket: WebSocket, candidate_id: int):
    await websocket.accept()
    # Initialize session
    state = init_interview_state(candidate_id, "Software Engineer")
    
    # Generate and send first question
    state = interview_graph.invoke(state)
    await websocket.send_json({"type": "question", "text": state["current_question"], "timeout": 30})
    
    try:
        while not state["is_complete"]:
            # Await answer from frontend with timeout fallback implemented on frontend mostly 
            # but backend can enforce
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=35.0) # 30s + 5s buffer
                state["answers"].append(data)
            except asyncio.TimeoutError:
                state["answers"].append("NO_ANSWER_TIMEOUT")
            
            # Step graph forward
            state = interview_graph.invoke(state)
            
            if state["is_complete"]:
                await websocket.send_json({
                    "type": "completion", 
                    "text": f"Interview Complete. Score: {state['total_score']:.2f}"
                })
                break
            else:
                await websocket.send_json({"type": "question", "text": state["current_question"], "timeout": 30})
    except WebSocketDisconnect:
        # Save partial state logic here if needed
        pass

@router.websocket("/hr-chatbot")
async def hr_chatbot(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            response = run_chatbot_query(data)
            await websocket.send_text(response)
    except WebSocketDisconnect:
        pass
