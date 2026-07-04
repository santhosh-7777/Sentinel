Sentinel

An agentic AI system for infrastructure fault detection, diagnosis, and remediation. Built as a demonstration of agentic workflows in the style of AI-driven infrastructure management platforms.

What it does

Sentinel investigates infrastructure issues (CPU, memory, disk, temperature) using an LLM-based agent that reasons through a structured loop instead of a single-shot response.

The loop:
1. Check current metrics for the affected server
2. Check for known CVEs if relevant
3. Search past incidents for similar historical patterns using vector retrieval
4. Propose a specific remediation action
5. Request explicit human approval before taking any action
6. Execute the approved fix (simulated) and explain the outcome in plain language

Human approval is required before any remediation executes. Nothing runs autonomously without a confirmed yes from the user.

Architecture

Agent: LangChain tool-calling agent, powered by Groq's LLaMA 3.3 70B
Retrieval: FAISS vector store with sentence-transformers embeddings, holding a small set of past incident records
Backend: FastAPI, exposing a single /chat endpoint that the frontend calls
Frontend: Streamlit chat interface with a visible reasoning trace, showing every tool call the agent made for a given response
Metrics: Simulated server metrics with gradual drift patterns per server, so repeated checks show realistic degradation rather than pure randomness

Tools available to the agent

check_metrics - returns current CPU, memory, disk I/O, and temperature for a server
check_cve - queries the NVD database for known vulnerabilities
search_similar_incidents - retrieves similar past incidents from the FAISS store
propose_remediation - suggests a remediation action based on the issue type
execute_fix - simulates executing a remediation command, gated behind human approval

Running locally

Install dependencies:
pip install -r requirements.txt

Set your Groq API key in a .env file:
GROQ_API_KEY=your_key_here

Start the backend:
uvicorn api.main:app --reload

Start the frontend in a separate terminal:
streamlit run app/streamlit_app.py

Project structure

agent/ - agent definition and tool implementations
api/ - FastAPI backend
app/ - Streamlit frontend
data/ - incident history and simulated metrics generator

Notes

Remediation execution is simulated rather than connected to real infrastructure, since this project has no live servers to act on. The execute_fix tool is structured so it could be pointed at a real orchestration layer (SSH, Ansible, a Kubernetes job) with minimal changes, but every execution still passes through the same human approval gate.
