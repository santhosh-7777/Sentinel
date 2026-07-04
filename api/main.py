from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from agent.agent import executor

app = FastAPI(title="Sentinel Agent API")

# In-memory session store, fine for a demo
SESSIONS: dict[str, list] = {}


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    steps: list[dict]


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    history = SESSIONS.get(req.session_id, [])

    result = executor.invoke({"input": req.message, "chat_history": history})

    # Extract tool-call steps so the frontend can show the reasoning trace
    steps = []
    for action, observation in result.get("intermediate_steps", []):
        steps.append(
            {
                "tool": action.tool,
                "input": action.tool_input,
                "output": str(observation),
            }
        )

    response_text = result["output"]

    history.append(HumanMessage(content=req.message))
    history.append(AIMessage(content=response_text))
    SESSIONS[req.session_id] = history

    return ChatResponse(response=response_text, steps=steps)


@app.post("/reset")
def reset(session_id: str):
    SESSIONS.pop(session_id, None)
    return {"status": "reset"}


@app.get("/health")
def health():
    return {"status": "ok"}