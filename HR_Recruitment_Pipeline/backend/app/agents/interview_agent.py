from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
import json


class InterviewState(TypedDict):
    candidate_id: int
    job_role: str
    experience_level: str
    questions_asked: List[str]
    current_question: str
    answers: List[str]
    scores: List[float]
    reasonings: List[str]
    total_score: float
    is_complete: bool
    max_questions: int


def _get_llm():
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.7,
    )


def generate_question_node(state: InterviewState):
    """Use LLM to generate a unique technical interview question."""
    idx = len(state["questions_asked"])
    if idx >= state["max_questions"]:
        return {"is_complete": True}

    llm = _get_llm()

    previously_asked = "\n".join(
        [f"- {q}" for q in state["questions_asked"]]
    ) if state["questions_asked"] else "No questions asked yet."

    system_prompt = """You are a technical interviewer for a tech company.
Generate ONE concise technical interview question appropriate for the given role and experience level.
The question should test practical knowledge, problem-solving ability, or system design thinking.
Do NOT repeat any previously asked questions.
Return ONLY the question text — no numbering, no preamble, no formatting."""

    human_prompt = f"""Role: {state["job_role"]}
Experience Level: {state["experience_level"]}
Question Number: {idx + 1} of {state["max_questions"]}

Previously Asked Questions:
{previously_asked}

Generate the next question."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ])
        question = response.content.strip()
    except Exception as e:
        # Fallback: Static questions for the role
        fallbacks = {
            "Software Engineer": [
                "Explain the difference between a Process and a Thread.",
                "How does a hash map resolve collisions internally?",
                "Describe the SOLID principles in object-oriented design."
            ],
            "Frontend Developer": [
                "Explain the Virtual DOM and how React uses it.",
                "What are the different ways to handle state management in a large app?",
                "Describe the CSS Box Model and how it affects layout."
            ]
        }
        role_questions = fallbacks.get(state["job_role"], [
            f"Describe your typical workflow for a {state['job_role']} task.",
            "What are the most common challenges you face in this role?",
            "How do you ensure the quality of your work?"
        ])
        question = role_questions[idx % len(role_questions)]
        # Add fallback indicator
        question = f"(Fallback Mode: LLM Unavailable) {question}" 


    return {
        "current_question": question,
        "questions_asked": state["questions_asked"] + [question],
    }


def evaluate_answer_node(state: InterviewState):
    """Use LLM to evaluate the candidate's answer."""
    if state["is_complete"] or not state["answers"]:
        return state

    latest_answer = state["answers"][-1]
    latest_question = state["questions_asked"][-1] if state["questions_asked"] else ""

    # Handle timeout / empty answers
    if latest_answer in ("NO_ANSWER_TIMEOUT", ""):
        return {
            "scores": state["scores"] + [0.0],
            "reasonings": state["reasonings"] + ["No answer provided (timeout)."],
            "total_score": (sum(state["scores"]) + 0.0) / (len(state["scores"]) + 1),
        }

    llm = _get_llm()

    system_prompt = """You are evaluating a technical interview answer.
Score the answer from 0 to 100 based on:
1. Technical accuracy
2. Depth of understanding
3. Clarity of communication
4. Relevance to the question

You MUST respond with ONLY valid JSON in this format, no other text:
{
    "score": <float between 0 and 100>,
    "reasoning": "<1-2 sentence evaluation>"
}"""

    human_prompt = f"""Question: {latest_question}

Candidate's Answer: {latest_answer}

Evaluate this answer. Return ONLY the JSON."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ])

        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            content = content.rsplit("```", 1)[0]
        result = json.loads(content.strip())
        score = float(result.get("score", 0))
        reasoning = result.get("reasoning", "No reasoning provided.")
    except Exception as e:
        # Heuristic Fallback: Score based on length and common tech keywords
        ans_len = len(latest_answer)
        keywords = ["api", "data", "system", "performance", "code", "test", "design", "security", "cloud"]
        match_count = sum(1 for kw in keywords if kw in latest_answer.lower())
        
        score = min(40 + (match_count * 10) + (ans_len // 50), 90)
        reasoning = f"(Fallback Mode) Gemini API error: {str(e)[:50]}. Scoring based on answer length and keyword density."


    score = min(max(score, 0), 100)
    new_scores = state["scores"] + [score]
    new_reasonings = state["reasonings"] + [reasoning]
    total = sum(new_scores) / len(new_scores)

    return {
        "scores": new_scores,
        "reasonings": new_reasonings,
        "total_score": total,
    }


builder = StateGraph(InterviewState)
builder.add_node("generate_question", generate_question_node)
builder.add_node("evaluate_answer", evaluate_answer_node)
builder.add_edge("generate_question", "evaluate_answer")
builder.add_edge("evaluate_answer", END)

builder.set_entry_point("generate_question")
interview_graph = builder.compile()


def init_interview_state(
    candidate_id: int,
    job_role: str,
    experience_level: str = "junior",
    max_questions: int = 3,
) -> InterviewState:
    return InterviewState(
        candidate_id=candidate_id,
        job_role=job_role,
        experience_level=experience_level,
        questions_asked=[],
        current_question="",
        answers=[],
        scores=[],
        reasonings=[],
        total_score=0.0,
        is_complete=False,
        max_questions=max_questions,
    )
