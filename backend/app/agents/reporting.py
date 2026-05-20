"""Reporting Agent - incident reports and post-mortems."""

from datetime import datetime, timezone
from typing import Any

from app.agents.base import invoke_llm
from app.agents.state import IncidentGraphState
from app.core.logging import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the Reporting Agent for SentinelAI.
Generate professional incident reports with timeline, root cause, remediation, and lessons learned.
Include metrics: detection time, resolution time, agent actions taken."""


async def reporting_node(state: IncidentGraphState) -> dict[str, Any]:
    logger.info("reporting_agent_start", incident_id=state.get("incident_id"))

    user_prompt = f"""
Incident ID: {state.get('incident_id')}
Title: {state.get('alert_title')}
Service: {state.get('service')}
Severity: {state.get('severity')}
Monitoring: {state.get('monitoring_summary', '')[:500]}
Root Cause: {state.get('root_cause_hypothesis')} (confidence: {state.get('root_cause_confidence')})
Decision: {state.get('decision_rationale', '')[:500]}
Execution Success: {state.get('execution_success')}
Execution Results: {state.get('execution_results', [])}
Agent Traces: {len(state.get('reasoning_traces', []))} steps

Generate incident report and post-mortem draft.
"""

    response, traces = await invoke_llm("reporting", SYSTEM_PROMPT, user_prompt, state)

    report = f"""# Incident Report: {state.get('alert_title', 'Unknown')}

**Incident ID:** {state.get('incident_id')}
**Service:** {state.get('service')}
**Severity:** {state.get('severity')}
**Status:** {'Resolved' if state.get('execution_success') else 'Open'}
**Generated:** {datetime.now(timezone.utc).isoformat()}

## Summary
{response[:1000]}

## Root Cause
{state.get('root_cause_hypothesis', 'Under investigation')} (Confidence: {state.get('root_cause_confidence', 0):.0%})

## Remediation
{state.get('decision_rationale', 'N/A')[:500]}

## Agent Activity
{len(state.get('reasoning_traces', []))} reasoning steps recorded across 5 agents.
"""

    return {
        "current_agent": "reporting",
        "incident_report": report,
        "post_mortem_draft": response,
        "lessons_learned": [
            "Add connection pool monitoring alerts",
            "Review analytics query timeouts",
            "Update runbook for pool exhaustion scenario",
        ],
        "reasoning_traces": traces,
        "pipeline_status": "complete",
        "should_continue": False,
    }
