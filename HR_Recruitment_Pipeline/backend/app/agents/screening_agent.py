from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
import json


class ScreeningState(TypedDict):
    resume_text: str
    candidate_name: str
    job_role: str
    questions: List[str]
    answers: List[str]
    evaluation: str


def _get_llm():
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.3,
    )


def generate_screening_questions_node(state: ScreeningState):
    """Use LLM to identify what HR-relevant info is missing from the resume and generate questions."""
    llm = _get_llm()

    system_prompt = """You are an HR screening specialist. Your task is to analyze a candidate's resume
and generate screening questions about information that is NOT already present in the resume.

Focus on:
- Notice period (if not mentioned)
- Earliest joining date (if not mentioned)
- Salary expectations (if not mentioned)
- Reason for leaving current role (if currently employed)
- Willingness to relocate (if role requires it)
- Any employment gaps

Do NOT ask about things the resume already clearly states.
Generate 3-5 targeted screening questions.

You MUST respond with ONLY a valid JSON array of question strings, no other text:
["Question 1?", "Question 2?", "Question 3?"]"""

    human_prompt = f"""Candidate: {state["candidate_name"]}
Role Applied For: {state["job_role"]}

Resume Content:
{state["resume_text"][:4000]}

Generate screening questions for information missing from this resume. Return ONLY the JSON array."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ])

        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            content = content.rsplit("```", 1)[0]
        questions = json.loads(content.strip())
        if not isinstance(questions, list):
            raise ValueError("Response not a list")
    except Exception as e:
        # Fallback: Basic HR questions
        questions = [
            "What is your notice period and earliest possible joining date?",
            "What are your current and expected salary expectations?",
            "Can you explain the reason for leaving your current/last company?"
        ]
        # Indicate fallback
        questions = [f"(LLM Offline) {q}" for q in questions]


    return {"questions": questions}


def evaluate_screening_node(state: ScreeningState):
    """Use LLM to evaluate the candidate's screening answers and produce a summary."""
    if not state["answers"]:
        return {"evaluation": "No answers provided."}

    llm = _get_llm()

    qa_pairs = "\n".join([
        f"Q: {q}\nA: {a}"
        for q, a in zip(state["questions"], state["answers"])
    ])

    system_prompt = """You are an HR specialist evaluating screening responses.
Based on the candidate's answers, provide a brief assessment covering:
1. Availability and notice period
2. Salary/compensation alignment
3. Overall HR fit assessment
4. Any concerns or flags

Keep the evaluation concise (3-5 sentences). Return plain text, no JSON."""

    human_prompt = f"""Candidate: {state["candidate_name"]}
Role: {state["job_role"]}

Screening Q&A:
{qa_pairs}

Provide your evaluation."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ])
        evaluation = response.content.strip()
    except Exception as e:
        # Heuristic Assessment
        all_answers = " ".join(state["answers"]).lower()
        has_salary = "salary" in all_answers or "$" in all_answers or "expected" in all_answers
        has_notice = "notice" in all_answers or "immediate" in all_answers or "week" in all_answers
        
        evaluation = "(Fallback Mode) Assessment based on response completion:\n"
        evaluation += f"- Availability details provided: {'Yes' if has_notice else 'Vague'}.\n"
        evaluation += f"- Compensation details provided: {'Yes' if has_salary else 'Vague'}.\n"
        evaluation += "- Recommendation: Proceed with human review to confirm details."



builder = StateGraph(ScreeningState)
builder.add_node("generate", generate_screening_questions_node)
builder.add_node("evaluate", evaluate_screening_node)
builder.set_entry_point("generate")
builder.add_edge("generate", END)

# Evaluation is a separate entry for when answers are submitted
eval_builder = StateGraph(ScreeningState)
eval_builder.add_node("evaluate", evaluate_screening_node)
eval_builder.set_entry_point("evaluate")
eval_builder.add_edge("evaluate", END)

screening_graph = builder.compile()
screening_eval_graph = eval_builder.compile()


def run_screening_generator(resume_text: str, candidate_name: str, job_role: str) -> list:
    state = ScreeningState(
        resume_text=resume_text,
        candidate_name=candidate_name,
        job_role=job_role,
        questions=[],
        answers=[],
        evaluation="",
    )
    result = screening_graph.invoke(state)
    return result["questions"]


def run_screening_evaluation(
    resume_text: str,
    candidate_name: str,
    job_role: str,
    questions: list,
    answers: list,
) -> str:
    state = ScreeningState(
        resume_text=resume_text,
        candidate_name=candidate_name,
        job_role=job_role,
        questions=questions,
        answers=answers,
        evaluation="",
    )
    result = screening_eval_graph.invoke(state)
    return result["evaluation"]
