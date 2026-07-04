import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from agent.tools import ALL_TOOLS

load_dotenv()

# LLM setup - Groq's LLaMA 3.3 70B, temperature 0 for consistent decisions
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)

# System prompt defining the detect -> retrieve -> decide -> approve -> act -> explain loop
SYSTEM_PROMPT = """You are Sentinel, an agentic AI infrastructure engineer.

Your job when investigating an issue:
1. Check current metrics for the affected server using check_metrics.
2. If relevant, check for known vulnerabilities using check_cve.
3. Search past incidents using search_similar_incidents to ground your diagnosis
   in real historical patterns rather than guessing.
4. Propose a specific remediation using propose_remediation.
5. Before executing anything with execute_fix, always ask the human for
   explicit approval first - describe the proposed action clearly and wait.
   Only call execute_fix with approved=True if the user has clearly said yes
   in this conversation. Always pass the server_id you were investigating.
6. Always explain your findings and actions in clear, plain English - the user
   is a human operator, not a machine. Avoid jargon dumps; be concise and direct.

Never skip the retrieval step, and never execute a fix without explicit approval.
"""

# Prompt template with chat history support for multi-turn memory
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ]
)

# Build the tool-calling agent and its executor
agent = create_tool_calling_agent(llm, ALL_TOOLS, prompt)

executor = AgentExecutor(
    agent=agent,
    tools=ALL_TOOLS,
    verbose=True,  # prints each tool call live to the terminal
    max_iterations=8,
)


def run_agent(user_input: str, chat_history: list) -> str:
    # Runs one turn of the agent, passing prior history for context
    result = executor.invoke({"input": user_input, "chat_history": chat_history})
    return result["output"]


if __name__ == "__main__":
    from langchain_core.messages import HumanMessage, AIMessage

    # Simple terminal chat loop for manual testing
    print("Sentinel agent ready. Type a question (or 'quit' to exit).\n")
    history = []
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() in ("quit", "exit"):
            break
        response = run_agent(user_input, history)
        print(f"\nSentinel: {response}\n")
        history.append(HumanMessage(content=user_input))
        history.append(AIMessage(content=response))