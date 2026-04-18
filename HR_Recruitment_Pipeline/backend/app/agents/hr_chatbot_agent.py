from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
import json


class ChatbotState(TypedDict):
    query: str
    response: str
    sql_query: str
    sql_result: str


DB_SCHEMA = """
Table: candidates
Columns:
  - id (INTEGER, PRIMARY KEY)
  - name (VARCHAR, indexed)
  - email (VARCHAR, unique, indexed)
  - resume_text (TEXT)
  - job_role (VARCHAR, indexed)
  - ats_score (FLOAT)
  - total_score (FLOAT)
  - pipeline_stage (VARCHAR) — values: 'Resume Ingestion', 'Rejected', 'Technical Interview', 'HR Screening', 'Scheduling', 'Scheduled', 'Offer'
  - created_at (DATETIME)
  - notes (TEXT, nullable)

Table: interview_qas
Columns:
  - id (INTEGER, PRIMARY KEY)
  - candidate_id (INTEGER, FOREIGN KEY → candidates.id)
  - question_text (TEXT)
  - answer_text (TEXT, nullable)
  - score (FLOAT)
  - reasoning (TEXT, nullable)
  - stage (VARCHAR) — 'Technical' or 'HR_Screening'
  - created_at (DATETIME)
"""

VALID_STAGES = [
    "Resume Ingestion", "Rejected", "Technical Interview",
    "HR Screening", "Scheduling", "Scheduled", "Offer",
]


def _get_llm():
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.1,
    )


def parse_intent_node(state: ChatbotState):
    """Use LLM to understand intent and generate safe SQL."""
    llm = _get_llm()

    system_prompt = f"""You are an HR database assistant. Given an HR user's natural language query,
generate a safe SQL query to answer it.

Here is the database schema:
{DB_SCHEMA}

Rules:
1. For read queries, generate SELECT statements only.
2. For stage change requests (e.g. "move candidate X to Offer"), generate an UPDATE
   on the pipeline_stage column ONLY. Valid stages: {VALID_STAGES}
3. NEVER generate DELETE, DROP, ALTER, CREATE, INSERT, or TRUNCATE statements.
4. Use ILIKE for name searches (case-insensitive matching).
5. Limit SELECT results to 50 rows max.

You MUST respond with ONLY valid JSON in this format, no other text:
{{"sql": "<the SQL query>", "is_update": false}}

Set is_update to true only for UPDATE queries."""

    human_prompt = f"HR Query: {state['query']}"

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ])
        content = response.content.strip()
    except Exception as e:
        # Heuristic Fallback: basic regex for common intents
        q = state["query"].lower()
        if "how many" in q or "count" in q:
            sql = "SELECT count(*) FROM candidates"
        elif "list" in q or "all candidates" in q or "show candidates" in q:
            sql = "SELECT id, name, email, job_role, pipeline_stage FROM candidates LIMIT 10"
        elif "rejected" in q:
            sql = "SELECT name, job_role FROM candidates WHERE pipeline_stage = 'Rejected'"
        elif "interview" in q:
            sql = "SELECT name, job_role FROM candidates WHERE pipeline_stage = 'Technical Interview'"
        else:
            return {
                "sql_query": "",
                "response": f"(Fallback Mode) Gemini API error: {str(e)[:50]}. Try queries like 'list candidates', 'how many candidates', or 'show rejected'."
            }
        return {"sql_query": sql}


    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            content = content.rsplit("```", 1)[0]
        result = json.loads(content.strip())
        sql = result.get("sql", "")

        # Safety check: block dangerous operations
        sql_upper = sql.upper().strip()
        dangerous = ["DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT"]
        if any(sql_upper.startswith(d) for d in dangerous):
            return {
                "sql_query": "",
                "response": "I cannot execute destructive database operations. Please rephrase your query.",
            }

        return {"sql_query": sql}
    except (json.JSONDecodeError, ValueError, AttributeError):
        return {
            "sql_query": "",
            "response": "I couldn't understand that query. Could you rephrase it?",
        }


def db_execution_node(state: ChatbotState, db: Session):
    """Execute the generated SQL against the real database."""
    if not state["sql_query"]:
        # parse_intent_node already set a response
        return state

    try:
        result = db.execute(text(state["sql_query"]))

        if state["sql_query"].strip().upper().startswith("UPDATE"):
            db.commit()
            return {"sql_result": f"Update successful. Rows affected: {result.rowcount}"}
        else:
            rows = result.fetchall()
            columns = list(result.keys()) if rows else []
            if not rows:
                return {"sql_result": "No results found."}

            # Format results as readable text
            formatted = []
            for row in rows[:50]:
                row_dict = dict(zip(columns, row))
                formatted.append(str(row_dict))
            return {"sql_result": "\n".join(formatted)}
    except Exception as e:
        return {"sql_result": f"Database error: {str(e)}"}


def format_response_node(state: ChatbotState):
    """Use LLM to format raw SQL results into a human-readable response."""
    if state.get("response"):
        # Already has a response from earlier nodes (error case)
        return state

    if not state.get("sql_result"):
        return {"response": "I couldn't find any relevant data."}

    llm = _get_llm()

    system_prompt = """You are an HR assistant. Format the given database query results into a
clear, human-readable response. Be concise and helpful. If it's a count, state the number clearly.
If it's a list of candidates, present it neatly. Do not include raw SQL or technical details."""

    human_prompt = f"""Original HR Query: {state['query']}
SQL Executed: {state['sql_query']}
Raw Results: {state['sql_result'][:2000]}

Format this into a helpful response for the HR user."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ])
        return {"response": response.content.strip()}
    except Exception:
        # Fallback: Just return raw results if formatting fails
        return {"response": f"(Raw Output) {state['sql_result']}"}



# Note: The chatbot graph cannot use the standard StateGraph compilation
# because db_execution_node needs a DB session parameter.
# Instead, we manually orchestrate the nodes in run_chatbot_query.


def run_chatbot_query(query: str, db: Session) -> str:
    """Run the full chatbot pipeline: parse → execute → format."""
    state = ChatbotState(
        query=query,
        response="",
        sql_query="",
        sql_result="",
    )

    # Step 1: Parse intent and generate SQL
    updates = parse_intent_node(state)
    state = {**state, **updates}

    # If parse_intent already set a response (error), return it
    if state.get("response"):
        return state["response"]

    # Step 2: Execute SQL against DB
    updates = db_execution_node(state, db)
    state = {**state, **updates}

    # Step 3: Format response
    updates = format_response_node(state)
    state = {**state, **updates}

    return state.get("response", "I couldn't process that query.")
