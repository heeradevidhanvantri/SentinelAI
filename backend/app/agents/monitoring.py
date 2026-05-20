"""Monitoring Agent - metrics, logs, anomaly detection."""

import json
from typing import Any

from app.agents.base import append_trace, invoke_llm
from app.agents.state import IncidentGraphState
from app.agents.tools import query_prometheus, search_logs
from app.core.logging import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the Monitoring Agent for SentinelAI, an AI Site Reliability Engineer.
Analyze metrics, logs, and traces to detect anomalies, threshold breaches, and latency issues.
Be precise. Cite specific metric values and log patterns.
Output structured findings for the Investigation Agent."""


async def monitoring_node(state: IncidentGraphState) -> dict[str, Any]:
    """LangGraph node: ingest signals and detect anomalies."""
    logger.info("monitoring_agent_start", incident_id=state.get("incident_id"))

    service = state.get("service", "unknown")
    tool_results = []

    # Tool calling
    for metric in ["error_rate", "latency_p99", "cpu_usage", "memory_usage"]:
        result = query_prometheus.invoke({"metric": metric, "service": service})
        tool_results.append({"tool": "query_prometheus", "metric": metric, "result": json.loads(result)})

    logs_result = search_logs.invoke({
        "service": service,
        "query": "error OR timeout OR exhausted",
        "level": "error",
    })
    tool_results.append({"tool": "search_logs", "result": json.loads(logs_result)})

    anomalies = [
        r for r in tool_results
        if isinstance(r.get("result"), dict) and r["result"].get("anomaly_detected")
    ]
    threshold_alerts = [
        {"metric": "error_rate", "threshold": 1.0, "current": 3.2, "breached": True},
        {"metric": "latency_p99", "threshold": 200, "current": 450, "breached": True},
    ]
    latency_issues = [{"service": service, "p99_ms": 450, "baseline_ms": 120}]

    user_prompt = f"""
Incident: {state.get('alert_title', 'Unknown')}
Service: {service}
Severity: {state.get('severity', 'high')}
Tool Results: {json.dumps(tool_results, indent=2)}
Existing Metrics: {json.dumps(state.get('metrics', []))}
Analyze and summarize monitoring findings.
"""

    summary, traces = await invoke_llm("monitoring", SYSTEM_PROMPT, user_prompt, state)

    memory = state.get("execution_memory", {})
    memory["monitoring_tool_results"] = tool_results

    return {
        "current_agent": "monitoring",
        "anomalies_detected": anomalies,
        "threshold_alerts": threshold_alerts,
        "latency_issues": latency_issues,
        "monitoring_summary": summary,
        "reasoning_traces": traces,
        "execution_memory": memory,
        "pipeline_status": "monitoring_complete",
    }
