from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
import json


class ATSState(TypedDict):
    resume_text: str
    job_role: str
    score: float
    reasoning: str
    pass_screening: bool


def _get_llm():
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.1,
    )


def ats_scoring_node(state: ATSState):
    """Use LLM to score resume against the job role."""
    llm = _get_llm()

    system_prompt = """You are an expert Applicant Tracking System (ATS) evaluator.
Your task is to score a candidate's resume against a target job role.

Evaluate based on:
1. Skill relevance — do the listed skills match the job role requirements?
2. Experience alignment — does the candidate's experience level and domain fit?
3. Keyword relevance — are important industry keywords present?
4. Education fit — does the educational background support the role?
5. Project relevance — do described projects demonstrate capability for this role?

You MUST respond with ONLY valid JSON in this exact format, no other text:
{
    "score": <float between 0 and 100>,
    "reasoning": "<2-3 sentence justification for the score>"
}"""

    human_prompt = f"""Job Role: {state["job_role"]}

Resume Content:
{state["resume_text"][:4000]}

Score this resume against the job role. Return ONLY the JSON."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ])

        # Clean the response content — strip markdown fences if present
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            content = content.rsplit("```", 1)[0]
        result = json.loads(content.strip())
        score = float(result.get("score", 0))
        reasoning = result.get("reasoning", "No reasoning provided.")
    except Exception as e:
        # Heuristic Fallback if LLM fails (e.g. Quota Exceeded)
        resume = state["resume_text"].lower()
        role = state["job_role"].lower()
        
        # Simple keyword matching for fallback
        keywords = ["python", "fastapi", "react", "sql", "aws", "docker", "javascript", "typescript"]
        matches = sum(1 for kw in keywords if kw in resume)
        score = min(60 + (matches * 5), 95) if role in resume else min(40 + (matches * 5), 75)
        reasoning = f"(Fallback Mode) Gemini API unavailable: {str(e)[:100]}. Evaluation based on keyword matching."

    return {
        "score": min(max(score, 0), 100),
        "reasoning": reasoning,
        "pass_screening": score >= 80.0,
    }


builder = StateGraph(ATSState)
builder.add_node("ats_scoring", ats_scoring_node)
builder.set_entry_point("ats_scoring")
builder.add_edge("ats_scoring", END)

ats_graph = builder.compile()


def run_ats_pipeline(resume_text: str, job_role: str) -> dict:
    initial_state = ATSState(
        resume_text=resume_text,
        job_role=job_role,
        score=0.0,
        reasoning="",
        pass_screening=False,
    )
    result = ats_graph.invoke(initial_state)
    return result
