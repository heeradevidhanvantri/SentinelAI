"""Autonomous pipeline smoke tests — LangGraph agent orchestration."""

from __future__ import annotations

import pytest

from app.agents.graph import create_incident_graph, run_incident_pipeline, should_retry_execution
from app.agents.state import IncidentGraphState


@pytest.mark.asyncio
async def test_incident_pipeline_completes(sample_incident_input):
    result = await run_incident_pipeline(
        incident_id=sample_incident_input["incident_id"],
        tenant_id=sample_incident_input["tenant_id"],
        alert_title=sample_incident_input["alert_title"],
        alert_description=sample_incident_input["alert_description"],
        service=sample_incident_input["service"],
        severity=sample_incident_input["severity"],
    )
    assert result.get("pipeline_status") == "complete"
    assert result.get("root_cause_hypothesis")
    assert len(result.get("reasoning_traces", [])) > 0


@pytest.mark.asyncio
async def test_pipeline_agent_sequence(sample_incident_input):
    """Validate Monitoring → Investigation → Decision → Execution → Reporting."""
    result = await run_incident_pipeline(
        incident_id="pipeline-seq-001",
        tenant_id="default",
        alert_title="Redis connection saturation",
        alert_description="Redis maxclients reached",
        service="redis-cache",
        severity="critical",
    )
    agents_seen = {t.get("agent_name") for t in result.get("reasoning_traces", []) if t.get("agent_name")}
    expected = {"monitoring", "investigation", "decision", "execution", "reporting"}
    assert expected.issubset(agents_seen), f"Missing agents: {expected - agents_seen}"


@pytest.mark.asyncio
async def test_pipeline_state_propagation(sample_incident_input):
    result = await run_incident_pipeline(
        incident_id="state-prop-001",
        tenant_id="default",
        alert_title="API timeout storm",
        alert_description="504 errors cascading",
        service="gateway-api",
        severity="high",
    )
    assert result.get("incident_id") == "state-prop-001"
    assert result.get("tenant_id") == "default"
    assert result.get("service") == "gateway-api"
    assert result.get("root_cause_hypothesis") is not None


def test_retry_routing_on_failure():
    state: IncidentGraphState = {
        "execution_success": False,
        "retry_count": 1,
        "max_retries": 3,
    }
    assert should_retry_execution(state) == "execution"

    state["retry_count"] = 3
    assert should_retry_execution(state) == "reporting"

    state["execution_success"] = True
    assert should_retry_execution(state) == "reporting"


def test_retry_routing_exhausted():
    state: IncidentGraphState = {
        "execution_success": False,
        "retry_count": 5,
        "max_retries": 3,
    }
    assert should_retry_execution(state) == "reporting"


def test_graph_structure():
    graph = create_incident_graph()
    assert graph is not None
    # Compiled graph should have nodes
    assert hasattr(graph, "invoke") or hasattr(graph, "ainvoke")


@pytest.mark.asyncio
async def test_pipeline_reasoning_traces_have_required_fields():
    result = await run_incident_pipeline(
        incident_id="traces-001",
        tenant_id="default",
        alert_title="CPU exhaustion",
        alert_description="CPU > 95% for 10 minutes",
        service="sentinelai-api",
        severity="high",
    )
    traces = result.get("reasoning_traces", [])
    assert len(traces) >= 3
    for trace in traces:
        assert "agent_name" in trace or "step" in trace


@pytest.mark.asyncio
@pytest.mark.slow
async def test_pipeline_remediation_plans_generated():
    result = await run_incident_pipeline(
        incident_id="remediation-001",
        tenant_id="default",
        alert_title="Postgres connection leak",
        alert_description="Connection pool exhausted",
        service="postgres-primary",
        severity="critical",
    )
    plans = result.get("remediation_plans", [])
    assert isinstance(plans, list)
