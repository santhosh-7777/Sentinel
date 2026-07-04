import uuid
import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Sentinel - Agentic Infra Copilot", page_icon="🛡️", layout="wide")

st.title("🛡️ Sentinel")
st.caption("Agentic AI for infrastructure detection, diagnosis, and remediation")

# Session state setup
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar quick demo scenarios + reset
with st.sidebar:
    st.subheader("Quick scenarios")
    if st.button("🔥 Disk I/O spike on db-server-1"):
        st.session_state.pending_input = "Why is db-server-1 showing a disk I/O spike?"
    if st.button("🧠 High memory on app-server-2"):
        st.session_state.pending_input = "app-server-2 memory usage keeps climbing, what's wrong?"
    if st.button("🌡️ Overheating on edge-server-3"):
        st.session_state.pending_input = "edge-server-3 temperature is too high, investigate"

    st.divider()
    if st.button("🔄 Reset conversation"):
        requests.post(f"{API_URL}/reset", params={"session_id": st.session_state.session_id})
        st.session_state.messages = []
        st.rerun()

# Render conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("steps"):
            with st.expander("🔍 Agent reasoning trace"):
                for i, step in enumerate(msg["steps"], 1):
                    st.markdown(f"**Step {i}: `{step['tool']}`**")
                    st.code(f"Input: {step['input']}\nOutput: {step['output']}", language="text")

# Chat input, regular typing or a sidebar quick-scenario button
user_input = st.chat_input("Ask Sentinel about a server issue...")
if "pending_input" in st.session_state:
    user_input = st.session_state.pop("pending_input")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Sentinel is investigating..."):
            try:
                resp = requests.post(
                    f"{API_URL}/chat",
                    json={"session_id": st.session_state.session_id, "message": user_input},
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
                answer = data["response"]
                steps = data["steps"]
            except Exception as e:
                answer = f"Error contacting Sentinel backend: {e}"
                steps = []

        st.write(answer)
        if steps:
            with st.expander("🔍 Agent reasoning trace"):
                for i, step in enumerate(steps, 1):
                    st.markdown(f"**Step {i}: `{step['tool']}`**")
                    st.code(f"Input: {step['input']}\nOutput: {step['output']}", language="text")

    st.session_state.messages.append({"role": "assistant", "content": answer, "steps": steps})