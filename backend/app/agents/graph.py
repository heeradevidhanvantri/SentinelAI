"""LangGraph multi-agent orchestration pipeline."""

from typing import Any, Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import IncidentGraphState
from app.agents.monitoring import monitoring_node
from app.agents.investigation import investigation_node
from app.agents.decision import decision_node
from app.agents.execution import execution_node
from app.agents.reporting import reporting_node
from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def should_retry_execution(state: IncidentGraphState) -> Literal["execution", "reporting"]:
    """Route to retry or proceed based on execution outcome."""
    if not state.get("execution_success") and state.get("retry_count", 0) < state.get("max_retries", 3):
        return "execution"
    return "reporting"


def create_incident_graph() -> StateGraph:
    """Build the LangGraph state machine for incident response."""
    workflow = StateGraph(IncidentGraphState)

    workflow.add_node("monitoring", monitoring_node)
    workflow.add_node("investigation", investigation_node)
    workflow.add_node("decision", decision_node)
    workflow.add_node("execution", execution_node)
    workflow.add_node("reporting", reporting_node)

    workflow.set_entry_point("monitoring")
    workflow.add_edge("monitoring", "investigation")
    workflow.add_edge("investigation", "decision")
    workflow.add_edge("decision", "execution")
    workflow.add_conditional_edges(
        "execution",
        should_retry_execution,
        {"execution": "execution", "reporting": "reporting"},
    )
    workflow.add_edge("reporting", END)

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


async def run_incident_pipeline(
    incident_id: str,
    tenant_id: str,
    alert_title: str,
    alert_description: str,
    service: str,
    severity: str = "high",
    metrics: list | None = None,
    logs: list | None = None,
) -> dict[str, Any]:
    """Execute the full agent pipeline for an incident."""
    settings = get_settings()
    graph = create_incident_graph()

    initial_state: IncidentGraphState = {
        "incident_id": incident_id,
        "tenant_id": tenant_id,
        "alert_title": alert_title,
        "alert_description": alert_description,
        "service": service,
        "severity": severity,
        "metrics": metrics or [],
        "logs": logs or [],
        "traces": [],
        "retry_count": 0,
        "max_retries": settings.agent_max_retries,
        "errors": [],
        "reasoning_traces": [],
        "remediation_plans": [],
        "execution_memory": {},
        "should_continue": True,
        "pipeline_status": "started",
    }

    config = {"configurable": {"thread_id": incident_id}}

    logger.info("pipeline_start", incident_id=incident_id)
    final_state = None

    async for event in graph.astream(initial_state, config=config):
        for node_name, node_output in event.items():
            logger.info("pipeline_node_complete", node=node_name)
            final_state = {**initial_state, **node_output} if final_state is None else {**final_state, **node_output}

    if final_state is None:
        final_state = initial_state

    logger.info(
        "pipeline_complete",
        incident_id=incident_id,
        status=final_state.get("pipeline_status"),
    )
    return final_state
