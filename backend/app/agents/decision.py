"""Decision Agent - remediation strategy selection."""

import json
from typing import Any

from app.agents.base import invoke_llm
from app.agents.state import IncidentGraphState, RemediationPlan
from app.core.logging import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the Decision Agent for SentinelAI.
Select optimal remediation strategies based on root cause, risk, and blast radius.
Rank actions by priority. Flag actions requiring human approval.
Assess risk: low, medium, high."""


async def decision_node(state: IncidentGraphState) -> dict[str, Any]:
    logger.info("decision_agent_start", incident_id=state.get("incident_id"))

    service = state.get("service", "unknown")
    root_cause = state.get("root_cause_hypothesis", "")
    confidence = state.get("root_cause_confidence", 0)

    plans: list[RemediationPlan] = [
        {
            "action_type": "k8s_pod_restart",
            "parameters": {"namespace": "production", "pod_name": f"{service}-0"},
            "priority": 1,
            "requires_approval": True,
            "rationale": "Restart pods to clear stale connections",
        },
        {
            "action_type": "autoscale",
            "parameters": {"service": service, "min_capacity": 3, "max_capacity": 10},
            "priority": 2,
            "requires_approval": False,
            "rationale": "Scale to handle connection load",
        },
        {
            "action_type": "service_restart",
            "parameters": {"service": service, "environment": "production"},
            "priority": 3,
            "requires_approval": True,
            "rationale": "Fallback if pod restart insufficient",
        },
    ]

    user_prompt = f"""
Root Cause: {root_cause} (confidence: {confidence})
Investigation: {state.get('investigation_summary', '')}
Severity: {state.get('severity')}
Proposed Plans: {json.dumps(plans)}
Select the best remediation plan and explain decision rationale.
"""

    response, traces = await invoke_llm("decision", SYSTEM_PROMPT, user_prompt, state)

    selected = plans[0] if confidence > 0.7 else plans[1]

    return {
        "current_agent": "decision",
        "remediation_plans": plans,
        "selected_plan": selected,
        "decision_rationale": response,
        "risk_assessment": "low" if confidence > 0.8 else "medium",
        "reasoning_traces": traces,
        "pipeline_status": "decision_complete",
    }
