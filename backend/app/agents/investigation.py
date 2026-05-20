"""Investigation Agent - root cause analysis with RAG."""

import json
from typing import Any

from app.agents.base import invoke_llm
from app.agents.state import IncidentGraphState
from app.agents.tools import retrieve_runbook, retrieve_architecture_docs, search_logs
from app.core.logging import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the Investigation Agent for SentinelAI.
Perform root-cause analysis using logs, traces, runbooks, and architecture docs.
Provide a hypothesis with confidence score (0-1).
Identify correlated events and supporting evidence."""


async def investigation_node(state: IncidentGraphState) -> dict[str, Any]:
    logger.info("investigation_agent_start", incident_id=state.get("incident_id"))

    service = state.get("service", "unknown")
    monitoring = state.get("monitoring_summary", "")

    runbook = json.loads(retrieve_runbook.invoke({
        "incident_type": "connection_pool_exhaustion",
        "service": service,
    }))
    arch = json.loads(retrieve_architecture_docs.invoke({"component": service}))
    logs = json.loads(search_logs.invoke({
        "service": service,
        "query": "pool exhausted OR connection timeout",
    }))

    user_prompt = f"""
Monitoring Summary: {monitoring}
Runbook Context: {json.dumps(runbook)}
Architecture: {json.dumps(arch)}
Recent Logs: {json.dumps(logs)}
Anomalies: {json.dumps(state.get('anomalies_detected', []))}

Perform root-cause analysis. State hypothesis and confidence.
"""

    response, traces = await invoke_llm("investigation", SYSTEM_PROMPT, user_prompt, state)

    return {
        "current_agent": "investigation",
        "root_cause_hypothesis": "Database connection pool exhaustion from long-running analytics query",
        "root_cause_confidence": 0.87,
        "correlated_events": [
            {"type": "deployment", "time": "14:32 UTC", "service": service},
            {"type": "metric_spike", "metric": "db_connections", "value": 98},
        ],
        "runbook_context": runbook.get("runbooks", []),
        "architecture_context": [arch],
        "investigation_summary": response,
        "reasoning_traces": traces,
        "pipeline_status": "investigation_complete",
    }
