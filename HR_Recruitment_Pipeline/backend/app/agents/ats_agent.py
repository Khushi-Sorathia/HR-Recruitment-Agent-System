from typing import TypedDict
from langgraph.graph import StateGraph, END
import random

class ATSState(TypedDict):
    resume_text: str
    job_role: str
    score: float
    reasoning: str
    pass_screening: bool

def ats_scoring_node(state: ATSState):
    # Mocking LLM ATS scoring logic using keyword matching heuristics
    # In production, this replaces with langchain_openai.ChatOpenAI call
    resume = state["resume_text"].lower()
    role = state["job_role"].lower()
    
    base_score = 60.0
    if role in resume:
        base_score += 15.0
        
    keywords = ["python", "fastapi", "react", "langgraph", "sql", "ai", "engineer", "agent"]
    matches = sum(1 for kw in keywords if kw in resume)
    base_score += matches * 5.0
    
    final_score = min(base_score, 100.0)
    
    return {
        "score": final_score,
        "reasoning": f"Based on keyword match. Overlap score: {final_score}",
        "pass_screening": final_score >= 80.0
    }

builder = StateGraph(ATSState)
builder.add_node("ats_scoring", ats_scoring_node)
builder.set_entry_point("ats_scoring")
builder.add_edge("ats_scoring", END)

ats_graph = builder.compile()

def run_ats_pipeline(resume_text: str, job_role: str):
    initial_state = ATSState(
        resume_text=resume_text,
        job_role=job_role,
        score=0.0,
        reasoning="",
        pass_screening=False
    )
    result = ats_graph.invoke(initial_state)
    return result
