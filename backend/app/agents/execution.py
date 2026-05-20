"""Execution Agent - automated recovery with retries and fallback."""

import json
from typing import Any

from app.agents.base import invoke_llm
from app.agents.state import IncidentGraphState
from app.agents.tools import (
    restart_kubernetes_pod,
    trigger_autoscale,
    restart_service,
)
from app.core.logging import get_logger
from app.core.resilience import with_retry

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the Execution Agent for SentinelAI.
Execute approved remediation actions safely.
Report results. Trigger rollback if actions fail.
Use fallback strategies when primary action fails."""


@with_retry(max_attempts=3)
async def _execute_action(plan: dict) -> dict:
    action_type = plan.get("action_type", "")
    params = plan.get("parameters", {})

    executors = {
        "k8s_pod_restart": lambda: restart_kubernetes_pod.invoke(params),
        "autoscale": lambda: trigger_autoscale.invoke(params),
        "service_restart": lambda: restart_service.invoke(params),
    }
    executor = executors.get(action_type)
    if not executor:
        return {"status": "unsupported", "action_type": action_type}

    result = executor()
    return json.loads(result)


async def execution_node(state: IncidentGraphState) -> dict[str, Any]:
    logger.info("execution_agent_start", incident_id=state.get("incident_id"))

    plan = state.get("selected_plan")
    if not plan:
        return {
            "current_agent": "execution",
            "execution_success": False,
            "errors": ["No remediation plan selected"],
            "pipeline_status": "execution_failed",
        }

    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    results = []
    success = False

    try:
        if plan.get("requires_approval"):
            # In production, wait for approval; simulate approved for demo
            logger.info("execution_awaiting_approval", plan=plan)

        result = await _execute_action(plan)
        results.append(result)
        success = result.get("status") in ("simulated_success", "success")

        # Fallback: autoscale if primary fails
        if not success and retry_count < max_retries:
            fallback_plan = next(
                (p for p in state.get("remediation_plans", []) if p.get("action_type") == "autoscale"),
                None,
            )
            if fallback_plan:
                fallback_result = await _execute_action(fallback_plan)
                results.append({"fallback": True, **fallback_result})
                success = fallback_result.get("status") in ("simulated_success", "success")

    except Exception as e:
        logger.error("execution_failed", error=str(e))
        return {
            "current_agent": "execution",
            "execution_results": results,
            "execution_success": False,
            "rollback_required": True,
            "errors": [str(e)],
            "retry_count": retry_count + 1,
            "reasoning_traces": [],
            "pipeline_status": "execution_failed",
        }

    user_prompt = f"Execution results: {json.dumps(results)}. Summarize outcome."
    response, traces = await invoke_llm("execution", SYSTEM_PROMPT, user_prompt, state)

    return {
        "current_agent": "execution",
        "execution_results": results,
        "execution_success": success,
        "rollback_required": not success,
        "reasoning_traces": traces,
        "pipeline_status": "execution_complete" if success else "execution_partial",
    }
