# AI HR Recruitment Pipeline MVP

[cite_start]This document outlines the Minimum Viable Product for the AI powered HR recruitment system[cite: 7]. It provides clear user stories to guide development and specific setup instructions.

## User Stories for MVP Development

Use these stories to build the core modules.

* [cite_start]**Resume Ingestion**: As a system administrator, I want an agent to accept a resume upload and parse its content[cite: 16, 17]. [cite_start]The agent must score the document against a job description using skill matching and keyword relevance[cite: 17]. [cite_start]Candidates scoring 80 percent or above must proceed to the interview stage[cite: 18].
* [cite_start]**Technical Interview**: As a candidate, I want to participate in a timed technical interview with questions generated based on the role experience level[cite: 20, 21]. [cite_start]I must type responses within 30 seconds per question[cite: 22]. [cite_start]The system must disable copy paste functionality in the input field[cite: 22, 23].
* [cite_start]**HR Screening**: As an HR user, I want an agent to conduct a screening based on the candidate resume[cite: 25, 26]. [cite_start]The agent must ask about notice periods and joining dates without repeating questions the resume already answers[cite: 26, 27].
* [cite_start]**Interview Scheduling**: As an HR user, I want the system to collect candidate availability and generate a meeting link[cite: 29, 30]. [cite_start]The system must send confirmation emails to the candidate and the HR team simultaneously[cite: 30].
* [cite_start]**HR Dashboard**: As an HR user, I want a dashboard displaying all candidates, their current pipeline stage, and their scores[cite: 33, 34]. [cite_start]I need the ability to filter data by role and stage[cite: 34, 35].
* [cite_start]**HR Chatbot**: As an HR user, I want a conversational agent on the dashboard to query the pipeline and change candidate stages[cite: 39, 40]. [cite_start]The chatbot must answer using only persisted database queries[cite: 40, 41].

## Technology Stack

You must build this MVP using specific tools.

* [cite_start]Python, LangGraph, and FastAPI are mandatory[cite: 11]. [cite_start]Every agent must operate as a graph using LangGraph[cite: 47]. [cite_start]All agent endpoints must run on FastAPI[cite: 48].
* [cite_start]React and TypeScript will handle the frontend WebSockets required for the interview timer[cite: 49].
* [cite_start]PostgreSQL will manage long term memory persistence[cite: 45].
* [cite_start]Pydantic will handle structured data validation[cite: 56].

