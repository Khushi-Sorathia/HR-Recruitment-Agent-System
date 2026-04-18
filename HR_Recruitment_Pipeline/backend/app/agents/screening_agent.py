from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ScreeningState(TypedDict):
    resume_text: str
    questions: List[str]

def generate_screening_questions_node(state: ScreeningState):
    # Mock finding what's missing in resume
    resume = state["resume_text"].lower()
    questions = []
    
    if "notice period" not in resume:
        questions.append("What is your current notice period?")
    if "joining date" not in resume:
        questions.append("What would be your earliest available joining date?")
    if "graduation date" not in resume and "student" in resume:
        questions.append("When is your expected graduation date?")
        
    if not questions:
        questions.append("Can you confirm your availability to join within the next 30 days?")
        
    state["questions"] = questions
    return state

builder = StateGraph(ScreeningState)
builder.add_node("generate", generate_screening_questions_node)
builder.set_entry_point("generate")
builder.add_edge("generate", END)

screening_graph = builder.compile()

def run_screening_generator(resume_text: str):
    state = ScreeningState(resume_text=resume_text, questions=[])
    result = screening_graph.invoke(state)
    return result["questions"]
