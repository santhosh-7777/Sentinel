import json
import requests
from langchain.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from data.generate_logs import get_metrics, reset_drift

# Embedding model used to build the FAISS incident store
EMBEDDINGS = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def _load_incident_store():
    with open("data/incidents.json", "r") as f:
        incidents = json.load(f)
    texts = [i["description"] for i in incidents]
    metadatas = incidents
    return FAISS.from_texts(texts, EMBEDDINGS, metadatas=metadatas)


try:
    INCIDENT_STORE = _load_incident_store()
except FileNotFoundError:
    INCIDENT_STORE = None  # populate data/incidents.json before running the agent


@tool
def check_metrics(server_id: str) -> str:
    """Get current CPU, memory, disk I/O, and temperature stats for a given server_id.
    Use this first when investigating a performance issue."""
    # Pulls realistic drifting metrics instead of pure random values
    m = get_metrics(server_id)
    return (
        f"Server {m['server_id']} metrics @ {m['timestamp']} -> "
        f"CPU: {m['cpu_percent']}%, Memory: {m['memory_percent']}%, "
        f"Disk I/O: {m['disk_io_mbps']} MB/s, Temp: {m['temp_celsius']}C"
    )



@tool
def check_cve(software: str, version: str) -> str:
    """Check the NVD database for known CVEs affecting a given software and version.
    Use this when investigating potential security vulnerabilities."""
    try:
        url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        params = {"keywordSearch": f"{software} {version}", "resultsPerPage": 3}
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        vulns = data.get("vulnerabilities", [])
        if not vulns:
            return f"No known CVEs found for {software} {version}."

        results = []
        for v in vulns[:3]:
            cve_id = v["cve"]["id"]
            desc = v["cve"]["descriptions"][0]["value"]
            results.append(f"{cve_id}: {desc[:150]}...")
        return "\n".join(results)
    except Exception as e:
        return f"Could not fetch CVE data: {e}"


@tool
def search_similar_incidents(query: str) -> str:
    """Search past incident logs for similar issues to the current problem.
    Use this to ground your diagnosis in real historical patterns."""
    if INCIDENT_STORE is None:
        return "No incident history available yet."

    results = INCIDENT_STORE.similarity_search(query, k=2)
    if not results:
        return "No similar past incidents found."

    formatted = []
    for r in results:
        formatted.append(
            f"- {r.metadata.get('description')} | Root cause: {r.metadata.get('root_cause')} "
            f"| Fix applied: {r.metadata.get('fix')}"
        )
    return "\n".join(formatted)


@tool
def propose_remediation(issue_summary: str) -> str:
    """Given a summary of the detected issue and any retrieved context, propose a
    specific remediation action. This does NOT execute anything - it only proposes."""
    # Basic keyword-matched playbook; the LLM reasons on top of this
    suggestions = {
        "disk": "Clear disk cache and rotate old logs on the affected server.",
        "cpu": "Restart the top resource-consuming process and check for a runaway loop.",
        "memory": "Restart the affected service to clear a potential memory leak.",
        "temp": "Check fan/cooling status and consider throttling non-critical workloads.",
        "cve": "Schedule a patch window and apply the vendor-provided update.",
    }
    for keyword, suggestion in suggestions.items():
        if keyword in issue_summary.lower():
            return f"Proposed remediation: {suggestion}"
    return "Proposed remediation: Investigate further; no standard playbook matched."


@tool
def execute_fix(command: str, approved: bool, server_id: str = "") -> str:
    """Execute a remediation command. This is SIMULATED - it does not actually run
    anything on real infrastructure. Only proceeds if approved=True (human-in-the-loop gate)."""
    if not approved:
        return f"Execution blocked: awaiting human approval for '{command}'."
    # Resets the simulated drift so the fix visibly "worked" on the next metrics check
    if server_id:
        reset_drift(server_id)
    return f"[SIMULATED EXECUTION] Ran: '{command}'. Status: success."


ALL_TOOLS = [
    check_metrics,
    check_cve,
    search_similar_incidents,
    propose_remediation,
    execute_fix,
]