from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChatbotState(TypedDict):
    query: str
    response: str
    sql_query: str

def parse_intent_node(state: ChatbotState):
    # Mock Intent Parsing
    query = state["query"].lower()
    if "how many" in query and "interview" in query:
        state["sql_query"] = "SELECT COUNT(*) FROM candidates WHERE pipeline_stage='Technical Interview';"
    elif "move candidate" in query:
        # Pseudo intent logic
        state["sql_query"] = "UPDATE candidates SET pipeline_stage='Offer' WHERE id=?"; 
    else:
        state["sql_query"] = "SELECT * FROM candidates;"
    return state

def db_execution_node(state: ChatbotState):
    # In production, uses DB connection and Langchain SQL Toolkit
    state["response"] = f"Based on the database, I executed `{state['sql_query']}` and here is your result."
    return state

builder = StateGraph(ChatbotState)
builder.add_node("parse_intent", parse_intent_node)
builder.add_node("db_execution", db_execution_node)
builder.add_edge("parse_intent", "db_execution")
builder.add_edge("db_execution", END)
builder.set_entry_point("parse_intent")

chatbot_graph = builder.compile()

def run_chatbot_query(query: str):
    state = ChatbotState(query=query, response="", sql_query="")
    result = chatbot_graph.invoke(state)
    return result["response"]
