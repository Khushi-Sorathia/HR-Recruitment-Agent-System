from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
import json

class InterviewState(TypedDict):
    candidate_id: int
    job_role: str
    experience_level: str
    questions_asked: List[str]
    current_question: str
    answers: List[str]
    scores: List[float]
    total_score: float
    is_complete: bool

def generate_question_node(state: InterviewState):
    # Mock dynamic question generation based on role
    idx = len(state["questions_asked"])
    if idx >= 3: # 3 questions max for MVP
        state["is_complete"] = True
        return state
        
    role = state["job_role"].lower()
    level = state["experience_level"].lower()
    question = f"Q{idx+1}: Describe a complex issue you solved using {role} for a {level} level scenario."
    state["current_question"] = question
    state["questions_asked"].append(question)
    return state

def evaluate_answer_node(state: InterviewState):
    if state["is_complete"] or not state["answers"]:
        return state
        
    latest_answer = state["answers"][-1]
    # Mock LLM evaluation logic
    score = min(100.0, max(0.0, len(latest_answer) * 2.0)) 
    state["scores"].append(score)
    
    if len(state["scores"]) > 0:
        state["total_score"] = sum(state["scores"]) / len(state["scores"])
    return state

builder = StateGraph(InterviewState)
builder.add_node("generate_question", generate_question_node)
builder.add_node("evaluate_answer", evaluate_answer_node)
builder.add_edge("generate_question", "evaluate_answer")
builder.add_edge("evaluate_answer", END)

builder.set_entry_point("generate_question")
interview_graph = builder.compile()

def init_interview_state(candidate_id: int, job_role: str, experience_level: str = "junior") -> InterviewState:
    return InterviewState(
        candidate_id=candidate_id,
        job_role=job_role,
        experience_level=experience_level,
        questions_asked=[],
        current_question="",
        answers=[],
        scores=[],
        total_score=0.0,
        is_complete=False
    )
